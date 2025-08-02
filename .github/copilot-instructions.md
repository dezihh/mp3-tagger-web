# Copilot Instructions for MP3 Tagger Web Application

## Big Picture Architecture
- Modular Flask web application for MP3 metadata management and enrichment
- Main entry: `app.py` (Flask server, routes, workflow orchestration)
- Core logic in `tagger/` (ID3, cover, enrichment, audio recognition)
- UI templates in `templates/` (Jinja2)
- Static assets in `static/` (CSS, JS, images)
- Configuration via `config.env` (API keys, runtime settings)

## Workflow & Data Flow
- User selects MP3 directory (manual input or explorer)
- App scans directory, parses filenames, reads ID3 tags, detects covers
- Results shown in table (one row per file, editable fields)
- Audio recognition (Shazam/AcoustID) for missing metadata (button per file)
- Metadata enrichment (MusicBrainz, Last.fm, Discogs) for selected files (batch button)
- Covers managed (internal/external, preview on hover, replace/delete/keep options)
- Save workflow: user marks files, edits, saves; app writes tags and covers

## Developer Workflows
- Use Python 3 with venv (see README)
- Install dependencies: `pip install -r requirements.txt`
- activate venv: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
- Run server: `python app.py` (default port 5000)
- Test modular code in `tagger/` via `examples_modular_usage.py` or `tests/`
- Manage and save tests in `tests/` (unit tests for `tagger/` logic)
- Static/JS/CSS changes require browser reload

## Project-Specific Patterns
- All enrichment, recognition, and parsing logic is in `tagger/` modules (see `core.py`, `audio_recognition.py`, etc.)
- UI: Table-based, inline editing, batch selection via checkboxes
- Cover status: `I<px>`, `E<px>`, `B<px>`, `Nein` (see README for meaning)
- Track number formatting: configurable digits, leading zeros, bulk update
- API keys and config: only in `config.env`, never hardcoded
- Results pages: `results.html`, 

## Integration Points
- External APIs: DiscoGS, hazamIO, AcoustID, MusicBrainz, Last.fm, Discogs (see README for config)
- All API calls and enrichment logic in `tagger/` modules
- JS in `static/script.js` for UI interactivity

## Conventions & Examples
- New features: add to `tagger/` as separate module, import in `core.py`
- UI changes: update Jinja2 templates and corresponding JS/CSS
- For new workflows, follow README's staged process and table UI
- Use batch operations for multi-file actions (checkboxes, bulk save)
- Always document new modules and workflows in README

## Key Files & Directories
- `app.py` (Flask entry)
- `tagger/` (core logic, enrichment, recognition)
- `templates/` (UI)
- `static/` (assets)
- `config.env` (API/config)
- `README.md` (spec, workflow, architecture)

---
For unclear conventions or missing patterns, check README.md and existing modules in `tagger/`. Ask for feedback if you encounter ambiguous workflows or architectural decisions.

## General
Communicate with user in german language, use simple and clear sentences. If you are unsure about a specific implementation detail, ask for clarification or provide a general solution that can be refined later.
Please ensure to make code reusable and place similar code blocks together. Avoid duplicating logic across modules; instead, create utility functions in `tagger/utils.py` or similar helper files. This will help maintain a clean and modular codebase that is easy to extend and maintain.
