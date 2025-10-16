from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional, Tuple

from .models import Issue
from . import api as jira_api

_WORD_RE = re.compile(r"[A-Za-z0-9]+")


def _normalize_text(s: str) -> str:
    return (s or "").strip().lower()


def _tokenize(s: str) -> List[str]:
    s = _normalize_text(s)
    return [t for t in _WORD_RE.findall(s) if len(t) >= 3]


def _select_tokens(title: str, description: str, max_tokens: int = 10) -> List[str]:
    toks = _tokenize(title) + _tokenize(description)
    # Map each token to its first occurrence index to avoid O(n^2) toks.index calls
    first_idx: Dict[str, int] = {}
    for i, t in enumerate(toks):
        if t not in first_idx:
            first_idx[t] = i
    # Sort unique tokens by length (desc), then first occurrence index (asc)
    sorted_uniq = sorted(first_idx.keys(), key=lambda t: (-len(t), first_idx[t]))
    return sorted_uniq[:max_tokens]


def _jql_quote(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def _maybe_project_filter(project: Optional[str]) -> str:
    return f' AND project = "{_jql_quote(project)}"' if project else ""


def _maybe_status_filter(include_closed: bool) -> str:
    return "" if include_closed else " AND statusCategory != Done"


def _build_phrase_query(phrase: str, project: Optional[str], include_closed: bool) -> str:
    q = f'(summary ~ "{_jql_quote(phrase)}" OR description ~ "{_jql_quote(phrase)}")'
    q += _maybe_project_filter(project) + _maybe_status_filter(include_closed)
    return q


def _build_token_or_query(tokens: List[str], project: Optional[str], include_closed: bool) -> str:
    pieces: List[str] = []
    for t in tokens:
        qt = _jql_quote(t)
        pieces.append(f'summary ~ "{qt}"')
        pieces.append(f'description ~ "{qt}"')
        pieces.append(f'text ~ "{qt}"')
    if not pieces:
        return ""
    q = "(" + " OR ".join(pieces) + ")"
    q += _maybe_project_filter(project) + _maybe_status_filter(include_closed)
    return q


def _build_token_and_query(tokens: List[str], project: Optional[str], include_closed: bool) -> str:
    if len(tokens) < 2:
        return _build_token_or_query(tokens, project, include_closed)
    mid = max(1, len(tokens) // 2)
    a, b = tokens[:mid], tokens[mid:]
    qa = _build_token_or_query(a, None, True)
    qb = _build_token_or_query(b, None, True)
    if not qa or not qb:
        return _build_token_or_query(tokens, project, include_closed)
    q = f"({qa}) AND ({qb})"
    q += _maybe_project_filter(project) + _maybe_status_filter(include_closed)
    return q


def _score_issue(row: Dict[str, Any], phrase: str, tokens: List[str], preferred_project: Optional[str]) -> Tuple[int, List[str]]:
    score = 0
    matched_terms: List[str] = []
    summary_l = _normalize_text(row.get("summary") or "")
    if phrase and phrase.lower() in summary_l:
        score += 3
        matched_terms.append(phrase)
    for t in tokens:
        if t in summary_l:
            score += 2
            matched_terms.append(t)
    if preferred_project and row.get("projectKey") == preferred_project:
        score += 1
    return score, matched_terms


def _extract_issue_row(issue: Dict[str, Any]) -> Dict[str, Any]:
    fields = issue.get("fields", {}) or {}
    status = fields.get("status") or {}
    project = fields.get("project") or {}
    return {
        "key": issue.get("key"),
        "summary": fields.get("summary"),
        "status": (status.get("name") or ""),
        "updated": fields.get("updated"),
        "projectKey": project.get("key"),
    }


def heuristic_find_similar(
    issue_key: Optional[str],
    title: Optional[str],
    description: Optional[str],
    project: Optional[str],
    max_results: int = 20,
    include_closed: bool = True,
    exclude_self: bool = True,
) -> List[Dict[str, Any]]:
    """
    Heuristic related-issue finder using phrase + token passes and ranking.
    Returns a list of rows with keys: key, summary, status, updated, projectKey, score, matchedTerms, sourceQueries
    """
    phrase = ""
    seed_summary = ""
    seed_description = ""
    seed_project = project

    if issue_key:
        st, _, body = jira_api.get_issue(issue_key, fields=["summary", "description", "project"])
        if st == 200:
            try:
                doc = json.loads(body.decode("utf-8"))
            except Exception:
                doc = {}
            f = (doc.get("fields") or {})
            seed_summary = f.get("summary") or ""
            seed_description = f.get("description") or ""
            if not seed_project and isinstance(f.get("project"), dict):
                seed_project = f["project"].get("key") or project

    base_title = (title or seed_summary or "")
    base_desc = (description or seed_description or "")
    phrase = " ".join(_tokenize(base_title)[:8])
    tokens = _select_tokens(base_title, base_desc, max_tokens=10)

    passes: List[Tuple[str, str]] = []
    if phrase:
        passes.append(("phrase", _build_phrase_query(phrase, seed_project, include_closed)))
    if tokens:
        passes.append(("token_or", _build_token_or_query(tokens, seed_project, include_closed)))
        passes.append(("token_and", _build_token_and_query(tokens, seed_project, include_closed)))

    seen: Dict[str, Dict[str, Any]] = {}
    for tag, jql in passes:
        if not jql:
            continue
        for it in jira_api.jql_search_raw(jql, max_results=50, fields=["summary", "status", "updated", "project", "description"]):
            key = it.get("key")
            if not key:
                continue
            if exclude_self and issue_key and key == issue_key:
                continue
            row = _extract_issue_row(it)
            sc, matched = _score_issue(row, phrase, tokens, seed_project)
            prev = seen.get(key)
            if prev:
                prev["score"] = max(prev["score"], sc)
                prev["matchedTerms"] = sorted(list(set(prev["matchedTerms"] + matched)))
                prev["sourceQueries"] = sorted(list(set(prev["sourceQueries"] + [tag])))
            else:
                row["score"] = sc
                row["matchedTerms"] = matched
                row["sourceQueries"] = [tag]
                seen[key] = row

    ranked = sorted(seen.values(), key=lambda r: (r.get("score", 0), r.get("updated") or ""), reverse=True)
    return ranked[:max_results]


# ---------- Optional semantic re-ranking (behind extra) ----------

def _maybe_load_embedder(model_name: str):
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore
    except Exception:
        return None
    try:
        return SentenceTransformer(model_name)
    except Exception:
        return None


def _embed_texts(model, texts: List[str]) -> Optional[List[List[float]]]:
    if model is None:
        return None
    try:
        vecs = model.encode(texts, convert_to_numpy=False, show_progress_bar=False)
        # Normalize to pure python lists for portability
        return [list(map(float, v)) for v in vecs]
    except Exception:
        return None


def _cosine_sim(u: List[float], v: List[float]) -> float:
    import math
    if not u or not v or len(u) != len(v):
        return 0.0
    du = math.sqrt(sum(x * x for x in u))
    dv = math.sqrt(sum(x * x for x in v))
    if du == 0.0 or dv == 0.0:
        return 0.0
    dot = sum(x * y for x, y in zip(u, v))
    return dot / (du * dv)


def semantic_rerank(
    seed_text: str,
    candidates: List[Dict[str, Any]],
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
) -> List[Dict[str, Any]]:
    """
    If the embedding model is available, re-rank by cosine similarity to seed_text.
    On failure/unavailable, return candidates unchanged.
    """
    model = _maybe_load_embedder(model_name)
    if model is None or not candidates or not seed_text:
        return candidates

    texts = [seed_text] + [str(c.get("summary") or "") for c in candidates]
    vecs = _embed_texts(model, texts)
    if not vecs:
        return candidates

    seed_vec = vecs[0]
    cand_vecs = vecs[1:]
    scored = []
    for c, v in zip(candidates, cand_vecs):
        c2 = dict(c)
        c2["semanticScore"] = _cosine_sim(seed_vec, v)
        scored.append(c2)

    scored.sort(key=lambda r: (r.get("semanticScore", 0.0), r.get("score", 0)), reverse=True)
    return scored


def find_similar(
    issue_key: Optional[str] = None,
    title: Optional[str] = None,
    description: Optional[str] = None,
    project: Optional[str] = None,
    max_results: int = 20,
    include_closed: bool = True,
    exclude_self: bool = True,
    mode: str = "heuristic",  # heuristic | semantic | hybrid
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
) -> List[Dict[str, Any]]:
    """
    Public API: find related Jira issues.
    mode:
      - heuristic: ranking purely by token/phrase + project bonus
      - semantic: if model available, use semantic re-ranking only; else fallback to heuristic
      - hybrid: run heuristic, then re-rank by semanticScore if available
    """
    base = heuristic_find_similar(
        issue_key=issue_key,
        title=title,
        description=description,
        project=project,
        max_results=max_results,
        include_closed=include_closed,
        exclude_self=exclude_self,
    )
    seed_text = (title or (description or "")) if (title or description) else (base[0]["summary"] if base else "")
    if mode == "heuristic":
        return base
    if mode == "semantic":
        reranked = semantic_rerank(seed_text, base, model_name=model_name)
        return reranked
    if mode == "hybrid":
        reranked = semantic_rerank(seed_text, base, model_name=model_name)
        return reranked
    # Unknown mode → default heuristic
    return base
