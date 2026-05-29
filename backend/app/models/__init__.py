"""SQLAlchemy ORM models for SignalGraph.

Importing this package registers all model classes on `db.Base.metadata`,
so a single `Base.metadata.create_all(...)` will create every table.
"""

from app.models.account import Account
from app.models.brief import Brief
from app.models.conversation_signal import ConversationSignal
from app.models.evidence import EvidenceDocument
from app.models.icp import ICPProfile
from app.models.account_watch import AccountWatch
from app.models.media_asset import MediaAsset
from app.models.media_scan_event import MediaScanEvent
from app.models.media_scan_job import MediaScanJob
from app.models.media_source import MediaSource
from app.models.notification import Notification
from app.models.outreach import OutreachDraft
from app.models.person import Person
from app.models.scan import Scan
from app.models.scan_event import ScanEvent
from app.models.score import Score
from app.models.signal import Signal
from app.models.source import Source
from app.models.transcript import Transcript

__all__ = [
    "Account",
    "Brief",
    "ConversationSignal",
    "EvidenceDocument",
    "ICPProfile",
    "AccountWatch",
    "MediaAsset",
    "MediaScanEvent",
    "MediaScanJob",
    "MediaSource",
    "Notification",
    "OutreachDraft",
    "Person",
    "Scan",
    "ScanEvent",
    "Score",
    "Signal",
    "Source",
    "Transcript",
]
