# cpl_automation_mcp

MCP backend server for the CPL Automation project.

This repo is intentionally separate from the main app repo:
- Main app (UI + matching): `cpl_automation`
- MCP backend (web browsing tools): `cpl_automation_mcp`

---

## What this server does

This MCP server provides browser-driven tools used by CPL workflows to retrieve unit/course information from external university websites.

Current tools in `server.py`:
- `search_web(query, site, max_results)`
- `fetch_page(url, max_chars)`
- `find_unit_page(unit_code, unit_title, institution, institution_site, max_results)`

Tech used:
- `fastmcp`
- `playwright`
- `beautifulsoup4`

---

## Requirements

- Python 3.11+
- Internet access
- Playwright browser binaries installed

---

## Install (from scratch)

### macOS / Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python -m playwright install
```

### Windows (PowerShell)
```powershell
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m playwright install
```

---

## Run

```bash
python3 server.py
```

Keep this process running while using the main CPL app.

---

## How to use with main app

In a separate terminal, run the main app from the other repo:

```bash
cd /path/to/cpl_automation
source .venv/bin/activate
streamlit run app.py --server.port 8503
```

Recommended terminal setup:
- Terminal A: this repo (`python3 server.py`)
- Terminal B: main app (`streamlit run app.py`)

---

## Troubleshooting

## `playwright` errors or blank retrieval
```bash
python -m playwright install
```

## Missing dependencies
```bash
pip install -r requirements.txt
```

## Server not running check
```bash
ps aux | grep -Ei "python.*server.py|cplmcp" | grep -v grep
```

---

## Repository relation

- Main project repo: `https://github.com/Sunil-paudel/cpl_automation`
- MCP backend repo: `https://github.com/Sunil-paudel/cpl_automation_mcp`
