# SHEA Projects

Collection of projects for SHEA (Sydney Higher Education Academy) systems and tools.

---

## 📦 Projects

### 1. SHEAC-HATBOT-main
**AI Chatbot with RAG**

A modern chatbot application powered by OpenAI and Google Gemini, with a RAG system for FAQ knowledge base.

- **Tech:** Next.js 16, TypeScript, Tailwind CSS, MongoDB
- **AI:** OpenAI GPT-4o-mini, Google Gemini 2.0 Flash
- **Status:** ✅ Active

📖 [View README](./SHEAC-HATBOT-main/README.md)

---

### 2. cpl_automation-main
**Credit for Prior Learning Assistant**

Maps external university units to SHEA units with confidence scoring, review workflow, and exportable reports.

- **Tech:** Python, Streamlit, SQLite, Playwright
- **Features:** Unit matching, confidence scoring, MCP backend integration
- **Status:** ✅ Active

📖 [View README](./cpl_automation-main/README.md)

---

### 3. streamlit-dashboard-main
**Student Risk Analytics Dashboard**

Identifies at-risk students by analyzing Moodle engagement, assessments, and performance data for early intervention.

- **Tech:** Python, Streamlit, Pandas, Moodle API
- **Features:** Risk scoring, email outreach, interactive dashboards
- **Status:** ✅ Active

📖 [View README](./streamlit-dashboard-main/readme.md)

---

## 🚀 Quick Start

### Prerequisites

- **Node.js 20+** (for SHEAC-HATBOT)
- **Python 3.11+** (for CPL Automation & Dashboard)
- **MongoDB** (for SHEAC-HATBOT)

### Setup All Projects

```bash
# SHEAC-HATBOT
cd SHEAC-HATBOT-main
npm install
cp .env.example .env.local
# Edit .env.local with your API keys
npm run dev

# CPL Automation
cd cpl_automation-main
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
streamlit run app.py

# Student Dashboard
cd streamlit-dashboard-main
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
streamlit run apilog2.py
```

---

## 📁 Repository Structure

```
shea-projects/
├── SHEAC-HATBOT-main/        # AI Chatbot
├── cpl_automation-main/      # CPL Assistant
├── streamlit-dashboard-main/ # Risk Analytics
└── README.md                 # This file
```

---

## 🔐 Security Notes

- Never commit `.env` files with real credentials
- Use `.env.example` as templates only
- Rotate API keys regularly
- Follow institutional data privacy policies

---

## 👨‍💻 Author

**Alex Lu**

---

## 📄 License

All projects are private and proprietary to SHEA.
