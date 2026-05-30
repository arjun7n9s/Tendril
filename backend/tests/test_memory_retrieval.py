"""Tests for the memory read loop: retrievable JSONL + graph recall.

Covers the *read* side that closes the Cognee/memory loop:
- JsonlMemoryService accumulates packets per account across scans and
  retrieves them by keyword overlap with recency tie-breaking.
- recall_account_memory shapes hits into a graph_context block, separates
  prior-scan history from the current run, and surfaces recurring themes.
"""

from __future__ import annotations

from pathlib import Path

from app.services.memory_retrieval import recall_account_memory
from app.services.memory_service import JsonlMemoryService, MemoryPacket


def _packet(
    *,
    scan_id: str,
    account_id: str = "acc_a",
    title: str,
    body: str,
    signal_type: str = "hiring",
    modality: str = "web",
    observed_at: str | None = None,
) -> MemoryPacket:
    return MemoryPacket(
        scan_id=scan_id,
        account_id=account_id,
        dataset="signalgraph_signals",
        title=title,
        body=body,
        fact=body,
        observed_at=observed_at,
        metadata={"signal_type": signal_type, "modality": modality},
    )


def test_query_returns_empty_without_account_id(tmp_path: Path) -> None:
    svc = JsonlMemoryService(tmp_path)
    svc.remember(_packet(scan_id="s1", title="Hiring", body="Kafka roles"))
    # Back-compat: no account scope means no rollup search.
    assert svc.query("kafka") == []


def test_query_retrieves_by_keyword_overlap(tmp_path: Path) -> None:
    svc = JsonlMemoryService(tmp_path)
    svc.remember(
        _packet(scan_id="s1", title="Hiring data engineers", body="Kafka and Snowflake roles")
    )
    svc.remember(
        _packet(scan_id="s1", title="Office lease", body="Signed a new office lease downtown")
    )

    hits = svc.query("snowflake migration", account_id="acc_a")
    assert hits, "expected at least one keyword hit"
    # The Kafka/Snowflake packet must rank first.
    assert "Snowflake" in hits[0].text or "snowflake" in hits[0].text.lower()


def test_rollup_accumulates_across_scans(tmp_path: Path) -> None:
    svc = JsonlMemoryService(tmp_path)
    svc.remember(_packet(scan_id="s1", title="Hiring", body="Kafka roles posted"))
    svc.remember(_packet(scan_id="s2", title="Migration", body="Snowflake migration blog"))

    account_file = tmp_path / "account_acc_a.jsonl"
    assert account_file.exists()
    lines = account_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2

    # A broad query returns packets from both scans.
    hits = svc.query("kafka snowflake", account_id="acc_a")
    scan_ids = {h.metadata.get("scan_id") for h in hits}
    assert {"s1", "s2"} <= scan_ids


def test_recall_separates_prior_history_and_surfaces_themes(tmp_path: Path) -> None:
    svc = JsonlMemoryService(tmp_path)
    # Two prior scans both showing hiring -> recurring theme.
    svc.remember(_packet(scan_id="s1", title="Hiring round 1", body="Kafka roles", signal_type="hiring"))
    svc.remember(_packet(scan_id="s2", title="Hiring round 2", body="Snowflake roles", signal_type="hiring"))
    # Current scan packet.
    svc.remember(_packet(scan_id="s3", title="New migration", body="Migrating to Snowflake", signal_type="migration"))

    recall = recall_account_memory(
        svc,
        account_id="acc_a",
        account_name="Acme",
        current_signal_titles=["New migration"],
        current_scan_id="s3",
    )

    assert recall.total >= 3
    # Prior hits exclude the current scan's packet.
    assert all(h.metadata.get("scan_id") != "s3" for h in recall.prior_hits)
    assert recall.prior_count >= 2
    # "hiring" appeared twice -> recurring theme.
    assert "hiring" in recall.recurring_themes
    assert recall.context_text != "(empty)"
    assert "Recurring themes" in recall.context_text


def test_recall_spans_modalities(tmp_path: Path) -> None:
    svc = JsonlMemoryService(tmp_path)
    svc.remember(_packet(scan_id="s1", title="Web hiring", body="Kafka roles", modality="web"))
    svc.remember(
        _packet(
            scan_id="s2",
            title="Podcast quote",
            body="CTO discusses Snowflake migration timeline",
            modality="conversation",
            signal_type="migration",
        )
    )

    recall = recall_account_memory(
        svc,
        account_id="acc_a",
        account_name="Acme",
        current_signal_titles=["Kafka roles"],
    )
    assert set(recall.modalities) >= {"web", "conversation"}


def test_recall_empty_for_unknown_account(tmp_path: Path) -> None:
    svc = JsonlMemoryService(tmp_path)
    recall = recall_account_memory(
        svc, account_id="ghost", account_name="Ghost Co"
    )
    assert recall.total == 0
    assert recall.context_text == "(empty)"
