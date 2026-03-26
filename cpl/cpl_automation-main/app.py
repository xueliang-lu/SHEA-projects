"""
CPL Automation System
Author: Sunil Paudel

Notes:
- Mandatory step: run AI retrieval first. All external units must be enriched via Playwright before matching.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from src.db import (
    init_db,
    upsert_shea_units,
    insert_external_units,
    fetch_external_units,
    fetch_shea_units,
    clear_shea_units,
    clear_external_units,
    clear_suggestions,
    insert_suggestions,
    fetch_suggestions,
    upsert_decision,
    update_external_unit_enrichment,
)
from src.export import export_rows_to_csv, export_rows_to_excel, export_rows_to_pdf
from src.matching import generate_matches
import src.retrieval_agent as retrieval_agent
from src.sample_data import SAMPLE_EXTERNAL_TEXT
from src.shea_loader import load_shea_units_from_excel
from src.transcript_extraction import extract_transcript_text, extract_header_text_via_ocr
from src.university_registry import load_registry, save_registry
from src.workflow import parse_external_units_from_text, rows_to_dicts, detect_institution

st.set_page_config(page_title="CPL Automation MVP", layout="wide")
st.title("CPL Automation MVP")
st.caption("Build: Transcript + course-structure outcomes/description workflow")

init_db()

with st.sidebar:
    st.markdown("### SHEA Data")
    if st.button("Load SHEA units from local Excel"):
        try:
            local_units = load_shea_units_from_excel()
            clear_shea_units()
            upsert_shea_units(local_units)
            st.success(f"Loaded/updated {len(local_units)} SHEA units from data/SHEA Course Data.xlsx")
        except Exception as exc:
            st.error(f"Local SHEA load failed: {exc}")

page = st.sidebar.radio(
    "Navigation",
    ["Upload Transcript", "CPL Suggestions", "Review & Approval"],
)

if "last_transcript_text" not in st.session_state:
    st.session_state.last_transcript_text = SAMPLE_EXTERNAL_TEXT
if "current_external_ids" not in st.session_state:
    st.session_state.current_external_ids = []
if "institution_name" not in st.session_state:
    st.session_state.institution_name = ""
if "institution_conf" not in st.session_state:
    st.session_state.institution_conf = 0.0


def _step_status_from_log(log: dict) -> dict:
    steps_text = (log.get("steps") or "").lower()
    return {
        "1_load_units": True,
        "2_build_query": "query:" in steps_text,
        "3_resolve_urls": "candidate_urls:" in steps_text,
        "4_playwright": "playwright_try:" in steps_text,
        "5_static_fallback": "static_try:" in steps_text,
        "6_extract_fields": (log.get("desc_len", 0) > 0) or (log.get("outcomes_len", 0) > 0),
        "7_confidence": log.get("confidence", 0) is not None,
        "8_save_db": bool(log.get("mode")) and str(log.get("mode")) != "none",
        "9_debug_log": True,
    }

if page == "Upload Transcript":
    st.header("1) Upload Transcript")
    st.caption("Upload text-based PDF transcript or use sample text.")

    institution = st.session_state.institution_name
    uploaded = st.file_uploader("Upload transcript PDF", type=["pdf"])

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Use sample transcript"):
            st.session_state.last_transcript_text = SAMPLE_EXTERNAL_TEXT
            st.success("Loaded sample transcript text.")

    if uploaded:
        save_path = Path("data") / uploaded.name
        save_path.write_bytes(uploaded.read())
        result = extract_transcript_text(save_path)

        if result.success:
            st.session_state.last_transcript_text = result.text

            # Auto-detect institution from extracted text, then header OCR fallback.
            detected, conf = detect_institution(result.text)
            if not detected:
                header_text = extract_header_text_via_ocr(save_path)
                detected, conf = detect_institution(header_text)
                if detected:
                    conf = max(conf, 0.65)
            if detected and (not st.session_state.institution_name or conf >= st.session_state.institution_conf):
                st.session_state.institution_name = detected
                st.session_state.institution_conf = conf

            st.success(f"Extracted text via {result.method} ({result.page_count} pages).")
            if result.warnings:
                st.warning("\n".join(result.warnings[:5]))
        else:
            st.error(result.error or "Failed to extract transcript")

    if st.session_state.institution_name:
        st.success(f"Detected institution: {st.session_state.institution_name}")
        if st.session_state.institution_conf > 0:
            st.caption(f"Institution detection confidence: {st.session_state.institution_conf:.0%}")

    text = st.text_area("Transcript text", value=st.session_state.last_transcript_text, height=250)
    replace_existing = st.checkbox("Use only this transcript's units (clear previous imported units)", value=True)

    if st.button("Parse and save external units"):
        units = parse_external_units_from_text(text)
        if not units:
            st.error("No unit lines detected. Ensure lines look like CODE123 Unit Title")
        else:
            for u in units:
                if institution and not u.get("institution"):
                    u["institution"] = institution

            missing_institution = [u["unit_code"] for u in units if not (u.get("institution") or "").strip()]
            missing_grade = [u["unit_code"] for u in units if not (u.get("grade") or "").strip()]

            # Institution is optional; grade remains required.
            if missing_grade:
                st.error("Missing required transcript data. Grade is required before saving.")
                st.warning(f"Missing grade for units: {', '.join(missing_grade)}")
                if missing_institution:
                    st.info(f"Institution is optional. Missing for units: {', '.join(missing_institution)}")
                st.dataframe(pd.DataFrame(units), width='stretch')
            else:
                if missing_institution:
                    st.info(f"Institution is optional. Missing for units: {', '.join(missing_institution)}")
                if replace_existing:
                    clear_suggestions()
                    clear_external_units()
                ids = insert_external_units(units)
                st.session_state.current_external_ids = ids
                st.success(f"Saved {len(units)} external units from current transcript.")
                st.dataframe(pd.DataFrame(units), width='stretch')

elif page == "CPL Suggestions":
    st.header("2) CPL Suggestions")
    st.caption("Generate suggested SHEA matches for imported external units.")

    external_all = rows_to_dicts(fetch_external_units())
    use_all = st.checkbox("Use all historical external units", value=False)
    if use_all or not st.session_state.current_external_ids:
        external = external_all
    else:
        idset = set(st.session_state.current_external_ids)
        external = [u for u in external_all if int(u.get("id", 0)) in idset]

    shea = rows_to_dicts(fetch_shea_units())

    st.write(f"External units loaded: **{len(external)}**")
    st.write(f"SHEA units loaded: **{len(shea)}**")

    # University URL registry used to improve candidate URL resolution.
    registry = load_registry()
    known_names = sorted(registry.keys())
    selected_name = st.selectbox("University/Institute (for MCP enrichment)", options=[""] + known_names)

    selected_url = ""
    selected_qualification = ""
    if selected_name:
        selected_entry = registry.get(selected_name, "")
        if isinstance(selected_entry, dict):
            selected_qualification = st.selectbox(
                "Qualification level",
                options=["bachelor", "master"],
                help="Choose the qualification to apply the correct institution URL.",
            )
            selected_url = str(selected_entry.get(selected_qualification, "")).strip()
            if selected_url:
                st.caption(f"Using {selected_qualification.title()} URL: {selected_url}")
            else:
                st.warning(f"No URL configured for {selected_qualification} under {selected_name}.")
        else:
            selected_url = str(selected_entry or "").strip()
            if selected_url:
                st.caption(f"Using registry URL: {selected_url}")

    manual_url = st.text_input(
        "Or paste external course URL directly",
        value="",
        placeholder="https://...",
        help="If provided, this URL takes priority over registry URL and MCP agent will browse it like a user.",
    ).strip()
    if manual_url.startswith("http"):
        selected_url = manual_url.rstrip("/")
        st.caption(f"Using manual URL: {selected_url}")

    c_reg1, c_reg2 = st.columns([2, 1])
    with c_reg1:
        new_name = st.text_input("Add new university/institute name", value="")
        new_url = st.text_input("Add new university/institute base URL", value="", placeholder="https://example.edu.au")
    with c_reg2:
        if st.button("Save university URL"):
            if new_name.strip() and new_url.strip().startswith("http"):
                registry[new_name.strip()] = new_url.strip().rstrip("/")
                save_registry(registry)
                st.success("Saved to university registry JSON.")
            else:
                st.error("Enter a valid name and URL (http/https).")

    st.markdown("#### MCP agent course/unit checker (external website)")
    c_agent1, c_agent2 = st.columns(2)
    with c_agent1:
        agent_workers = st.slider("Agent workers", min_value=1, max_value=12, value=6)
    with c_agent2:
        request_timeout_seconds = st.slider("Per-page timeout (sec)", min_value=4, max_value=30, value=8)

    if selected_url and st.button("Run MCP check: crawl external course website"):
        if not external:
            st.error("No external units found. Upload/parse transcript first.")
        else:
            with st.spinner("MCP agent is browsing external unit pages and extracting with reasoning..."):
                course_summary = retrieval_agent.harvest_course_page_summary(
                    selected_url,
                    request_timeout_seconds=request_timeout_seconds,
                )
                harvested = {}

                def _enrich_one(unit: dict):
                    code = str(unit.get("unit_code") or "").upper()
                    title = str(unit.get("title") or "")
                    if not code:
                        return "", None
                    res = retrieval_agent.enrich_external_unit(
                        unit_code=code,
                        title=title,
                        institution=str(selected_name or unit.get("institution") or ""),
                        university_url=selected_url,
                        request_timeout_seconds=request_timeout_seconds,
                    )
                    if res and res.retrieval_confidence > 0 and (res.description or res.learning_outcomes or res.topics):
                        return code, {
                            "title": title,
                            "description": res.description,
                            "learning_outcomes": res.learning_outcomes,
                            "topics": res.topics,
                            "source_url": res.source_url,
                            "retrieval_mode": res.retrieval_mode,
                            "retrieval_confidence": res.retrieval_confidence,
                        }
                    return code, None

                max_parallel = max(1, min(agent_workers, len(external)))
                with ThreadPoolExecutor(max_workers=max_parallel) as ex:
                    futures = [ex.submit(_enrich_one, unit) for unit in external]
                    for f in as_completed(futures):
                        try:
                            code, payload = f.result()
                            if code and payload:
                                harvested[code] = payload
                        except Exception:
                            continue

                # SHEA crawling removed: use locally loaded SHEA dataset from DB.

            updated = 0
            dashboard_rows = []
            for unit in external:
                code = str(unit.get("unit_code") or "").upper()
                payload = harvested.get(code, {})
                shea_payload = next((s for s in shea if str(s.get("unit_code") or "").upper() == code), {})

                if payload:
                    update_external_unit_enrichment(
                        int(unit["id"]),
                        {
                            "description": payload.get("description"),
                            "learning_outcomes": payload.get("learning_outcomes"),
                            "topics": payload.get("topics"),
                            "source_url": payload.get("source_url"),
                            "retrieval_mode": payload.get("retrieval_mode") or "mcp_user_agent",
                            "retrieval_confidence": payload.get("retrieval_confidence") or 0.75,
                        },
                    )
                    updated += 1

                dashboard_rows.append(
                    {
                        "unit_code": code,
                        "transcript_title": unit.get("title", ""),
                        "institution_description": payload.get("description", ""),
                        "institution_learning_outcomes": payload.get("learning_outcomes", ""),
                        "institution_unit_url": payload.get("source_url", ""),
                        "shea_description": shea_payload.get("description", ""),
                        "shea_learning_outcomes": shea_payload.get("learning_outcomes", ""),
                        "shea_unit_url": shea_payload.get("source_url", ""),
                    }
                )

            st.session_state["course_import_preview"] = dashboard_rows
            st.session_state["course_page_summary"] = course_summary
            st.success(
                f"Updated {updated} external units from institution pages. "
                f"Joined against local SHEA dataset for {len([r for r in dashboard_rows if r.get('shea_description') or r.get('shea_learning_outcomes')])} units."
            )
            external = rows_to_dicts(fetch_external_units())

    course_summary = st.session_state.get("course_page_summary", {})
    if course_summary:
        st.subheader("Course page details")
        st.markdown(f"**Course URL:** {course_summary.get('course_url','')}")
        if course_summary.get("overview"):
            st.markdown("**Overview**")
            st.write(course_summary.get("overview"))
        if course_summary.get("learning_outcomes"):
            st.markdown("**Learning outcomes**")
            st.write(course_summary.get("learning_outcomes"))
        if course_summary.get("course_structure"):
            st.markdown("**Course structure**")
            st.write(course_summary.get("course_structure"))
        if course_summary.get("careers"):
            st.markdown("**Careers**")
            st.write(course_summary.get("careers"))

    preview = st.session_state.get("course_import_preview", [])
    if preview:
        st.subheader("Dashboard: Institution vs SHEA (same qualification)")
        st.dataframe(pd.DataFrame(preview), width='stretch')

    with st.expander("External unit data (post-retrieval)", expanded=False):
        if external:
            show_cols = [
                "id",
                "institution",
                "unit_code",
                "title",
                "retrieval_mode",
                "retrieval_confidence",
                "source_url",
            ]
            st.dataframe(pd.DataFrame(external)[show_cols], width='stretch')

    top_k = st.slider("Suggestions per external unit", min_value=1, max_value=3, value=1)

    if st.button("Generate suggestions"):
        if not external:
            st.error("No external units found. Upload/parse transcript first.")
        else:
            shea_missing_course = [u for u in shea if not (u.get("course") or "").strip()]
            if shea_missing_course:
                st.error("SHEA local unit data is required. Click 'Load SHEA units from local Excel' first.")
            else:
                # Level-gated matching: compare external units only against same SHEA course level.
                # AQF 9+ -> MIT, AQF <=8 -> BIT. If missing AQF, keep both and mark in explanation.
                rows = []
                for ext in external:
                    aqf_raw = str(ext.get("aqf_level") or "").strip()
                    target_course = None
                    gate_source = "none"
                    try:
                        aqf_num = float(aqf_raw) if aqf_raw else 0.0
                        if aqf_num >= 9:
                            target_course = "MIT"
                            gate_source = "aqf"
                        elif aqf_num > 0:
                            target_course = "BIT"
                            gate_source = "aqf"
                    except Exception:
                        target_course = None

                    # Fallback: infer from qualification keywords when AQF missing.
                    if not target_course:
                        context_text = " ".join(
                            [
                                str(ext.get("title") or ""),
                                str(ext.get("description") or ""),
                                str(ext.get("learning_outcomes") or ""),
                                str(ext.get("topics") or ""),
                            ]
                        ).lower()
                        if any(k in context_text for k in ["master", "postgraduate", "graduate diploma"]):
                            target_course = "MIT"
                            gate_source = "keyword"
                        elif any(k in context_text for k in ["bachelor", "undergraduate"]):
                            target_course = "BIT"
                            gate_source = "keyword"

                    shea_pool = shea
                    if target_course:
                        filtered = [s for s in shea if str(s.get("course") or "").upper() == target_course]
                        if filtered:
                            shea_pool = filtered

                    unit_results = generate_matches([ext], shea_pool, top_k=top_k)
                    for r in unit_results:
                        rows.append(
                            {
                                "external_unit_id": ext["id"],
                                "shea_unit_id": shea_pool[r.shea_idx]["id"],
                                "score": r.score,
                                "confidence_band": r.confidence_band,
                                "explanation": (
                                    (f"Level gate={target_course} via {gate_source}. " if target_course else "Level gate=not-detected. ")
                                    + r.explanation
                                ),
                                "name_sim": r.name_sim,
                                "desc_sim": r.desc_sim,
                                "outcomes_sim": r.outcomes_sim,
                                "credit_sim": r.credit_sim,
                                "grade_bonus": r.grade_bonus,
                                "retrieval_bonus": r.retrieval_bonus,
                            }
                        )

                clear_suggestions()
                insert_suggestions(rows)
                st.success(f"Generated {len(rows)} suggestions with level-gated course filtering.")

    sug_rows = [dict(r) for r in fetch_suggestions()]
    if sug_rows:
        st.dataframe(pd.DataFrame(sug_rows), width='stretch')

        c1, c2, c3 = st.columns(3)
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        with c1:
            if st.button("Export CSV"):
                out = export_rows_to_csv(sug_rows, Path("exports") / f"cpl_suggestions_{ts}.csv")
                st.success(f"Exported: {out}")
        with c2:
            if st.button("Export Excel"):
                out = export_rows_to_excel(sug_rows, Path("exports") / f"cpl_suggestions_{ts}.xlsx")
                st.success(f"Exported: {out}")
        with c3:
            if st.button("Export PDF"):
                out = export_rows_to_pdf(sug_rows, Path("exports") / f"cpl_suggestions_{ts}.pdf")
                st.success(f"Exported: {out}")

elif page == "Review & Approval":
    st.header("3) Review & Approval")

    sug_rows = [dict(r) for r in fetch_suggestions()]
    if not sug_rows:
        st.info("No suggestions yet. Generate suggestions first.")
    else:
        df = pd.DataFrame(sug_rows)
        st.dataframe(df, width='stretch')

        st.subheader("Record decision")
        suggestion_id = st.selectbox("Suggestion ID", options=df["suggestion_id"].tolist())
        status = st.selectbox("Decision", options=["approved", "rejected", "needs_review", "override"])
        shea_units = rows_to_dicts(fetch_shea_units())
        override_options = {f"{u['unit_code']} — {u['title']}": u["id"] for u in shea_units}
        override_label = st.selectbox("Override to SHEA unit (only if Decision=override)", options=[""] + list(override_options.keys()))
        reviewer = st.text_input("Reviewer", value="MVP Reviewer")
        notes = st.text_area("Notes", value="")

        if st.button("Save decision"):
            override_id = override_options.get(override_label) if status == "override" and override_label else None
            upsert_decision(
                int(suggestion_id),
                status=status,
                reviewer=reviewer,
                notes=notes,
                override_shea_unit_id=override_id,
            )
            st.success("Decision saved.")
