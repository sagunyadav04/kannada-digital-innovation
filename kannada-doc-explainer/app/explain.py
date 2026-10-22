"""Offline, rule-based explanation: document type, dates, amounts and a Kannada->English glossary.

This runs with no API key, so the app still explains documents when the AI is unavailable.
"""
import re

KN_DIGITS = str.maketrans("೦೧೨೩೪೫೬೭೮೯", "0123456789")

GLOSSARY = {
    "ವಿದ್ಯುತ್": "electricity", "ಬಿಲ್": "bill", "ಬಾಕಿ": "outstanding / overdue amount",
    "ದಂಡ": "penalty / fine", "ಕೊನೆಯ ದಿನಾಂಕ": "last date (deadline)", "ದಿನಾಂಕ": "date",
    "ಮೊತ್ತ": "amount", "ಒಟ್ಟು": "total", "ಪಾವತಿ": "payment", "ಸಹಿ": "signature",
    "ಅರ್ಜಿ": "application", "ನೋಟಿಸ್": "notice", "ಆದೇಶ": "order", "ತೆರಿಗೆ": "tax",
    "ಆಸ್ತಿ": "property", "ಜಮೀನು": "land", "ಪಹಣಿ": "RTC (land record of rights)",
    "ಸರ್ವೆ ನಂಬರ್": "survey number", "ಖಾತಾ": "khata (property account)", "ಬಾಡಿಗೆ": "rent",
    "ಠೇವಣಿ": "deposit", "ಒಪ್ಪಂದ": "agreement", "ಹೆಸರು": "name", "ವಿಳಾಸ": "address",
    "ಮೀಟರ್": "meter", "ಯೂನಿಟ್": "units (kWh)", "ಗ್ರಾಹಕ": "customer",
    "ಖಾತೆ ಸಂಖ್ಯೆ": "account number", "ಜನ್ಮ ದಿನಾಂಕ": "date of birth",
    "ಪ್ರಮಾಣ ಪತ್ರ": "certificate", "ಶುಲ್ಕ": "fee", "ರಶೀದಿ": "receipt",
    "ಕಡ್ಡಾಯ": "mandatory", "ತುರ್ತು": "urgent", "ವಿಚಾರಣೆ": "hearing",
    "ನ್ಯಾಯಾಲಯ": "court", "ಪೊಲೀಸ್": "police", "ಸಂಪರ್ಕ ಕಡಿತ": "disconnection",
    "ನೀರು": "water", "ಮಾಲೀಕ": "owner / landlord", "ಬಾಡಿಗೆದಾರ": "tenant",
}

DOC_TYPES = {
    "electricity_bill": ("Electricity bill", ["ವಿದ್ಯುತ್", "ಬೆಸ್ಕಾಂ", "ಯೂನಿಟ್", "ಮೀಟರ್"],
                         ["Check the total amount and the last date to pay.",
                          "Pay before the last date to avoid a penalty or disconnection."]),
    "land_record": ("Land record (RTC / Pahani)", ["ಪಹಣಿ", "ಸರ್ವೆ", "ಜಮೀನು", "ಖಾತಾ"],
                    ["Verify the owner name and survey number match your papers.",
                     "Keep a copy; banks and registrars ask for it."]),
    "rental_agreement": ("Rental agreement", ["ಬಾಡಿಗೆ", "ಠೇವಣಿ", "ಬಾಡಿಗೆದಾರ"],
                         ["Check rent, deposit, notice period and lock-in terms before signing."]),
    "legal_notice": ("Notice / legal document", ["ನೋಟಿಸ್", "ನ್ಯಾಯಾಲಯ", "ವಿಚಾರಣೆ", "ಆದೇಶ"],
                     ["Note any hearing or reply date; consider getting advice from a lawyer."]),
    "tax": ("Tax document", ["ತೆರಿಗೆ"], ["Check the amount due and the payment deadline."]),
    "certificate": ("Certificate", ["ಪ್ರಮಾಣ ಪತ್ರ", "ಜನ್ಮ ದಿನಾಂಕ"],
                    ["Check that name and date of birth are spelled correctly."]),
}

DATE_RE = re.compile(r"(?<!\d)(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{4}|\d{2})(?!\d)")
AMOUNT_RE = re.compile(
    r"(?:₹|Rs\.?|INR|ರೂ\.?)\s*([\d,]+(?:\.\d{1,2})?)|([\d,]+(?:\.\d{1,2})?)\s*(?:ರೂಪಾಯಿ|ರೂ)",
    re.I,
)
PHONE_RE = re.compile(r"(?<!\d)[6-9]\d{9}(?!\d)")


def normalize_digits(text: str) -> str:
    return text.translate(KN_DIGITS)


def find_dates(text: str):
    seen = []
    for d, m, y in DATE_RE.findall(normalize_digits(text)):
        if 1 <= int(d) <= 31 and 1 <= int(m) <= 12:
            s = f"{int(d):02d}/{int(m):02d}/{y}"
            if s not in seen:
                seen.append(s)
    return seen


def find_amounts(text: str):
    seen = []
    for a, b in AMOUNT_RE.findall(normalize_digits(text)):
        v = (a or b).rstrip(".,")
        if v and v not in seen:
            seen.append(v)
    return [f"₹{v}" for v in seen]


def find_glossary(text: str):
    # Longest terms first so "ಜನ್ಮ ದಿನಾಂಕ" wins over "ದಿನಾಂಕ".
    hits, covered = [], text
    for kn in sorted(GLOSSARY, key=len, reverse=True):
        if kn in covered:
            hits.append({"kn": kn, "en": GLOSSARY[kn]})
            covered = covered.replace(kn, " ")
    return hits


def detect_type(text: str):
    best, best_score = "other", 0
    for key, (_, kws, _) in DOC_TYPES.items():
        score = sum(text.count(k) for k in kws)
        if score > best_score:
            best, best_score = key, score
    return best


def analyze(text: str) -> dict:
    doc_type = detect_type(text)
    label, _, tips = DOC_TYPES.get(doc_type, ("Document", [], []))
    dates, amounts, phones = find_dates(text), find_amounts(text), PHONE_RE.findall(normalize_digits(text))
    facts = []
    if dates:
        facts.append({"label": "Dates found", "value": ", ".join(dates)})
    if amounts:
        facts.append({"label": "Amounts found", "value": ", ".join(amounts)})
    if phones:
        facts.append({"label": "Phone numbers", "value": ", ".join(dict.fromkeys(phones))})
    if doc_type == "other":
        summary = "Could not tell what kind of document this is from the text alone."
    else:
        summary = f"This looks like a {label.lower()}."
    return {
        "doc_type": doc_type, "doc_type_label": label if doc_type != "other" else "Document",
        "summary": summary, "key_facts": facts, "action_items": list(tips),
        "translation_en": "", "glossary": find_glossary(text), "source": "rules",
    }


def merge(rules: dict, ai: dict | None) -> dict:
    """Prefer AI summary/facts/translation when present; always keep the offline glossary."""
    if not ai:
        return rules
    out = dict(rules)
    dt = ai.get("doc_type")
    if dt in DOC_TYPES:
        out["doc_type"], out["doc_type_label"] = dt, DOC_TYPES[dt][0]
    out["summary"] = ai.get("summary") or rules["summary"]
    out["key_facts"] = ai.get("key_facts") or rules["key_facts"]
    out["action_items"] = ai.get("action_items") or rules["action_items"]
    out["translation_en"] = ai.get("translation_en", "")
    out["source"] = "ai"
    return out
