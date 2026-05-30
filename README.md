
# 📊 Geojit AI Financial Report Analyzer

An AI-powered full-stack web application that accepts a financial document (PDF/TXT/CSV),
extracts key financial metrics using OpenAI GPT-4o, generates Revenue/EBITDA/PAT charts,
and produces a professional **Geojit-style PDF equity research report**.

---

## 🏗 Project Structure

```
geojit-analyzer/
├── backend/
│   ├── main.py              # FastAPI app & routes
│   ├── parser.py            # PDF/TXT/CSV text extraction (PyMuPDF)
│   ├── extractor.py         # OpenAI API → structured JSON
│   ├── charts.py            # Matplotlib chart generation
│   ├── report_generator.py  # Jinja2 → HTML → WeasyPrint PDF
│   ├── prompts.py           # All AI prompt templates
│   └── requirements.txt
├── frontend/
│   ├── pages/
│   │   ├── _app.tsx         # Next.js app wrapper
│   │   └── index.tsx        # Main page
│   ├── components/
│   │   ├── StepIndicator.tsx
│   │   ├── ReportSummary.tsx
│   │   ├── FinancialCharts.tsx
│   │   └── MetricsTable.tsx
│   ├── styles/globals.css
│   ├── next.config.js
│   ├── tailwind.config.js
│   └── package.json
├── templates/
│   └── geojit_template.html # Jinja2 HTML template (PDF layout)
├── generated_reports/       # Output PDF + chart images (auto-created)
├── .env.example
└── README.md
```

---

## ⚙️ Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Python | 3.10+ | [python.org](https://python.org) |
| Node.js | 18+ | [nodejs.org](https://nodejs.org) |
| pip | latest | bundled with Python |
| npm | latest | bundled with Node.js |

### System dependencies for WeasyPrint (PDF generation)

**Ubuntu / Debian:**
```bash
sudo apt-get install -y libpango-1.0-0 libcairo2 libgdk-pixbuf2.0-0 libffi-dev
```

**macOS (Homebrew):**
```bash
brew install pango cairo gdk-pixbuf libffi
```

**Windows:**
Install [GTK3 runtime](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer).

---

## 🔑 OpenAI API Setup

1. Go to [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Create a new secret key
3. Copy the key (it starts with `sk-proj-...`)
4. Add it to your `.env` file (see step 2 below)

**Recommended model:** `gpt-4o` (best accuracy for financial extraction)  
**Budget option:** `gpt-3.5-turbo` (faster/cheaper, less precise)

---

## 🚀 Installation & Running

### Step 1 – Clone & open in VS Code

```bash
# If you haven't created the project yet:
mkdir geojit-analyzer && cd geojit-analyzer
code .   # opens VS Code
```

### Step 2 – Environment variables

```bash
# In the project root:
cp .env.example .env
# Then edit .env and paste your OPENAI_API_KEY
```

---

### Step 3 – Backend setup

Open a terminal in VS Code (`Ctrl+`` ` ``):

```bash
cd backend

# Create Python virtual environment
python -m venv venv

# Activate (Linux/macOS)
source venv/bin/activate

# Activate (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### Step 4 – Run the backend

```bash
# From the backend/ directory (with venv activated):
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

✅ Backend running at: [http://localhost:8000](http://localhost:8000)  
📖 API docs at: [http://localhost:8000/docs](http://localhost:8000/docs)

---

### Step 5 – Frontend setup

Open a **second terminal** in VS Code:

```bash
cd frontend

# Install Node.js dependencies
npm install
```

### Step 6 – Run the frontend

```bash
# From frontend/ directory:
npm run dev
```

✅ Frontend running at: [http://localhost:3000](http://localhost:3000)

---

## 📄 PDF Generation Steps

1. Open [http://localhost:3000](http://localhost:3000)
2. Enter the **Company Name** (e.g. "Eternal Limited")
3. **Upload** a financial document (PDF, TXT, or CSV)
4. Click **"Analyze & Generate Report"**
5. Wait for AI extraction (~15-30 seconds depending on document size)
6. Click **"Download PDF Report"** to save the Geojit-style report

The generated PDF is also saved to `generated_reports/` folder.

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check |
| `GET` | `/health` | Detailed health |
| `POST` | `/analyze` | Main: upload doc, get report |
| `GET` | `/download/{filename}` | Download a generated PDF |

**POST `/analyze` request:**
```
Content-Type: multipart/form-data
Fields:
  - company_name: string
  - file: PDF/TXT/CSV file
```

**Response JSON:**
```json
{
  "success": true,
  "session_id": "abc12345",
  "financial_data": {
    "company_name": "Eternal Limited",
    "sector": "Internet & Catalogue Retail",
    "rating": "HOLD",
    "target_price": 337,
    "cmp": 306,
    "highlights": ["..."],
    "outlook": "...",
    "risks": ["..."],
    "revenue": [{"year": "FY23", "value": 7079}, ...],
    "ebitda":  [{"year": "FY23", "value": -1210}, ...],
    "pat":     [{"year": "FY23", "value": -971}, ...]
  },
  "report_url": "/reports/report_Eternal_Limited_abc12345.pdf",
  "chart_urls": {
    "revenue": "/reports/charts/revenue_abc12345.png",
    "ebitda":  "/reports/charts/ebitda_abc12345.png",
    "pat":     "/reports/charts/pat_abc12345.png"
  }
}
```

---

## 🐛 Troubleshooting

**WeasyPrint / PDF fails on Linux:**
```bash
sudo apt-get install -y libpangocairo-1.0-0 libpango-1.0-0 libcairo2
```

**OpenAI error "Incorrect API key":**
- Check your `.env` file has `OPENAI_API_KEY=sk-proj-...` (no quotes, no spaces)
- Restart the backend after editing `.env`

**PyMuPDF import error:**
```bash
pip install PyMuPDF==1.24.3
```

**CORS errors in browser:**
- Ensure backend is running on port 8000
- Check `NEXT_PUBLIC_API_URL=http://localhost:8000` in `.env`

**"Could not extract text" from PDF:**
- Scanned PDFs (images-only) may not extract well; try a text-based PDF
- Or copy the text and upload as `.txt`

---

## 🏛 Architecture

```
Browser (Next.js)
      │
      │ POST /analyze (multipart form)
      ▼
FastAPI Backend
      │
      ├─ parser.py      → extract raw text (PyMuPDF/CSV/TXT)
      ├─ extractor.py   → call OpenAI GPT-4o → structured JSON
      ├─ charts.py      → Matplotlib PNG charts
      └─ report_generator.py
              │
              ├─ Jinja2 renders geojit_template.html
              └─ WeasyPrint → PDF
```

---

## 📝 License

MIT License – for educational and professional use.

---

*Standard Warning: Investment in securities market are subject to market risks. Read all the related documents carefully before investing.*
=======
# AI_DOCUMENT_ANALYZER
>>>>>>> 8154ca1233b76d3fd5046cfa05d126330161b4ce
