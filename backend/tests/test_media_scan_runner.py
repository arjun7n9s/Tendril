"""End-to-end mock media-scan pipeline tests.

Drives the durable runner synchronously (no BackgroundTask race) and asserts
the full vertical slice: discovery, ranking, CAS resolution, transcription,
PII scrubbing, conversation extraction, memory, scoring, and notifications.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.db import get_sessionmaker
from app.jobs.media_scan_runner import run_media_scan
from app.models.conversation_signal import ConversationSignal
from app.models.enums import MediaScanStage, PrivacyStatus, TranscriptionStatus
from app.models.media_asset import MediaAsset
from app.models.media_scan_job import MediaScanJob
from app.models.notification import Notification


@pytest.fixture
def seeded_account(client: TestClient, seed_csv_path: Path) -> str:
    with seed_csv_path.open("rb") as f:
        r = client.post(
            "/api/v1/import/seed",
            files={"file": ("seed_demo.csv", f, "text/csv")},
        )
    assert r.status_code == 200, r.text
    body = client.get("/api/v1/accounts", params={"search": "ramp"}).json()
    return body["items"][0]["id"]


def test_full_mock_media_scan(client: TestClient, seeded_account: str) -> None:
    create = client.post(
        f"/api/v1/accounts/{seeded_account}/media-scans",
        json={"mode": "mock", "max_sources": 3},
    )
    assert create.status_code == 201, create.text
    scan_id = create.json()["media_scan_id"]

    # Drive the runner directly so assertions don't race the BackgroundTask.
    run_media_scan(scan_id)

    status = client.get(f"/api/v1/media-scans/{scan_id}").json()
    assert status["status"] == "completed"
    assert status["progress_percent"] == 100
    counts = status["counts"]
    assert counts["sources_discovered"] >= 3
    assert counts["sources_selected"] >= 1
    assert counts["transcripts"] >= 1
    assert counts["conversation_signals"] >= 2
    assert counts["memory_writes"] >= 1

    # Conversation signals carry timestamped, evidence-backed quotes.
    sigs = client.get(
        f"/api/v1/accounts/{seeded_account}/conversation-signals"
    ).json()
    assert sigs["total"] >= 2
    first = sigs["items"][0]
    assert first["source_url"]
    assert first["quote_text"]
    assert first["quote_start_seconds"] is not None
    assert first["speaker_label"]

    # Media sources are listable.
    sources = client.get(f"/api/v1/accounts/{seeded_account}/media-sources").json()
    assert len(sources) >= 1
    assert any(s["status"] in ("transcribed", "extracted", "resolved") for s in sources)

    # A completion notification was created.
    notifs = client.get("/api/v1/notifications").json()
    assert notifs["total"] >= 1
    assert any(n["notification_type"] == "media_scan_completed" for n in notifs["items"])


def test_media_scan_events_ordered_and_staged(
    client: TestClient, seeded_account: str
) -> None:
    create = client.post(
        f"/api/v1/accounts/{seeded_account}/media-scans",
        json={"mode": "mock"},
    )
    scan_id = create.json()["media_scan_id"]
    run_media_scan(scan_id)

    events = client.get(f"/api/v1/media-scans/{scan_id}/events").json()
    items = events["items"]
    assert items, "expected media scan events"
    seqs = [e["sequence"] for e in items]
    assert seqs == sorted(seqs)
    assert seqs[0] == 1

    started_stages = [e["stage"] for e in items if e["event_type"] == "stage_started"]
    for expected in ("discover_sources", "rank_sources", "transcribe", "extract_signals"):
        assert expected in started_stages

    # No credential-shaped strings leak into the trace.
    flat = repr(events)
    assert "Bearer " not in flat


def test_transcript_endpoint_returns_scrubbed_only(
    client: TestClient, seeded_account: str
) -> None:
    create = client.post(
        f"/api/v1/accounts/{seeded_account}/media-scans",
        json={"mode": "mock"},
    )
    scan_id = create.json()["media_scan_id"]
    run_media_scan(scan_id)

    sigs = client.get(
        f"/api/v1/accounts/{seeded_account}/conversation-signals"
    ).json()["items"]
    transcript_ids = {s["transcript_id"] for s in sigs if s["transcript_id"]}
    assert transcript_ids

    tid = next(iter(transcript_ids))
    transcript = client.get(f"/api/v1/transcripts/{tid}").json()
    # The eng-podcast fixture contains an email; scrubbing must redact it and
    # the API must never expose raw_text.
    assert "raw_text" not in transcript
    assert transcript["pii_status"] in ("scrubbed", "clean", "sensitive_blocked")
    blob = (transcript.get("scrubbed_text") or "") + repr(transcript.get("segments_json"))
    assert "engineer@example.com" not in blob


def test_cas_dedup_reuses_transcript(client: TestClient, seeded_account: str) -> None:
    """A second scan reuses cached transcripts instead of re-transcribing."""
    first = client.post(
        f"/api/v1/accounts/{seeded_account}/media-scans", json={"mode": "mock"}
    ).json()["media_scan_id"]
    run_media_scan(first)

    SessionLocal = get_sessionmaker()
    with SessionLocal() as db:
        assets_after_first = db.query(MediaAsset).count()
        transcripts_after_first = db.query(MediaAsset).filter(
            MediaAsset.transcript_id.isnot(None)
        ).count()

    second = client.post(
        f"/api/v1/accounts/{seeded_account}/media-scans", json={"mode": "mock"}
    ).json()["media_scan_id"]
    run_media_scan(second)

    with SessionLocal() as db:
        assets_after_second = db.query(MediaAsset).count()
        reused = db.query(MediaAsset).filter(
            MediaAsset.transcription_status == TranscriptionStatus.reused
        ).count()

    # No new assets created for the same media (CAS), and reuse happened.
    assert assets_after_second == assets_after_first
    assert transcripts_after_first >= 1
    assert reused >= 1

    second_status = client.get(f"/api/v1/media-scans/{second}").json()
    assert second_status["counts"]["cache_hits"] >= 1


def test_resume_from_failed_stage(
    client: TestClient, seeded_account: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A job that fails mid-pipeline resumes from its last completed stage."""
    # Disable the create-time BackgroundTask so we drive the runner manually
    # and control exactly when (and how) the first attempt runs.
    import app.api.media_scans as media_api

    monkeypatch.setattr(media_api, "run_media_scan", lambda job_id: None)

    create = client.post(
        f"/api/v1/accounts/{seeded_account}/media-scans", json={"mode": "mock"}
    ).json()
    scan_id = create["media_scan_id"]

    # Force a failure during transcription on the first attempt.
    import app.jobs.media_scan_runner as runner

    original = runner.transcribe_source

    def boom(*args, **kwargs):
        raise RuntimeError("simulated transcription outage")

    monkeypatch.setattr(runner, "transcribe_source", boom)
    run_media_scan(scan_id)

    failed = client.get(f"/api/v1/media-scans/{scan_id}").json()
    assert failed["status"] == "failed"
    # Discovery + ranking completed and are recorded for resume.
    assert failed["stage_state_json"].get("discover_sources", {}).get("done") is True
    assert failed["stage_state_json"].get("rank_sources", {}).get("done") is True
    assert failed["stage_state_json"].get("transcribe", {}).get("done") is not True

    # Restore the real stage and resume (resume endpoint's BackgroundTask is
    # also a no-op, so drive the runner manually after it resets the job).
    monkeypatch.setattr(runner, "transcribe_source", original)
    resume = client.post(f"/api/v1/media-scans/{scan_id}/resume")
    assert resume.status_code == 200
    run_media_scan(scan_id)

    done = client.get(f"/api/v1/media-scans/{scan_id}").json()
    assert done["status"] == "completed"
    assert done["counts"]["conversation_signals"] >= 1


def test_live_media_scan_coerced_to_mock_when_mock_mode(
    client: TestClient, seeded_account: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SIGNALGRAPH_MOCK_MODE", "true")
    from app.config import get_settings

    get_settings.cache_clear()

    create = client.post(
        f"/api/v1/accounts/{seeded_account}/media-scans", json={"mode": "live"}
    )
    assert create.status_code == 201
    assert create.json()["mode"] == "mock"
