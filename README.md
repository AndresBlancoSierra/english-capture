<p align="center">
  <a href="https://github.com/AndresBlancoSierra/english-capture">
    <img src="https://raw.githubusercontent.com/AndresBlancoSierra/english-capture/main/profile.svg" alt="English Capture — english-capture@arch">
  </a>
</p>

# English Capture

Sistema de **captura de texto global para aprender inglés**: seleccionas una
zona de la pantalla, se captura y se ejecuta OCR (Tesseract), y el texto queda
almacenado y consultable en SQLite, con notificaciones y daemon de fondo.

Python 3.12 + Pillow + pytesseract + evdev + pygobject/pycairo (Linux/Wayland).

---

## 🚀 Cómo correrlo

```bash
cd ~/Proyects/english-capture
uv run english-capture
```

Para dejarlo corriendo en segundo plano como daemon de usuario:

```bash
systemctl --user enable --now english-capture-daemon
```

---

## 🧠 Qué hace

1. **Capturar**: seleccionas un área de la pantalla (`slurp`) y se toma la
   imagen (`grim`), con una región de contexto ampliada.
2. **OCR**: extrae el texto con Tesseract (idioma configurable, por defecto
   `eng`).
3. **Guardar**: cada captura se indexa en SQLite con su texto, timestamp y
   estado.
4. **Notificar**: muestra una notificación del sistema con el texto extraído.
5. **Procesar**: pipeline opcional automático sobre lo capturado.

### Stack

Pillow, pytesseract, evdev, pygobject, pycairo, SQLAlchemy (SQLite).

---

## 📁 Estructura

```
english-capture/
├── src/english_capture/
│   ├── cli.py          ← entrypoint (`english-capture`)
│   ├── screenshot.py   ← captura de pantalla
│   ├── selection/      ← selección de área
│   ├── ocr/            ← Tesseract OCR
│   ├── processing.py   ← pipeline de procesamiento
│   ├── database.py     ← SQLite
│   ├── notifications.py← notificaciones de escritorio
│   └── config.py       ← rutas XDG + config.json
└── pyproject.toml      ← entrypoint `english-capture`
```

---

## ⚙️ Configuración

Config en `~/.config/english-capture/config.json`:

| Clave | Default | Qué es |
| --- | --- | --- |
| `ocr_engine` | `tesseract` | Motor OCR |
| `tesseract_lang` | `eng` | Idioma de OCR |
| `screenshot_tool` | `grim` | Captura de pantalla |
| `selection_tool` | `slurp` | Selección de área |
| `context_region_scale` | `2.0` | Zoom de la región de contexto |
| `notifications_enabled` | `true` | Notificaciones al capturar |
| `auto_process_on_capture` | `true` | Procesar automáticamente |

Datos en `~/.local/share/english-capture/` (inbox, processed, failed,
`captures.db`). Capturas en `~/Pictures/english-capture/`.
