# HOMEBOUND — Contributing

## Setup

```bash
git clone https://github.com/imamsanghaarc/nasa.git
cd nasa
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Never install plain `pygame`; use `pygame-ce`.

## Code style

- Run `black` before commits (cosmetic; avoids diff noise).
- Delta time everywhere — no `time.sleep`, no frame-counted timers.
- No blocking calls in the loop; async-friendly `main()` keeps pygbag possible.

## Adding a level

1. Add JSON under `data/levels/<id>.json`.
2. Add planet entry under `data/planets.json` with `playable`, `part`, `map_position`, `fact`, `facts`, `unlock`.
3. Register the scene in `main.py`.
4. Wire dialogue under `data/dialogue/<id>.json`.
5. Update HUD objective and unlock rules through `GameState`.

Bad JSON should raise a readable `DataError`, not crash mid-frame.

## Testing before merge

```bash
python tools/smoke_test.py   # headless smoke test: boot every scene
python tools/playtest.py     # scripted full-loop playtest
```

## Documentation sync

When gameplay or architecture changes, update the relevant doc in the suite:

- Gameplay / levels / story → `DESIGN.md`, `PLAYGUIDE.md`, `README.md`.
- Code / architecture / modules → `TECHNICAL.md`.
- Tests / QA → `TOOLS.md`.
- Content / JSON → `DATA.md`.
- All user-facing → `README.md`.

See [DOCS.md](DOCS.md) for the full index.
