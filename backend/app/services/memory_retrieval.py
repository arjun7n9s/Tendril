"""Graph-memory recall for briefing.

This is the *read* side of the memory loop. After a scan writes its signals
into the memory layer, the runner recalls the account's accumulated history
(across prior scans and across web + conversation modalities) and turns it
into a compact, citation-friendly `graph_context` block that grounds the
account brief in change-over-time rather than a single run.

Design notes:
- Works with any `MemoryService` (JSONL rollup or Cognee). The JSONL backend
  provides real retrieval from the per-account rollup; Cognee provides graph
  recall with a JSONL fallback. Either way this module only depends on the
  `query()` contract.
- We separate prior observations (from earlier scans) from the current scan's
  packets so the brief can say "this is new" vs "this corroborates history".
- Recurring themes (signal types / keywords seen repeatedly over time) are the
  strongest "why now" evidence, so we surface them explicitly.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from app.logging_setup import get_logger
from app.services.memory_service import MemoryHit, MemoryService

log = get_logger("memory_retrieval")

_MAX_CONTEXT_LINES = 6


@dataclass
class GraphRecall:
    """Result of recalling an account's memory for a scan."""

    hits: list[MemoryHit] = field(default_factory=list)
    prior_hits: list[MemoryHit] = field(default_factory=list)
    recurring_themes: list[str] = field(default_factory=list)
    modalities: list[str] = field(default_factory=list)
    context_text: str = "(empty)"

    @property
    def total(self) -> int:
        return len(self.hits)

    @property
    def prior_count(self) -> int:
        return len(self.prior_hits)


def _build_question(account_name: str, signal_titles: list[str]) -> str:
    """Compose a retrieval question from the account and its fresh signals."""
    head = f"{account_name} buying signals timing migration hiring funding"
    if signal_titles:
        head = f"{head} {' '.join(signal_titles[:4])}"
    return head


def recall_account_memory(
    memory: MemoryService,
    *,
    account_id: str,
    account_name: str,
    current_signal_titles: list[str] | None = None,
    current_scan_id: str | None = None,
    limit: int = 8,
) -> GraphRecall:
    """Recall an account's memory and shape it into a GraphRecall.

    Never raises: a memory backend problem degrades to an empty recall so the
    briefing phase always proceeds.
    """
    titles = current_signal_titles or []
    question = _build_question(account_name, titles)
    try:
        hits = memory.query(question, limit=limit, account_id=account_id)
    except TypeError:
        # A backend whose query() predates the account_id kwarg.
        try:
            hits = memory.query(question, limit=limit)
        except Exception as exc:
            log.warning("memory_retrieval.query_failed", error=str(exc))
            return GraphRecall()
    except Exception as exc:
        log.warning("memory_retrieval.query_failed", error=str(exc))
        return GraphRecall()

    if not hits:
        return GraphRecall()

    # Split history (earlier scans) from the current run's just-written packets.
    prior_hits: list[MemoryHit] = []
    for h in hits:
        scan_id = h.metadata.get("scan_id") if isinstance(h.metadata, dict) else None
        if current_scan_id and scan_id == current_scan_id:
            continue
        prior_hits.append(h)

    recurring = _recurring_themes(hits)
    modalities = _distinct_modalities(hits)
    context_text = _format_context(
        prior_hits or hits, recurring=recurring, modalities=modalities
    )

    return GraphRecall(
        hits=hits,
        prior_hits=prior_hits,
        recurring_themes=recurring,
        modalities=modalities,
        context_text=context_text,
    )


def _recurring_themes(hits: list[MemoryHit]) -> list[str]:
    """Signal types seen more than once across recalled memory."""
    counter: Counter[str] = Counter()
    for h in hits:
        if not isinstance(h.metadata, dict):
            continue
        stype = h.metadata.get("signal_type")
        if stype and stype not in ("None", "other"):
            counter[str(stype)] += 1
    return [theme for theme, count in counter.most_common() if count >= 2]


def _distinct_modalities(hits: list[MemoryHit]) -> list[str]:
    seen: list[str] = []
    for h in hits:
        if not isinstance(h.metadata, dict):
            continue
        modality = h.metadata.get("modality") or "web"
        if modality not in seen:
            seen.append(str(modality))
    return seen


def _format_context(
    hits: list[MemoryHit],
    *,
    recurring: list[str],
    modalities: list[str],
) -> str:
    """Render a compact, model-friendly context block.

    Kept short on purpose: this is grounding, not a data dump, and it must not
    blow the briefing prompt's token budget.
    """
    if not hits:
        return "(empty)"

    lines: list[str] = []
    if recurring:
        lines.append("Recurring themes over time: " + ", ".join(recurring) + ".")
    if len(modalities) > 1:
        lines.append("Evidence spans modalities: " + ", ".join(modalities) + ".")

    lines.append("Prior account memory (most relevant first):")
    for h in hits[:_MAX_CONTEXT_LINES]:
        meta = h.metadata if isinstance(h.metadata, dict) else {}
        observed = meta.get("observed_at") or meta.get("written_at") or ""
        stamp = f" [{observed[:10]}]" if observed else ""
        lines.append(f"- {h.text}{stamp}")
    return "\n".join(lines)
