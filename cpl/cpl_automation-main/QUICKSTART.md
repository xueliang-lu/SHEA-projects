# CPL Automation - Quick Start Guide

Get up and running in 5 minutes.

---

## ⚡ 5-Minute Setup

### 1. Install Dependencies

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# OR: .venv\Scripts\Activate.ps1  # Windows

# Install packages
pip install -r requirements.txt

# Install Playwright browsers
python -m playwright install
```

### 2. Add SHEA Data

Place your SHEA course data file in:
```
data/SHEA Course Data.xlsx
```

### 3. Run the App

```bash
streamlit run app.py --server.port 8503
```

Open: http://localhost:8503

---

## 🎯 Core Workflow

### Step 1: Load SHEA Units
- Sidebar → **"Load SHEA units from local Excel"**
- Wait for confirmation

### Step 2: Upload Transcript
- Go to **"Upload Transcript"** page
- Upload student transcript PDF
- Click **"Parse and save external units"**

### Step 3: Enrich Data
- Go to **"CPL Suggestions"** page
- Select university OR paste course URL
- Click **"Run MCP check: crawl external course website"**

### Step 4: Generate Matches
- Click **"Generate suggestions"**
- Review confidence scores and explanations

### Step 5: Review & Approve
- Go to **"Review & Approval"** page
- Mark each suggestion:
  - ✅ Approved
  - ❌ Rejected
  - ⚠️ Needs Review
  - 🔧 Override

### Step 6: Export
- Use export buttons to download:
  - CSV
  - Excel
  - PDF reports

Files saved to: `exports/`

---

## 📊 Understanding Confidence Scores

| Score | Meaning | Action |
|-------|---------|--------|
| **90-100%** | Excellent match | Auto-approve candidate |
| **75-89%** | Good match | Review recommended |
| **60-74%** | Moderate match | Manual review required |
| **< 60%** | Weak match | Likely reject |

### Score Components

Confidence is calculated from:
- **Title similarity** (25%)
- **Description similarity** (25%)
- **Learning outcomes** (20%)
- **Credit hours** (15%)
- **Grade bonus** (10%)
- **Retrieval bonus** (5%)

---

## 🔧 MCP Backend (Optional)

For advanced website retrieval, run the MCP server:

```bash
# In separate terminal
cd /path/to/cpl_automation_mcp
python3 server.py
```

Keep running while using main app.

---

## ⚠️ Important Notes

### Grade Flags

The system automatically flags:
- **Fail (F)** - Not eligible for CPL
- **Not Competent (NC/NYC)** - Not eligible
- **Incomplete (I)** - Requires resolution

These should **not** be auto-approved.

### Data Quality

- Ensure SHEA Excel file is up to date
- Verify transcript PDFs are readable
- Check external URLs are accessible

---

## 🐛 Quick Troubleshooting

| Issue | Solution |
|-------|----------|
| App won't start | Check port 8503 is free |
| Empty SHEA units | Verify Excel file in `data/` |
| No retrieval results | Check MCP server is running |
| Database errors | Run: `python -c "from src.db import init_db; init_db()"` |

---

## 📚 Full Documentation

- **Complete Guide:** `docs/INSTALL_AND_USER_GUIDE.md`
- **PDF Version:** `docs/INSTALL_AND_USER_GUIDE.pdf`

---

## 🆘 Need Help?

1. Check the full documentation in `docs/`
2. Review existing issues on GitHub
3. Contact the maintainer

---

**Author:** Sunil Paudel  
**Version:** 1.0  
**Last Updated:** March 2026
