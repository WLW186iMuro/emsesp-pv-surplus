# Bildvorlagen

Vorlagen für das Ankündigungsbild jeder neuen Version und für die Link-Vorschau des Repositorys (Social Preview).

| Datei | Zweck | Größe |
|---|---|---|
| `facebook-quer.html` | Ankündigungsbild einer Version (Facebook, Querformat) | 1200 × 630, gerendert ×2 |
| `social-preview.html` | Link-Vorschau des Repositorys (`docs/social-preview.png`) | 1280 × 640 |
| `render.mjs` | rendert eine Vorlage zu PNG | |

## Bei jeder neuen Version

1. Beide Vorlagen an die Neuerungen der Version anpassen (Überschrift, Text, Punkte, Grafik rechts). Die Social Preview bleibt allgemein: keine Versionsnummer, damit sie nicht veraltet.
2. Rendern:
   ```sh
   node tools/bilder/render.mjs tools/bilder/facebook-quer.html ems-esp-wp-pv-ueberschuss-vX.Y.Z.png 1200 630 2
   node tools/bilder/render.mjs tools/bilder/social-preview.html docs/social-preview.png 1280 640 1
   ```
3. Bild prüfen: nichts abgeschnitten, nichts überlappt, keine persönlichen Daten (Raumnamen, echte Messwerte).
4. `docs/social-preview.png` committen und unter *Settings → General → Social preview* hochladen. GitHub bietet dafür keine API, das Hochladen geht nur über die Weboberfläche.
