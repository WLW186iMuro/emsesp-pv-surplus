# Änderungsprotokoll

## Unveröffentlicht

- Repository komplett auf Deutsch, englische Dokumentation am Ende der README deutlich markiert.
- Ausführliche Anleitung auf Deutsch (`docs/anleitung.md`) und Englisch (`docs/guide.md`).
- Echte Screenshots aus einer laufenden Installation (Buderus WLW186i).
- Repo umbenannt in `emsesp-wp-pv-ueberschuss`, Links in Manifest und Karte angepasst.
- PayPal-Button (PayPal.me) zum Unterstützen des Projekts.
- Raumnamen aus den Screenshots entfernt.

## 0.2.1 – 2026-10-21

- Neuer Anzeigename: **EMS-ESP WP PV Überschuss** (Integrationsliste, HACS, Kartenauswahl, Gerätehersteller). Die Domain `emsesp_pv_surplus` und der Kartentyp `custom:emsesp-pv-surplus-card` bleiben gleich, bestehende Einrichtungen und Dashboards laufen ohne Änderung weiter.

## 0.2.0 – 2026-10-21

Erste öffentliche Version.

- Kurze Aussetzer von Messwerten (EMS-ESP-/MQTT-Reconnect, Abfragelücken des Wechselrichters) setzen den Status nicht mehr auf „Messwerte fehlen“. Der Status wechselt erst nach 2 Minuten; der Sicherheits-Stopp nach 10 Minuten bleibt.
- Diagnose-Download für Fehlerberichte.
- Der vorgeschlagene Gerätename folgt der Home-Assistant-Sprache (DE/EN).
- Name und Beschreibung in der Kartenauswahl auf Deutsch oder Englisch.
- Manifest: Links zu Dokumentation und Issue-Tracker.
- Repository für HACS eingerichtet (benutzerdefiniertes Repository), mit hassfest-/HACS-Prüfung, Tests und automatisch gebautem Release-ZIP.

## 0.1.1

- Die Karte wird nur noch als Lovelace-Ressource geladen, registriert nach dem Start von Home Assistant. Das behebt „Custom element doesn't exist“ zusammen mit HACS-Karten, die eine eigene Custom-Element-Registry installieren.
- Die Karte registriert sich erneut, falls ein anderes Skript `window.customElements` ersetzt.

## 0.1.0

- Erste Version: PV-/SG-Ready-Signal über eine EMS-ESP-Eingangsoption, Akku-Vorrang, Solcast-Prognose, Leistungsnachführung, Beobachtungsmodus, Dashboard-Karte.
