"""
FILE: backend/main.py
FastAPI application entry point for the Financial Report Analyzer.
"""

import os
import uuid
import json
import traceback
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from parser import extract_text_from_file
from extractor import extract_financial_data
from charts import generate_all_charts
from report_generator import generate_pdf_report

app = FastAPI(
    title="Financial Report Analyzer API",
    description="AI-powered financial document analysis and report generation",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GENERATED_REPORTS_DIR = Path(__file__).parent.parent / "generated_reports"
GENERATED_REPORTS_DIR.mkdir(exist_ok=True)

CHARTS_DIR = Path(__file__).parent.parent / "generated_reports" / "charts"
CHARTS_DIR.mkdir(exist_ok=True)

app.mount("/reports", StaticFiles(directory=str(GENERATED_REPORTS_DIR)), name="reports")


@app.get("/")
async def root():
    return {"message": "Financial Report Analyzer API is running", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/analyze")
async def analyze_document(
    company_name: str = Form(...),
    file: UploadFile = File(...)
):
    """
    Main endpoint: accepts company name + financial document,
    runs AI extraction, generates charts, produces PDF report.
    """
    allowed_types = [
        "application/pdf",
        "text/plain",
        "text/csv",
        "application/vnd.ms-excel",
        "application/octet-stream",
    ]
    if file.content_type not in allowed_types and not file.filename.endswith((".pdf", ".txt", ".csv")):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. Upload PDF, TXT, or CSV."
        )

    session_id = str(uuid.uuid4())[:8]

    try:
        # 1. Read file bytes
        file_bytes = await file.read()
        file_extension = Path(file.filename).suffix.lower()

        # 2. Extract raw text from document
        raw_text = extract_text_from_file(file_bytes, file_extension, company_name)

        if not raw_text or len(raw_text.strip()) < 50:
            raise HTTPException(
                status_code=422,
                detail="Could not extract sufficient text from the document. Please check the file."
            )

        # 3. AI extraction → structured JSON
        financial_data = extract_financial_data(raw_text, company_name)

        # 4. Generate charts
        chart_paths = generate_all_charts(financial_data, session_id, str(CHARTS_DIR))

        # 5. Generate PDF report
        report_filename = f"report_{company_name.replace(' ', '_')}_{session_id}.pdf"
        report_path = GENERATED_REPORTS_DIR / report_filename

        generate_pdf_report(
            financial_data=financial_data,
            chart_paths=chart_paths,
            output_path=str(report_path),
            session_id=session_id,
        )

        return JSONResponse({
            "success": True,
            "session_id": session_id,
            "financial_data": financial_data,
            "report_url": f"/reports/{report_filename}",
            "chart_urls": {
                k: f"/reports/charts/{Path(v).name}"
                for k, v in chart_paths.items()
            },
        })

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.get("/download/{filename}")
async def download_report(filename: str):
    """Download a generated PDF report."""
    file_path = GENERATED_REPORTS_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Report not found")
    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        filename=filename
    )
