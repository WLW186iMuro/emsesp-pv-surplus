"""Unit tests for the decision logic (run: python -m unittest discover tests)."""

from __future__ import annotations

import importlib.util
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
import sys
import unittest

_LOGIC = Path(__file__).resolve().parents[1] / "custom_components" / "emsesp_pv_surplus" / "logic.py"
_spec = importlib.util.spec_from_file_location("logic", _LOGIC)
logic = importlib.util.module_from_spec(_spec)
sys.modules["logic"] = logic
_spec.loader.exec_module(logic)

TZ = timezone(timedelta(hours=2))
BITS_OFF = "000000100000"
BITS_ON = "100000100000"


def at(h: int, m: int = 0, s: int = 0, day: int = 18) -> datetime:
    return datetime(2026, 10, day, h, m, s, tzinfo=TZ)


class Sim:
    """Steps the controller in 15 s ticks with a scripted environment."""

    def __init__(self, **settings):
        self.settings = logic.Settings(**settings)
        self.state = logic.State()
        self.now = at(11)
        self.grid_w = 0.0
        self.battery_w = 0.0
        self.soc = 100.0
        self.sun_up = True
        self.remaining = 10.0
        self.f30 = 3000.0
        self.hp_w = 25.0
        self.bits = BITS_OFF
        self.pvmax = 1.0
        self.last: logic.Result | None = None
        self.events: list[str] = []

    def step(self, seconds: int = 15) -> logic.Result:
        self.now += timedelta(seconds=seconds)
        res = logic.evaluate(
            self.settings,
            self.state,
            logic.Inputs(
                now=self.now,
                grid_w=self.grid_w,
                battery_w=self.battery_w,
                soc=self.soc,
                sun_up=self.sun_up,
                forecast_remaining_kwh=self.remaining,
                forecast_30min_w=self.f30,
                hp_power_w=self.hp_w,
                signal_bits=self.bits,
                pvmaxcomp_kw=self.pvmax,
            ),
        )
        # emulate the heat pump following the signal and the limit
        if res.enforce_signal and res.signal_bits_target and res.signal_bits_target != self.bits:
            self.bits = res.signal_bits_target
        if res.write_comp and res.comp_target_kw is not None:
            self.pvmax = res.comp_target_kw
            self.events.append(f"comp:{res.comp_target_kw}")
        if res.started:
            self.events.append(f"start:{res.reason}")
        if res.stopped:
            self.events.append(f"stop:{res.reason}")
        self.last = res
        return res

    def run(self, minutes: float) -> logic.Result:
        res = self.last
        for _ in range(int(minutes * 4)):
            res = self.step()
        return res


class TestHelpers(unittest.TestCase):
    def test_battery_release(self):
        s = logic.Settings(soc_release=80, soc_forecast=60, battery_capacity_kwh=10, forecast_reserve_kwh=4)
        self.assertTrue(logic.battery_release(s, 80, 0))
        self.assertFalse(logic.battery_release(s, 79, 0))
        # 65 % -> 3.5 kWh missing; 8 - 4 = 4 >= 3.5
        self.assertTrue(logic.battery_release(s, 65, 8))
        self.assertFalse(logic.battery_release(s, 65, 7))
        # below forecast threshold never released by forecast
        self.assertFalse(logic.battery_release(s, 55, 30))
        s.use_forecast = False
        self.assertFalse(logic.battery_release(s, 65, 30))
        self.assertFalse(logic.battery_release(s, None, 30))

    def test_available_power(self):
        # exporting 500 W, battery charging 2000 W
        self.assertEqual(logic.available_power(-500, -2000, True), 2500)
        self.assertEqual(logic.available_power(-500, -2000, False), 500)
        # battery discharging 800 W always subtracted
        self.assertEqual(logic.available_power(0, 800, True), -800)
        self.assertEqual(logic.available_power(0, 800, False), -800)

    def test_compressor_target(self):
        s = logic.Settings(comp_min_kw=1.0, comp_max_kw=2.5, comp_reserve_kw=0.1)
        self.assertEqual(logic.compressor_target(s, 2300, True), 2.2)
        self.assertEqual(logic.compressor_target(s, 4600, True), 2.5)
        self.assertEqual(logic.compressor_target(s, 800, True), 1.0)
        self.assertEqual(logic.compressor_target(s, 4600, False), 1.0)
        self.assertEqual(logic.compressor_target(s, None, True), 1.0)

    def test_bits(self):
        self.assertEqual(logic.set_bit(BITS_OFF, 0, True), BITS_ON)
        self.assertEqual(logic.set_bit(BITS_ON, 0, False), BITS_OFF)
        self.assertTrue(logic.valid_bits(BITS_OFF, 0))
        self.assertFalse(logic.valid_bits("unavailable", 0))
        self.assertFalse(logic.valid_bits("0101", 4))
        self.assertFalse(logic.valid_bits(None, 0))

    def test_window(self):
        self.assertTrue(logic.in_window(time(10), time(10), time(16)))
        self.assertFalse(logic.in_window(time(16), time(10), time(16)))
        self.assertTrue(logic.in_window(time(23), time(22), time(6)))
        self.assertTrue(logic.in_window(time(3), time(3), time(3)))

    def test_persistence_roundtrip(self):
        st = logic.State(requested=True, requested_since=at(12), last_off=at(9), activations=1, runtime_s=600)
        st.day = at(12).date()
        back = logic.State.from_dict(st.to_dict())
        self.assertTrue(back.requested)
        self.assertEqual(back.requested_since, at(12))
        self.assertEqual(back.last_off, at(9))
        self.assertEqual(back.activations, 1)
        self.assertEqual(back.day, at(12).date())
        s = logic.Settings(on_threshold_w=1700, window_start=time(9, 30), mode="manual")
        s2 = logic.Settings.from_dict(s.to_dict())
        self.assertEqual(s2.on_threshold_w, 1700)
        self.assertEqual(s2.window_start, time(9, 30))
        self.assertEqual(s2.mode, "manual")
        self.assertEqual(logic.Settings.from_dict({"mode": "nonsense"}).mode, "auto")


class TestControl(unittest.TestCase):
    def test_start_needs_stable_surplus(self):
        sim = Sim()
        sim.grid_w = -2000  # exporting 2 kW
        res = sim.run(4.5)
        self.assertEqual(res.status, logic.ST_PENDING)
        self.assertFalse(sim.state.requested)
        res = sim.run(1)
        self.assertTrue(sim.state.requested)
        self.assertEqual(res.status, logic.ST_PV)
        self.assertEqual(sim.bits, BITS_ON)
        self.assertEqual(sim.state.activations, 1)
        self.assertIn("start:surplus", sim.events)

    def test_short_dip_resets_on_delay(self):
        sim = Sim()
        sim.grid_w = -2000
        sim.run(4)
        sim.grid_w = 0
        sim.step()
        sim.grid_w = -2000
        sim.run(4)
        self.assertFalse(sim.state.requested)

    def test_forecast_blocks_start(self):
        sim = Sim()
        sim.grid_w = -2000
        sim.f30 = 500
        res = sim.run(10)
        self.assertFalse(sim.state.requested)
        self.assertFalse(res.checks["forecast"])
        self.assertEqual(res.status, logic.ST_WAIT)
        sim.settings.use_forecast = False
        sim.run(6)
        self.assertTrue(sim.state.requested)

    def test_min_runtime_then_stop_and_lock(self):
        sim = Sim()
        sim.grid_w = -2000
        sim.run(6)
        self.assertTrue(sim.state.requested)
        # heat pump now draws more than the surplus
        sim.grid_w = 1500
        res = sim.run(20)
        self.assertTrue(sim.state.requested, "must keep running during min runtime")
        self.assertEqual(res.status, logic.ST_DEFICIT)
        sim.run(11)
        self.assertFalse(sim.state.requested)
        self.assertIn("stop:no_surplus", sim.events)
        self.assertEqual(sim.bits, BITS_OFF)
        # surplus again -> locked for 2 h
        sim.grid_w = -2500
        res = sim.run(60)
        self.assertFalse(sim.state.requested)
        self.assertEqual(res.status, logic.ST_LOCKED)
        self.assertIsNotNone(res.lock_until)
        sim.run(65)
        self.assertTrue(sim.state.requested)
        self.assertEqual(sim.state.activations, 2)

    def test_deficit_between_thresholds_keeps_running(self):
        sim = Sim()
        sim.grid_w = -2000
        sim.run(6)
        sim.grid_w = 300  # small import, above off threshold of -800 W available
        sim.run(60)
        self.assertTrue(sim.state.requested)

    def test_daily_limit(self):
        sim = Sim(lock_min=1, min_runtime_min=1, off_delay_min=1, on_delay_min=1)
        for _ in range(2):
            sim.grid_w = -2000
            sim.run(3)
            self.assertTrue(sim.state.requested)
            sim.grid_w = 2000
            sim.run(3)
            self.assertFalse(sim.state.requested)
        sim.grid_w = -2000
        res = sim.run(10)
        self.assertFalse(sim.state.requested)
        self.assertEqual(res.status, logic.ST_LIMIT)
        # next day resets the counter
        sim.now = at(10, 30, day=19)
        res = sim.run(3)
        self.assertTrue(sim.state.requested)
        self.assertEqual(sim.state.activations, 1)

    def test_battery_low_stops(self):
        sim = Sim()
        sim.grid_w = -2000
        sim.run(6)
        sim.soc = 49
        sim.run(1.5)
        self.assertTrue(sim.state.requested)
        sim.run(1)
        self.assertFalse(sim.state.requested)
        self.assertIn("stop:battery_low", sim.events)

    def test_battery_below_stop_blocks_start(self):
        sim = Sim()
        sim.soc = 45
        sim.grid_w = -2500
        res = sim.run(10)
        self.assertFalse(sim.state.requested)
        self.assertEqual(res.status, logic.ST_BATTERY)

    def test_night_and_window(self):
        sim = Sim()
        sim.now = at(16, 0)
        sim.grid_w = -2500
        res = sim.run(10)
        self.assertFalse(sim.state.requested)
        self.assertEqual(res.status, logic.ST_WINDOW)
        sim2 = Sim()
        sim2.grid_w = -2500
        sim2.run(6)
        sim2.sun_up = False
        res = sim2.step()
        self.assertFalse(sim2.state.requested)
        self.assertEqual(res.status, logic.ST_NIGHT)

    def test_sensor_failure_stops_after_10_min(self):
        sim = Sim()
        sim.grid_w = -2500
        sim.run(6)
        sim.grid_w = None
        res = sim.run(9)
        self.assertTrue(sim.state.requested)
        sim.run(1.5)
        self.assertFalse(sim.state.requested)
        self.assertIn("stop:sensor_error", sim.events)

    def test_short_sensor_dropout_keeps_status(self):
        sim = Sim()
        sim.soc = 40
        res = sim.run(2)
        self.assertEqual(res.status, logic.ST_BATTERY)
        sim.soc = None
        res = sim.step()
        self.assertEqual(res.status, logic.ST_BATTERY)
        self.assertFalse(res.checks["sensors"])
        sim.soc = 40
        self.assertEqual(sim.step().status, logic.ST_BATTERY)
        sim.soc = None
        res = sim.run(2.5)
        self.assertEqual(res.status, logic.ST_SENSOR)

    def test_battery_priority_without_release(self):
        sim = Sim()
        sim.soc = 60
        sim.remaining = 3  # forecast won't fill the battery
        sim.grid_w = 0
        sim.battery_w = -3000  # all surplus goes into the battery
        res = sim.run(10)
        self.assertFalse(res.battery_release)
        self.assertFalse(sim.state.requested)
        sim.soc = 85
        res = sim.run(6)
        self.assertTrue(res.battery_release)
        self.assertTrue(sim.state.requested)

    def test_modes(self):
        sim = Sim()
        sim.settings.mode = logic.MODE_MANUAL
        res = sim.step()
        self.assertTrue(sim.state.requested)
        self.assertEqual(res.status, logic.ST_MANUAL)
        self.assertEqual(sim.state.activations, 0)
        self.assertEqual(sim.bits, BITS_ON)
        sim.settings.mode = logic.MODE_OFF
        res = sim.step()
        self.assertFalse(sim.state.requested)
        self.assertEqual(res.status, logic.ST_OFF)
        self.assertFalse(res.enforce_signal)

    def test_compressor_follows_budget_every_5_min(self):
        sim = Sim()
        sim.grid_w = -2400
        sim.run(6)
        self.assertTrue(sim.state.requested)
        # immediate start value from pre-start average (2400 + 25 W)
        self.assertEqual(sim.events.count("comp:2.3"), 1)
        # heat pump ramps to 2.3 kW, grid goes to 0 -> budget stays ~2.3 kW
        sim.hp_w = 2300
        sim.grid_w = -100
        sim.run(10)
        self.assertEqual(sim.pvmax, 2.3)
        # sun increases, 4.6 kW budget -> capped at 2.5
        sim.grid_w = -2300
        sim.run(10)
        self.assertEqual(sim.pvmax, 2.5)
        # cloud, budget 1.2 kW -> 1.1
        sim.hp_w = 1000
        sim.grid_w = -200
        sim.run(10)
        self.assertEqual(sim.pvmax, 1.1)

    def test_compressor_min_without_release(self):
        sim = Sim()
        sim.settings.mode = logic.MODE_MANUAL
        sim.soc = 60
        sim.remaining = 0
        sim.pvmax = 2.0
        sim.battery_w = -3000
        sim.step()
        self.assertEqual(sim.pvmax, 1.0)

    def test_compressor_only_writes_on_big_change(self):
        sim = Sim()
        sim.grid_w = -2400
        sim.run(6)
        writes = len([e for e in sim.events if e.startswith("comp:")])
        sim.grid_w = -2450  # +50 W
        sim.run(15)
        self.assertEqual(len([e for e in sim.events if e.startswith("comp:")]), writes)

    def test_runtime_counts(self):
        sim = Sim()
        sim.grid_w = -2400
        sim.run(6)
        sim.run(30)
        self.assertAlmostEqual(sim.state.runtime_s / 60, 30.75, delta=1)


if __name__ == "__main__":
    unittest.main()
