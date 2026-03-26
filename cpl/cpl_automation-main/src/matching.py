"""Matching engine for CPL suggestions.

Prefers embedding-based similarity (sentence-transformers) if available,
falls back to TF-IDF cosine similarity.
Author: Sunil Paudel
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from .llm_assist import compare_units_natural_language


@dataclass
class MatchResult:
    external_idx: int
    shea_idx: int
    score: float
    confidence_band: str
    explanation: str
    name_sim: float = 0.0
    desc_sim: float = 0.0
    outcomes_sim: float = 0.0
    credit_sim: float = 0.0
    grade_bonus: float = 0.0
    retrieval_bonus: float = 0.0


def _confidence_band(score: float) -> str:
    # Percentage-style thresholds (easier for reviewers to interpret)
    if score >= 0.70:
        return "High"
    if score >= 0.45:
        return "Medium"
    return "Low"


def _build_text(unit: Dict[str, Any]) -> str:
    return " | ".join(
        [
            str(unit.get("unit_code", "")),
            str(unit.get("title", "")),
            str(unit.get("description", "")),
            str(unit.get("learning_outcomes", "")),
            str(unit.get("topics", "")),
            str(unit.get("keywords", "")),
        ]
    )


def _content_text(unit: Dict[str, Any]) -> str:
    """Best-effort semantic content text (not just title).

    Uses fallbacks so comparison still works when one side has sparse fields.
    """
    return " | ".join(
        [
            str(unit.get("description", "")),
            str(unit.get("learning_outcomes", "")),
            str(unit.get("topics", "")),
            str(unit.get("keywords", "")),
            str(unit.get("title", "")),
        ]
    )


def _compute_similarity(texts_a: List[str], texts_b: List[str]) -> Tuple[List[List[float]], str]:
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore
        from sklearn.metrics.pairwise import cosine_similarity  # type: ignore

        model = SentenceTransformer("all-MiniLM-L6-v2")
        emb_a = model.encode(texts_a)
        emb_b = model.encode(texts_b)
        sim = cosine_similarity(emb_a, emb_b)
        return sim.tolist(), "Embeddings"
    except Exception:
        from sklearn.feature_extraction.text import TfidfVectorizer  # type: ignore
        from sklearn.metrics.pairwise import cosine_similarity  # type: ignore

        vectorizer = TfidfVectorizer(stop_words="english")
        all_texts = texts_a + texts_b
        mat = vectorizer.fit_transform(all_texts)
        mat_a = mat[: len(texts_a)]
        mat_b = mat[len(texts_a) :]
        sim = cosine_similarity(mat_a, mat_b)
        return sim.tolist(), "TF-IDF"


def _safe_num(s: Any) -> float:
    try:
        return float(str(s).strip())
    except Exception:
        return 0.0


def _compat_score(a: Any, b: Any, tolerance: float = 0.0) -> float:
    aa, bb = _safe_num(a), _safe_num(b)
    if not aa or not bb:
        return 0.0
    if abs(aa - bb) <= tolerance:
        return 1.0
    diff_ratio = abs(aa - bb) / max(aa, bb)
    return max(0.0, 1.0 - diff_ratio)


def _token_overlap(a: str, b: str) -> float:
    sa = {t for t in a.lower().split() if len(t) > 2}
    sb = {t for t in b.lower().split() if len(t) > 2}
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def _is_non_passing_grade(grade: Any) -> bool:
    g = str(grade or "").strip().lower()
    return g in {
        "fail", "fl", "f", "n", "nn", "nyc", "not yet competent", "not competent", "unsatisfactory"
    }


def _grade_bonus(grade: Any) -> float:
    g = str(grade or "").strip().lower()
    if g in {"hd", "high distinction"}:
        return 0.10
    if g in {"distinction", "dn", "d"}:
        return 0.07
    if g in {"credit", "cr", "c"}:
        return 0.04
    if g in {"pass", "ps", "p", "competent"}:
        return 0.00
    if _is_non_passing_grade(g):
        return -0.10
    return 0.00


def _explanation(external: Dict[str, Any], shea: Dict[str, Any], final_score: float, method: str, parts: Dict[str, float]) -> str:
    retrieval_mode = external.get('retrieval_mode') or 'transcript-only'
    retrieval_conf = float(external.get('retrieval_confidence') or 0)

    if parts['desc'] < 0.2 and parts['outcomes'] < 0.15:
        reason = "Low confidence because match is mostly name-based and lacks course-content evidence"
    elif parts['outcomes'] >= 0.4:
        reason = "Good content alignment from learning outcomes/topics"
    else:
        reason = "Moderate alignment; check outcomes and AQF/credit manually"

    ai_text = compare_units_natural_language(
        {
            "title": str(external.get("title", "") or ""),
            "description": str(external.get("description", "") or ""),
            "learning_outcomes": str(external.get("learning_outcomes", "") or ""),
        },
        {
            "title": str(shea.get("title", "") or ""),
            "description": str(shea.get("description", "") or ""),
            "learning_outcomes": str(shea.get("learning_outcomes", "") or ""),
        },
        final_score,
    )

    return (
        f"{reason}. Method={method}. Confidence={final_score * 100:.1f}%. "
        f"Components: name {parts['name']:.2f}, description {parts['desc']:.2f}, outcomes {parts['outcomes']:.2f}, "
        f"credit {parts['credit']:.2f}, grade_bonus {parts['grade_bonus']:.2f}. "
        f"Retrieval source: {retrieval_mode} ({retrieval_conf:.2f}). "
        f"{ai_text}"
    )


def generate_matches(external_units: List[Dict[str, Any]], shea_units: List[Dict[str, Any]], top_k: int = 1) -> List[MatchResult]:
    if not external_units or not shea_units:
        return []

    external_texts = [_build_text(u) for u in external_units]
    shea_texts = [_build_text(u) for u in shea_units]
    sim_matrix, method = _compute_similarity(external_texts, shea_texts)

    # extra component similarities
    ext_names = [str(u.get("title", "")) for u in external_units]
    shea_names = [str(u.get("title", "")) for u in shea_units]
    name_sim, _ = _compute_similarity(ext_names, shea_names)

    ext_desc = [_content_text(u) for u in external_units]
    shea_desc = [_content_text(u) for u in shea_units]
    desc_sim, _ = _compute_similarity(ext_desc, shea_desc)

    ext_outcomes = [
        str(u.get("learning_outcomes") or u.get("topics") or u.get("description") or u.get("title") or "")
        for u in external_units
    ]
    shea_outcomes = [
        str(u.get("learning_outcomes") or u.get("topics") or u.get("description") or u.get("title") or "")
        for u in shea_units
    ]
    outcomes_sim, _ = _compute_similarity(ext_outcomes, shea_outcomes)

    results: List[MatchResult] = []

    for ext_idx, row in enumerate(sim_matrix):
        ranked = sorted(enumerate(row), key=lambda x: x[1], reverse=True)[:top_k]
        for shea_idx, _ in ranked:
            outcomes = float(max(0.0, min(1.0, outcomes_sim[ext_idx][shea_idx])))
            credit = _compat_score(external_units[ext_idx].get("credit_points"), shea_units[shea_idx].get("credit_points"), tolerance=2)
            grade_bonus = _grade_bonus(external_units[ext_idx].get("grade"))

            parts = {
                "name": float(max(0.0, min(1.0, name_sim[ext_idx][shea_idx]))),
                "desc": float(max(0.0, min(1.0, desc_sim[ext_idx][shea_idx]))),
                "outcomes": float(max(0.0, min(1.0, outcomes))),
                "credit": float(max(0.0, min(1.0, credit))),
                "grade_bonus": float(grade_bonus),
            }

            score = (
                0.20 * parts["name"]
                + 0.35 * parts["desc"]
                + 0.35 * parts["outcomes"]
                + 0.10 * parts["credit"]
                + parts["grade_bonus"]
            )

            retrieval_conf = float(external_units[ext_idx].get("retrieval_confidence") or 0.0)
            retrieval_bonus = 0.08 * retrieval_conf
            score = min(1.0, score + retrieval_bonus)

            # Guardrail: name-only match can't be high confidence.
            if parts["outcomes"] < 0.15 and parts["desc"] < 0.20:
                score = min(score, 0.58)

            score = float(max(0.0, min(1.0, score)))

            flagged_non_passing = _is_non_passing_grade(external_units[ext_idx].get("grade"))
            if flagged_non_passing:
                score = min(score, 0.20)

            band = "Flagged" if flagged_non_passing else _confidence_band(score)
            explanation = _explanation(external_units[ext_idx], shea_units[shea_idx], score, method, parts)
            if flagged_non_passing:
                explanation = "FLAG: Non-passing/Not Competent grade. Do NOT auto-approve credit. " + explanation

            results.append(
                MatchResult(
                    external_idx=ext_idx,
                    shea_idx=shea_idx,
                    score=score,
                    confidence_band=band,
                    explanation=explanation,
                    name_sim=parts["name"],
                    desc_sim=parts["desc"],
                    outcomes_sim=parts["outcomes"],
                    credit_sim=parts["credit"],
                    grade_bonus=parts["grade_bonus"],
                    retrieval_bonus=retrieval_bonus,
                )
            )

    results.sort(key=lambda r: r.score, reverse=True)
    return results
