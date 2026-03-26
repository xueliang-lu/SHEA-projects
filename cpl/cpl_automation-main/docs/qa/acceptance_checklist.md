# CPL Automation QA Acceptance Checklist

## 1) Extraction Accuracy Target Harness
- [ ] Parser can ingest transcript text fixture and return structured extraction payload.
- [ ] Required keys present: `student_id`, `decision`, `recommended_credits`, `confidence`, `evidence`.
- [ ] Accuracy harness compares parser outputs to expected fixture outputs.
- [ ] Target: >= 0.85 exact-match on `student_id` + `decision`, and >= 0.75 overlap on `recommended_credits` across benchmark set.

## 2) Recommendation Presence
- [ ] Matcher returns >=1 recommendation for positive/partial extraction cases.
- [ ] Every recommendation includes `code` and `reason`.
- [ ] Confidence values (if present) are bounded in [0, 1].

## 3) Decision Audit Trail
- [ ] DB schema can initialize on clean sqlite file.
- [ ] CRUD lifecycle works: create application -> fetch -> update decision -> list.
- [ ] Updated decisions preserve audit rationale text.

## 4) CSV Export Output
- [ ] Export writes CSV file without error.
- [ ] CSV contains required columns (`student_id`, `decision`, etc.).
- [ ] Exported values preserve decision and recommended credit strings.

## 5) Automation / CI
- [ ] `pytest` runs from repo root using `python3 -m pytest -ra`.
- [ ] Test suite is deterministic with synthetic fixture inputs.
