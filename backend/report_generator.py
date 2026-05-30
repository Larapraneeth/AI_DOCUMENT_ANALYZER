"""
FILE: backend/report_generator.py
Renders a structured equity research PDF using ReportLab Platypus.
Replaces the previous WeasyPrint / Jinja2 HTML approach.
"""

import os
import base64
import logging
from io import BytesIO
from pathlib import Path
from typing import Dict, Any

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, Image,
)

logger = logging.getLogger(__name__)

OUTPUT_DIR = Path(__file__).parent.parent / "generated_reports"

# ── Page geometry ──────────────────────────────────────────────────────────
PAGE_W, PAGE_H = A4
PAGE_M   = 12 * mm      # left / right margin
BOTTOM_M = 14 * mm      # bottom margin for footer
TOP_M    = 12 * mm

# ── Colour palette ─────────────────────────────────────────────────────────
DARK_BLUE  = colors.HexColor("#1B3A6B")
MID_BLUE   = colors.HexColor("#2E5FA3")
LIGHT_BLUE = colors.HexColor("#EAF0FB")
ACCENT     = colors.HexColor("#E8A020")
BUY_GREEN  = colors.HexColor("#1A7A3C")
HOLD_AMBER = colors.HexColor("#B8860B")
SELL_RED   = colors.HexColor("#C0392B")
BORDER     = colors.HexColor("#D0D8E8")
LIGHT_GREY = colors.HexColor("#F5F6FA")
TEXT_DARK  = colors.HexColor("#1A1A2E")
TEXT_MED   = colors.HexColor("#4A4A6A")
WHITE      = colors.white


# ── Style registry ─────────────────────────────────────────────────────────

def _build_styles() -> Dict[str, ParagraphStyle]:
    def s(**kw):
        return ParagraphStyle(**kw)

    return {
        "doc_title":   s(name="DocTitle",   fontSize=18, leading=22, textColor=WHITE,
                         fontName="Helvetica-Bold", alignment=TA_LEFT),
        "subtitle":    s(name="Subtitle",   fontSize=10, leading=13, textColor=LIGHT_BLUE,
                         fontName="Helvetica", alignment=TA_LEFT),
        "desc":        s(name="Desc",       fontSize=7.5, leading=10, textColor=LIGHT_BLUE,
                         fontName="Helvetica"),
        "section_hd":  s(name="SectionHd",  fontSize=10, leading=13, textColor=WHITE,
                         fontName="Helvetica-Bold", alignment=TA_LEFT),
        "body":        s(name="Body",        fontSize=8.5, leading=12, textColor=TEXT_DARK,
                         fontName="Helvetica", alignment=TA_JUSTIFY),
        "bullet":      s(name="Bullet",      fontSize=8.5, leading=12, textColor=TEXT_DARK,
                         fontName="Helvetica", leftIndent=10),
        "table_hd":    s(name="TableHd",     fontSize=8, leading=10, textColor=WHITE,
                         fontName="Helvetica-Bold", alignment=TA_CENTER),
        "table_cell":  s(name="TableCell",   fontSize=8, leading=10, textColor=TEXT_DARK,
                         fontName="Helvetica", alignment=TA_RIGHT),
        "table_label": s(name="TableLabel",  fontSize=8, leading=10, textColor=TEXT_DARK,
                         fontName="Helvetica-Bold", alignment=TA_LEFT),
        "kpi_val":     s(name="KpiVal",      fontSize=13, leading=16, textColor=DARK_BLUE,
                         fontName="Helvetica-Bold", alignment=TA_CENTER),
        "kpi_lbl":     s(name="KpiLbl",      fontSize=7,  leading=9,  textColor=TEXT_MED,
                         fontName="Helvetica", alignment=TA_CENTER),
        "rating_buy":  s(name="RatingBuy",   fontSize=13, leading=16, textColor=BUY_GREEN,
                         fontName="Helvetica-Bold", alignment=TA_CENTER),
        "rating_hold": s(name="RatingHold",  fontSize=13, leading=16, textColor=HOLD_AMBER,
                         fontName="Helvetica-Bold", alignment=TA_CENTER),
        "rating_sell": s(name="RatingSell",  fontSize=13, leading=16, textColor=SELL_RED,
                         fontName="Helvetica-Bold", alignment=TA_CENTER),
        "small_label": s(name="SmallLabel",  fontSize=7,  leading=9,  textColor=TEXT_MED,
                         fontName="Helvetica"),
        "kpi_val_wh":  s(name="KpiValWh",    fontSize=13, leading=16, textColor=WHITE,
                         fontName="Helvetica-Bold", alignment=TA_CENTER),
    }


# ── Formatting helpers ─────────────────────────────────────────────────────

def format_value(val, suffix="", prefix="", decimal=1, na="N/A") -> str:
    """Safely format a numeric value for display."""
    if val is None:
        return na
    try:
        return f"{prefix}{float(val):,.{decimal}f}{suffix}"
    except (TypeError, ValueError):
        return str(val)


def format_growth(val, na="N/A") -> str:
    """Format growth percentage with sign."""
    if val is None:
        return na
    try:
        v = float(val)
        return f"{'+'if v >= 0 else''}{v:.1f}%"
    except (TypeError, ValueError):
        return str(val)


def get_rating_class(rating: str) -> str:
    """Map rating string to CSS-equivalent key."""
    r = str(rating).upper()
    if r in ("BUY", "ACCUMULATE"):
        return "rating_buy"
    if r in ("HOLD", "NEUTRAL"):
        return "rating_hold"
    if r in ("SELL", "REDUCE"):
        return "rating_sell"
    return "kpi_val"


# ── Section header ─────────────────────────────────────────────────────────

def _section_header(title: str, S: dict) -> Table:
    cw = PAGE_W - 2 * PAGE_M
    tbl = Table([[Paragraph(title, S["section_hd"])]], colWidths=[cw])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), DARK_BLUE),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
    ]))
    return tbl


# ── Header banner ──────────────────────────────────────────────────────────

def _build_header(d: dict, S: dict) -> Table:
    CW = PAGE_W - 2 * PAGE_M

    sector_line = d.get("sector", "")
    if d.get("stock_type"):
        sector_line += f"  |  {d['stock_type']}"

    left = Table([
        [Paragraph(d.get("company_name", ""), S["doc_title"])],
        [Paragraph(sector_line, S["subtitle"])],
        [Paragraph(d.get("company_description", ""), S["desc"])],
    ], colWidths=[CW * 0.62])
    left.setStyle(TableStyle([
        ("TOPPADDING",    (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
    ]))

    rating     = d.get("rating", "N/A")
    rating_key = get_rating_class(rating)
    kw         = CW * 0.38 / 3
    kpis = [
        [Paragraph("RATING",  S["kpi_lbl"]),
         Paragraph("CMP",     S["kpi_lbl"]),
         Paragraph("TARGET",  S["kpi_lbl"])],
        [Paragraph(str(rating), S[rating_key]),
         Paragraph(format_value(d.get("cmp"),          prefix="Rs.", decimal=0), S["kpi_val_wh"]),
         Paragraph(format_value(d.get("target_price"), prefix="Rs.", decimal=0), S["kpi_val_wh"])],
        [Paragraph("",                                  S["kpi_lbl"]),
         Paragraph(d.get("time_frame", "12M"),          S["kpi_lbl"]),
         Paragraph(format_value(d.get("expected_return_pct"), suffix="%"), S["kpi_lbl"])],
    ]
    kt = Table(kpis, colWidths=[kw] * 3)
    kt.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), MID_BLUE),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 4),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
        ("LINEBELOW",     (0, 0), (-1, 0),  0.5, LIGHT_BLUE),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))

    banner = Table([[left, kt]], colWidths=[CW * 0.62, CW * 0.38])
    banner.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), DARK_BLUE),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
    ]))
    return banner


# ── Key metrics strip ──────────────────────────────────────────────────────

def _build_key_metrics(d: dict, S: dict) -> Table:
    CW = PAGE_W - 2 * PAGE_M
    items = [
        ("Market Cap",  d.get("market_cap", "N/A")),
        ("52W High",    format_value(d.get("week_52_high"), prefix="Rs.")),
        ("52W Low",     format_value(d.get("week_52_low"),  prefix="Rs.")),
        ("Beta",        format_value(d.get("beta"),         decimal=2)),
        ("Free Float",  format_value(d.get("free_float_pct"), suffix="%")),
        ("Div Yield",   str(d.get("dividend_yield", "N/A"))),
        ("NSE Code",    str(d.get("nse_code",        "N/A"))),
        ("Face Value",  str(d.get("face_value",      "N/A"))),
    ]
    cw  = CW / len(items)
    val_style = ParagraphStyle(name="MV", fontSize=8, leading=10, textColor=DARK_BLUE,
                               fontName="Helvetica-Bold", alignment=TA_CENTER)
    hdr_row = [Paragraph(k, S["kpi_lbl"]) for k, _ in items]
    val_row = [Paragraph(str(v), val_style) for _, v in items]
    tbl = Table([hdr_row, val_row], colWidths=[cw] * len(items))
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  LIGHT_BLUE),
        ("BACKGROUND",    (0, 1), (-1, 1),  WHITE),
        ("GRID",          (0, 0), (-1, -1), 0.4, BORDER),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return tbl


# ── Annual financials table ────────────────────────────────────────────────

YEARS = ["FY23", "FY24", "FY25", "FY26E", "FY27E"]


def _series_row(label: str, series, S: dict, suffix="", decimal=1):
    lookup = {r["year"]: r.get("value") for r in (series or [])}
    row = [Paragraph(label, S["table_label"])]
    for y in YEARS:
        row.append(Paragraph(format_value(lookup.get(y), suffix=suffix, decimal=decimal),
                              S["table_cell"]))
    return row


def _build_annual_table(d: dict, S: dict) -> Table:
    CW = PAGE_W - 2 * PAGE_M
    lw = CW * 0.24
    yw = (CW - lw) / len(YEARS)
    hdr = [Paragraph("Metric", S["table_hd"])] + [Paragraph(y, S["table_hd"]) for y in YEARS]
    rows = [
        hdr,
        _series_row("Revenue (Rs. Cr)",    d.get("revenue",       []), S),
        _series_row("EBITDA (Rs. Cr)",     d.get("ebitda",        []), S),
        _series_row("PAT (Rs. Cr)",        d.get("pat",           []), S),
        _series_row("EBITDA Margin (%)",   d.get("ebitda_margin", []), S, suffix="%"),
        _series_row("EPS (Rs.)",           d.get("eps",           []), S, decimal=2),
        _series_row("ROE (%)",             d.get("roe",           []), S, suffix="%"),
        _series_row("P/E (x)",             d.get("pe_ratio",      []), S),
    ]
    tbl = Table(rows, colWidths=[lw] + [yw] * len(YEARS))
    style = [
        ("BACKGROUND",    (0, 0), (-1, 0),  MID_BLUE),
        ("GRID",          (0, 0), (-1, -1), 0.4, BORDER),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING",   (0, 0), (-1, -1), 5),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 5),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]
    for i in range(1, len(rows)):
        style.append(("BACKGROUND", (0, i), (-1, i), LIGHT_GREY if i % 2 == 0 else WHITE))
    tbl.setStyle(TableStyle(style))
    return tbl


# ── Quarterly financials table ─────────────────────────────────────────────

def _build_quarterly_table(d: dict, S: dict) -> Table:
    CW = PAGE_W - 2 * PAGE_M
    q  = d.get("quarterly_financials", {})
    cq = q.get("current_quarter",   "Q1FY26")
    py = q.get("prev_year_quarter", "Q1FY25")
    pq = q.get("prev_quarter",      "Q4FY25")
    cws = [CW*0.26, CW*0.185, CW*0.185, CW*0.13, CW*0.13, CW*0.11]
    hdr = [Paragraph(h, S["table_hd"])
           for h in ["Metric", cq, py, "YoY%", pq, "QoQ%"]]

    def qrow(label, cur, yoy, qoq):
        return [Paragraph(label, S["table_label"]),
                Paragraph(format_value(cur),      S["table_cell"]),
                Paragraph("—",                    S["table_cell"]),
                Paragraph(format_growth(yoy),     S["table_cell"]),
                Paragraph("—",                    S["table_cell"]),
                Paragraph(format_growth(qoq),     S["table_cell"])]

    rows = [
        hdr,
        qrow("Sales (Rs. Cr)",   q.get("sales_current"),  q.get("sales_yoy_growth"),  q.get("sales_qoq_growth")),
        qrow("EBITDA (Rs. Cr)",  q.get("ebitda_current"), q.get("ebitda_yoy_growth"), None),
        qrow("EBITDA Margin (%)",q.get("ebitda_margin_current"), None, None),
        qrow("PAT (Rs. Cr)",     q.get("pat_current"),    q.get("pat_yoy_growth"),    None),
    ]
    tbl = Table(rows, colWidths=cws)
    style = [
        ("BACKGROUND",    (0, 0), (-1, 0),  MID_BLUE),
        ("GRID",          (0, 0), (-1, -1), 0.4, BORDER),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING",   (0, 0), (-1, -1), 5),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 5),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]
    for i in range(1, len(rows)):
        style.append(("BACKGROUND", (0, i), (-1, i), LIGHT_GREY if i % 2 == 0 else WHITE))
    tbl.setStyle(TableStyle(style))
    return tbl


# ── Shareholding + price performance ──────────────────────────────────────

def _build_share_price_row(d: dict, S: dict) -> Table:
    CW = PAGE_W - 2 * PAGE_M
    sh = d.get("shareholding",     {})
    pp = d.get("price_performance",{})

    sh_rows = [[Paragraph("Shareholder", S["table_hd"]), Paragraph("%", S["table_hd"])]]
    for label, key in [("Promoters","promoters"),("FII","fii"),
                        ("MF / Inst.","mf_institutions"),("Public","public"),("Others","others")]:
        sh_rows.append([Paragraph(label, S["table_label"]),
                         Paragraph(format_value(sh.get(key), suffix="%"), S["table_cell"])])
    sh_tbl = Table(sh_rows, colWidths=[CW*0.18, CW*0.10])
    sh_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  MID_BLUE),
        ("GRID",          (0, 0), (-1, -1), 0.4, BORDER),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING",   (0, 0), (-1, -1), 5),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 5),
    ]))

    pp_rows = [[Paragraph("Period", S["table_hd"]),
                Paragraph("Abs %", S["table_hd"]),
                Paragraph("Rel %", S["table_hd"])]]
    for label, ak, rk in [("3M","absolute_3m","relative_3m"),
                            ("6M","absolute_6m","relative_6m"),
                            ("1Y","absolute_1y","relative_1y")]:
        pp_rows.append([Paragraph(label, S["table_label"]),
                         Paragraph(format_growth(pp.get(ak)), S["table_cell"]),
                         Paragraph(format_growth(pp.get(rk)), S["table_cell"])])
    pp_tbl = Table(pp_rows, colWidths=[CW*0.10, CW*0.10, CW*0.10])
    pp_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  MID_BLUE),
        ("GRID",          (0, 0), (-1, -1), 0.4, BORDER),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING",   (0, 0), (-1, -1), 5),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 5),
    ]))

    wrapper = Table([[sh_tbl, Spacer(CW*0.04, 1), pp_tbl]],
                    colWidths=[CW*0.30, CW*0.04, CW*0.32])
    wrapper.setStyle(TableStyle([
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
    ]))
    return wrapper


# ── Chart image ────────────────────────────────────────────────────────────

def _chart_image(b64_str: str, width_mm: float = 82) -> Any:
    """Decode a base64 PNG chart into a ReportLab Image flowable."""
    if not b64_str:
        return None
    try:
        raw = base64.b64decode(b64_str)
        buf = BytesIO(raw)
        return Image(buf, width=width_mm * mm, height=width_mm * mm * 0.6)
    except Exception as e:
        logger.warning(f"Could not decode chart image: {e}")
        return None


# ── Bullet list ────────────────────────────────────────────────────────────

def _bullet_list(items, S: dict):
    out = []
    for item in (items or []):
        out.append(Paragraph(f"&#8226; &nbsp;{item}", S["bullet"]))
        out.append(Spacer(1, 2))
    return out


# ── Page footer/header callback ────────────────────────────────────────────

def _on_page(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 6.5)
    canvas.setFillColor(TEXT_MED)
    canvas.drawString(PAGE_M, 7 * mm,
                      "This report is for informational purposes only and does not constitute investment advice.")
    canvas.drawRightString(PAGE_W - PAGE_M, 7 * mm, f"Page {doc.page}")
    canvas.setStrokeColor(BORDER)
    canvas.setLineWidth(0.5)
    canvas.line(PAGE_M, 9 * mm, PAGE_W - PAGE_M, 9 * mm)
    canvas.restoreState()


# ── Story builder ──────────────────────────────────────────────────────────

def _build_story(financial_data: Dict[str, Any],
                 charts_b64:    Dict[str, str],
                 S:             dict) -> list:
    d     = financial_data
    story = []
    sp    = lambda h: Spacer(1, h * mm)

    # ── Header banner + key metrics ────────────────────────────────────────
    story.append(_build_header(d, S))
    story.append(sp(1.5))
    story.append(_build_key_metrics(d, S))
    story.append(sp(4))

    # ── Highlights ─────────────────────────────────────────────────────────
    highlights = d.get("highlights", [])
    if highlights:
        story.append(_section_header("KEY HIGHLIGHTS", S))
        story.append(sp(1.5))
        story.extend(_bullet_list(highlights, S))
        story.append(sp(4))

    # ── Outlook ────────────────────────────────────────────────────────────
    outlook = d.get("outlook", "")
    if outlook:
        story.append(_section_header("OUTLOOK", S))
        story.append(sp(1.5))
        story.append(Paragraph(outlook, S["body"]))
        story.append(sp(4))

    # ── Annual financials ──────────────────────────────────────────────────
    story.append(_section_header("ANNUAL FINANCIALS", S))
    story.append(sp(1.5))
    story.append(_build_annual_table(d, S))
    story.append(sp(4))

    # ── Charts (2-up layout) ───────────────────────────────────────────────
    CHART_KEYS = ["revenue_chart", "pat_chart", "margin_chart", "pe_chart"]
    imgs = [(k, _chart_image(charts_b64.get(k, ""), width_mm=82))
            for k in CHART_KEYS]
    valid_imgs = [(k, img) for k, img in imgs if img is not None]
    if valid_imgs:
        CW = PAGE_W - 2 * PAGE_M
        story.append(_section_header("CHARTS", S))
        story.append(sp(1.5))
        for i in range(0, len(valid_imgs), 2):
            pair = [v[1] for v in valid_imgs[i:i+2]]
            while len(pair) < 2:
                pair.append(Spacer(CW / 2, 1))
            row = Table([pair], colWidths=[CW / 2, CW / 2])
            row.setStyle(TableStyle([
                ("TOPPADDING",    (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ("LEFTPADDING",   (0, 0), (-1, -1), 0),
                ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
            ]))
            story.append(row)
            story.append(sp(2))
        story.append(sp(2))

    # ── Quarterly financials ───────────────────────────────────────────────
    story.append(_section_header("QUARTERLY FINANCIALS", S))
    story.append(sp(1.5))
    story.append(_build_quarterly_table(d, S))
    story.append(sp(4))

    # ── Shareholding + price performance ───────────────────────────────────
    story.append(_section_header("SHAREHOLDING & PRICE PERFORMANCE", S))
    story.append(sp(1.5))
    story.append(_build_share_price_row(d, S))
    story.append(sp(4))

    # ── Risks ──────────────────────────────────────────────────────────────
    risks = d.get("risks", [])
    if risks:
        story.append(_section_header("KEY RISKS", S))
        story.append(sp(1.5))
        story.extend(_bullet_list(risks, S))
        story.append(sp(4))

    # ── Valuation basis ────────────────────────────────────────────────────
    valuation = d.get("valuation_basis", "")
    if valuation:
        story.append(_section_header("VALUATION", S))
        story.append(sp(1.5))
        story.append(Paragraph(valuation, S["body"]))
        story.append(sp(4))

    # ── Analyst / date footer line ─────────────────────────────────────────
    analyst     = d.get("analyst_name", "")
    report_date = d.get("report_date",  "")
    meta_parts  = []
    if analyst:
        meta_parts.append(f"Analyst: {analyst}")
    if report_date:
        meta_parts.append(report_date)
    if meta_parts:
        story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER))
        story.append(sp(1))
        story.append(Paragraph("  |  ".join(meta_parts), S["small_label"]))

    return story


# ── Public API ─────────────────────────────────────────────────────────────

def image_to_base64(image_path: str) -> str:
    """Convert image file to base64 string for chart embedding."""
    if not image_path or not os.path.exists(image_path):
        return ""
    try:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except Exception as e:
        logger.warning(f"Could not encode image {image_path}: {e}")
        return ""


def generate_pdf_report(
    financial_data: Dict[str, Any],
    chart_paths:    Dict[str, str],
    output_path:    str,
    session_id:     str,
) -> None:
    """
    Full pipeline: financial_data + chart_paths → PDF saved to output_path.

    chart_paths values are filesystem paths to PNG files; they are encoded
    to base64 internally before being embedded in the document.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Generating PDF report for session {session_id} → {output_path}")

    # Encode chart images
    charts_b64 = {k: image_to_base64(v) for k, v in (chart_paths or {}).items()}

    S   = _build_styles()
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=PAGE_M,
        rightMargin=PAGE_M,
        topMargin=TOP_M,
        bottomMargin=BOTTOM_M,
        title=financial_data.get("company_name", "Equity Research Report"),
        author=financial_data.get("analyst_name", ""),
    )

    story = _build_story(financial_data, charts_b64, S)
    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
    logger.info(f"PDF report complete: {output_path}")