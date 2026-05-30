"""
FILE: backend/prompts.py
All OpenAI prompt templates for financial data extraction.
Centralised here for easy tuning and maintenance.
"""

SYSTEM_PROMPT = """You are an expert financial analyst and equity research assistant.
Your job is to extract structured financial data from research reports or financial documents.
You always respond with valid JSON only — no markdown, no explanation, no code blocks.
If a value is not found in the document, use null for numbers and "" for strings.
All monetary values should be in the original currency unit shown in the document (e.g., Rs. Cr).
"""

EXTRACTION_PROMPT_TEMPLATE = """
Analyse the following financial document for the company: {company_name}

Extract ALL the following fields and return a single valid JSON object:

{{
  "company_name": "Full company name",
  "formerly_known_as": "Previous company name if mentioned",
  "sector": "Industry sector",
  "rating": "BUY / HOLD / SELL / ACCUMULATE / REDUCE",
  "target_price": "Target price as number (e.g. 337)",
  "cmp": "Current Market Price as number (e.g. 306)",
  "expected_return_pct": "Expected return percentage as number (e.g. 10)",
  "time_frame": "e.g. 12 Months",
  "market_cap": "Market cap value",
  "enterprise_value": "Enterprise value",
  "stock_type": "e.g. Large Cap / Mid Cap / Small Cap",
  "bloomberg_code": "Bloomberg ticker",
  "nse_code": "NSE ticker",
  "bse_code": "BSE code",
  "face_value": "Face value",
  "beta": "Beta value as number",
  "week_52_high": "52-week high price",
  "week_52_low": "52-week low price",
  "free_float_pct": "Free float percentage",
  "outstanding_shares": "Outstanding shares",
  "dividend_yield": "Dividend yield",
  "company_description": "2-3 sentence description of what the company does",
  "highlights": [
    "Key highlight point 1",
    "Key highlight point 2",
    "Key highlight point 3",
    "Key highlight point 4",
    "Key highlight point 5"
  ],
  "outlook": "Detailed outlook paragraph (3-5 sentences)",
  "risks": [
    "Key risk 1",
    "Key risk 2",
    "Key risk 3"
  ],
  "revenue": [
    {{"year": "FY23", "value": null}},
    {{"year": "FY24", "value": null}},
    {{"year": "FY25", "value": null}},
    {{"year": "FY26E", "value": null}},
    {{"year": "FY27E", "value": null}}
  ],
  "ebitda": [
    {{"year": "FY23", "value": null}},
    {{"year": "FY24", "value": null}},
    {{"year": "FY25", "value": null}},
    {{"year": "FY26E", "value": null}},
    {{"year": "FY27E", "value": null}}
  ],
  "pat": [
    {{"year": "FY23", "value": null}},
    {{"year": "FY24", "value": null}},
    {{"year": "FY25", "value": null}},
    {{"year": "FY26E", "value": null}},
    {{"year": "FY27E", "value": null}}
  ],
  "ebitda_margin": [
    {{"year": "FY23", "value": null}},
    {{"year": "FY24", "value": null}},
    {{"year": "FY25", "value": null}},
    {{"year": "FY26E", "value": null}},
    {{"year": "FY27E", "value": null}}
  ],
  "eps": [
    {{"year": "FY23", "value": null}},
    {{"year": "FY24", "value": null}},
    {{"year": "FY25", "value": null}},
    {{"year": "FY26E", "value": null}},
    {{"year": "FY27E", "value": null}}
  ],
  "roe": [
    {{"year": "FY23", "value": null}},
    {{"year": "FY24", "value": null}},
    {{"year": "FY25", "value": null}},
    {{"year": "FY26E", "value": null}},
    {{"year": "FY27E", "value": null}}
  ],
  "pe_ratio": [
    {{"year": "FY23", "value": null}},
    {{"year": "FY24", "value": null}},
    {{"year": "FY25", "value": null}},
    {{"year": "FY26E", "value": null}},
    {{"year": "FY27E", "value": null}}
  ],
  "quarterly_financials": {{
    "current_quarter": "e.g. Q1FY26",
    "prev_year_quarter": "e.g. Q1FY25",
    "prev_quarter": "e.g. Q4FY25",
    "sales_current": null,
    "sales_yoy_growth": null,
    "sales_qoq_growth": null,
    "ebitda_current": null,
    "ebitda_yoy_growth": null,
    "ebitda_margin_current": null,
    "pat_current": null,
    "pat_yoy_growth": null,
    "ebit_current": null,
    "pbt_current": null
  }},
  "shareholding": {{
    "promoters": null,
    "fii": null,
    "mf_institutions": null,
    "public": null,
    "others": null
  }},
  "price_performance": {{
    "absolute_3m": null,
    "absolute_6m": null,
    "absolute_1y": null,
    "relative_3m": null,
    "relative_6m": null,
    "relative_1y": null
  }},
  "analyst_name": "Analyst name if mentioned",
  "report_date": "Report date if mentioned",
  "valuation_basis": "Valuation methodology used (e.g. 6x FY27 price/sales)"
}}

DOCUMENT TEXT:
{document_text}

Respond ONLY with the JSON object. No markdown, no explanation.
"""


def build_extraction_prompt(company_name: str, document_text: str) -> str:
    """Build the full extraction prompt with document text inserted."""
    # Truncate very long documents to stay within token limits (~12k chars)
    max_chars = 30000
    if len(document_text) > max_chars:
        document_text = document_text[:max_chars] + "\n\n[Document truncated for length]"

    return EXTRACTION_PROMPT_TEMPLATE.format(
        company_name=company_name,
        document_text=document_text,
    )
