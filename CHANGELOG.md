# Changelog

## 0.2.0 – 2026-10-21

First public release.

- Short sensor dropouts (EMS-ESP/MQTT reconnects, inverter polling gaps) no longer flip the status to "Readings missing". The status only changes after 2 minutes; the safety stop after 10 minutes is unchanged.
- Diagnostics download for bug reports.
- Default device name follows the Home Assistant language (EN/DE).
- Card picker name and description in English or German.
- Manifest: documentation and issue tracker links, integration name "EMS-ESP PV Surplus".
- Repository set up for HACS (custom repository), with hassfest/HACS validation, tests and a release ZIP built by GitHub Actions.

## 0.1.1

- The card is loaded only as a Lovelace resource, registered after Home Assistant has started. This fixes "Custom element doesn't exist" together with HACS cards that install a scoped custom element registry.
- The card defines itself again if another script replaces `window.customElements`.

## 0.1.0

- First version: PV/SG Ready signal via an EMS-ESP input option, battery priority, Solcast forecast, compressor power control, observe mode, dashboard card.
