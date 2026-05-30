"""
FILE: backend/extractor.py
Calls Google Gemini API to extract structured financial data.
Uses the gemini-2.5-flash model via the google-genai Python SDK.
"""

import os
import json
import logging
import re
from typing import Dict, Any

from dotenv import load_dotenv
from prompts import build_extraction_prompt, SYSTEM_PROMPT

load_dotenv()

logger = logging.getLogger(__name__)


def get_gemini_client():
    """Lazily initialise Gemini client."""
    try:
        from google import genai
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY environment variable not set.")
        return genai.Client(api_key=api_key)
    except ImportError:
        raise RuntimeError("google-genai package not installed. Run: pip install google-genai")


def clean_json_response(raw: str) -> str:
    """Strip markdown fences and whitespace from LLM response."""
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.MULTILINE)
    raw = re.sub(r"\s*```$", "", raw, flags=re.MULTILINE)
    return raw.strip()


def recover_truncated_json(raw: str) -> str:
    """
    Best-effort repair of a truncated JSON string.
    Closes any unclosed strings, arrays, and objects so json.loads
    has a chance to succeed and return whatever was fully extracted.
    """
    cleaned = raw.strip()

    open_braces = 0
    open_brackets = 0
    in_string = False
    escape_next = False

    for ch in cleaned:
        if escape_next:
            escape_next = False
            continue
        if ch == "\\" and in_string:
            escape_next = True
            continue
        if ch == '"' and not escape_next:
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            open_braces += 1
        elif ch == "}":
            open_braces -= 1
        elif ch == "[":
            open_brackets += 1
        elif ch == "]":
            open_brackets -= 1

    suffix = ""
    if in_string:
        suffix += '"'
    suffix += "]" * max(open_brackets, 0)
    suffix += "}" * max(open_braces, 0)

    return cleaned + suffix



def validate_and_fill_defaults(data: Dict[str, Any], company_name: str) -> Dict[str, Any]:
    """Ensures all required keys exist with sensible defaults."""
    year_series = [
        {"year": "FY23", "value": None},
        {"year": "FY24", "value": None},
        {"year": "FY25", "value": None},
        {"year": "FY26E", "value": None},
        {"year": "FY27E", "value": None},
    ]

    defaults = {
        "company_name": company_name,
        "formerly_known_as": "",
        "sector": "N/A",
        "rating": "N/A",
        "target_price": None,
        "cmp": None,
        "expected_return_pct": None,
        "time_frame": "12 Months",
        "market_cap": "N/A",
        "enterprise_value": "N/A",
        "stock_type": "N/A",
        "bloomberg_code": "N/A",
        "nse_code": "N/A",
        "bse_code": "N/A",
        "face_value": "N/A",
        "beta": None,
        "week_52_high": None,
        "week_52_low": None,
        "free_float_pct": None,
        "outstanding_shares": "N/A",
        "dividend_yield": "N/A",
        "company_description": f"{company_name} is a listed company.",
        "highlights": [],
        "outlook": "Outlook information not available in the document.",
        "risks": [],
        "revenue": [dict(r) for r in year_series],
        "ebitda": [dict(r) for r in year_series],
        "pat": [dict(r) for r in year_series],
        "ebitda_margin": [dict(r) for r in year_series],
        "eps": [dict(r) for r in year_series],
        "roe": [dict(r) for r in year_series],
        "pe_ratio": [dict(r) for r in year_series],
        "quarterly_financials": {
            "current_quarter": "Q1FY26",
            "prev_year_quarter": "Q1FY25",
            "prev_quarter": "Q4FY25",
            "sales_current": None,
            "sales_yoy_growth": None,
            "sales_qoq_growth": None,
            "ebitda_current": None,
            "ebitda_yoy_growth": None,
            "ebitda_margin_current": None,
            "pat_current": None,
            "pat_yoy_growth": None,
            "ebit_current": None,
            "pbt_current": None,
        },
        "shareholding": {
            "promoters": None,
            "fii": None,
            "mf_institutions": None,
            "public": None,
            "others": None,
        },
        "price_performance": {
            "absolute_3m": None,
            "absolute_6m": None,
            "absolute_1y": None,
            "relative_3m": None,
            "relative_6m": None,
            "relative_1y": None,
        },
        "analyst_name": "",
        "report_date": "",
        "valuation_basis": "",
    }

    for key, default_val in defaults.items():
        if key not in data or data[key] is None:
            data[key] = default_val

    for series_key in ("revenue", "ebitda", "pat", "ebitda_margin", "eps", "roe", "pe_ratio"):
        if not isinstance(data.get(series_key), list) or len(data[series_key]) == 0:
            data[series_key] = [dict(r) for r in year_series]

    for nested_key in ("quarterly_financials", "shareholding", "price_performance"):
        if not isinstance(data.get(nested_key), dict):
            data[nested_key] = defaults[nested_key]

    return data


def extract_financial_data(document_text: str, company_name: str) -> Dict[str, Any]:
    """
    Main extraction function.
    Sends document text to Gemini and returns structured financial data dict.
    """
    from google.genai import types

    client = get_gemini_client()
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    prompt = build_extraction_prompt(company_name, document_text)

    logger.info(f"Calling Gemini {model} for financial extraction...")

    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                max_output_tokens=8192,
                temperature=0.1,
                response_mime_type="application/json",
            ),
        )

        # Warn if the model stopped early due to token limit
        candidate = response.candidates[0] if response.candidates else None
        if candidate and hasattr(candidate, "finish_reason"):
            finish_reason = str(candidate.finish_reason)
            if finish_reason not in ("FinishReason.STOP", "STOP", "1"):
                logger.warning(f"Gemini finish_reason={finish_reason} — response may be truncated")

        raw_content = response.text
        logger.info(f"Gemini response received ({len(raw_content)} chars)")

    except Exception as e:
        logger.error(f"Gemini API call failed: {e}")
        raise RuntimeError(f"Gemini API error: {e}")

    # Parse JSON — with truncation-recovery fallback
    cleaned = clean_json_response(raw_content)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as primary_err:
        logger.warning(f"Primary JSON parse failed ({primary_err}), attempting truncation recovery...")
        try:
            repaired = recover_truncated_json(cleaned)
            data = json.loads(repaired)
            logger.info("Truncation recovery succeeded.")
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse failed after recovery. Raw response:\n{raw_content[:800]}")
            raise RuntimeError(f"Could not parse AI response as JSON: {e}")

    data = validate_and_fill_defaults(data, company_name)
    logger.info(f"Extraction complete for: {data.get('company_name')}")
    return data