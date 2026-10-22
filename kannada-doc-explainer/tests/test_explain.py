from app import explain

BILL = """ಬೆಸ್ಕಾಂ ವಿದ್ಯುತ್ ಬಿಲ್
ಗ್ರಾಹಕ ಹೆಸರು: ರಾಮ್
ಬಿಲ್ ದಿನಾಂಕ: ೧೨/೧೦/೨೦೨೬
ಕೊನೆಯ ದಿನಾಂಕ: 28-10-2026
ಒಟ್ಟು ಮೊತ್ತ: ರೂ. ೧,೨೩೪.೫೦
ಯೂನಿಟ್ 210"""


def test_detects_electricity_bill():
    assert explain.analyze(BILL)["doc_type"] == "electricity_bill"


def test_kannada_digits_dates_amounts():
    r = explain.analyze(BILL)
    facts = {f["label"]: f["value"] for f in r["key_facts"]}
    assert "12/10/2026" in facts["Dates found"] and "28/10/2026" in facts["Dates found"]
    assert "₹1,234.50" in facts["Amounts found"]


def test_glossary_prefers_longest_term():
    kn = [g["kn"] for g in explain.analyze(BILL)["glossary"]]
    assert "ಕೊನೆಯ ದಿನಾಂಕ" in kn and "ವಿದ್ಯುತ್" in kn


def test_invalid_date_ignored():
    assert explain.find_dates("99/99/2026") == []


def test_unknown_doc():
    assert explain.analyze("hello world")["doc_type"] == "other"
