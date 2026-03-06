"""All database tables for the satellite-agent."""

import enum
import uuid
from datetime import datetime

from geoalchemy2 import Geometry
from sqlalchemy import (
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.session import Base


# ── Enums ──────────────────────────────────────────────────────────────


class SearchStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class QualityVerdict(str, enum.Enum):
    passed = "passed"
    failed = "failed"


class DownloadStatus(str, enum.Enum):
    queued = "queued"
    downloading = "downloading"
    completed = "completed"
    failed = "failed"


class RunStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


# ── Mixin ──────────────────────────────────────────────────────────────


class TimestampMixin:
    """Adds created_at / updated_at to every model."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


# ── Tables ─────────────────────────────────────────────────────────────


class SearchRequest(TimestampMixin, Base):
    """A user query for satellite imagery."""

    __tablename__ = "search_requests"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    natural_query: Mapped[str] = mapped_column(Text, nullable=False)
    aoi = mapped_column(Geometry("POLYGON", srid=4326), nullable=True)
    date_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    date_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cloud_cover_max: Mapped[int | None] = mapped_column(Integer)
    constraints: Mapped[dict | None] = mapped_column(JSONB)
    status: Mapped[SearchStatus] = mapped_column(
        Enum(SearchStatus), default=SearchStatus.pending
    )

    # relationships
    scenes: Mapped[list["Scene"]] = relationship(back_populates="search_request")
    agent_runs: Mapped[list["AgentRun"]] = relationship(back_populates="search_request")


class Scene(TimestampMixin, Base):
    """A candidate satellite scene returned from a STAC catalog."""

    __tablename__ = "scenes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    search_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("search_requests.id"), nullable=False
    )
    scene_id: Mapped[str] = mapped_column(String(256), nullable=False)
    platform: Mapped[str] = mapped_column(String(64))
    collection: Mapped[str] = mapped_column(String(128))
    datetime_acquired: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cloud_cover: Mapped[float | None] = mapped_column(Float)
    geometry = mapped_column(Geometry("POLYGON", srid=4326), nullable=True)
    stac_properties: Mapped[dict | None] = mapped_column(JSONB)
    asset_urls: Mapped[dict | None] = mapped_column(JSONB)

    # relationships
    search_request: Mapped["SearchRequest"] = relationship(back_populates="scenes")
    quality_checks: Mapped[list["QualityCheck"]] = relationship(
        back_populates="scene"
    )
    downloads: Mapped[list["Download"]] = relationship(back_populates="scene")


class QualityCheck(TimestampMixin, Base):
    """Per-scene quality gate results."""

    __tablename__ = "quality_checks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    scene_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scenes.id"), nullable=False
    )
    cloud_cover_pct: Mapped[float | None] = mapped_column(Float)
    aoi_coverage_pct: Mapped[float | None] = mapped_column(Float)
    nodata_pct: Mapped[float | None] = mapped_column(Float)
    processing_level: Mapped[str | None] = mapped_column(String(16))
    verdict: Mapped[QualityVerdict] = mapped_column(
        Enum(QualityVerdict), default=QualityVerdict.failed
    )
    details: Mapped[dict | None] = mapped_column(JSONB)

    # relationships
    scene: Mapped["Scene"] = relationship(back_populates="quality_checks")


class Download(TimestampMixin, Base):
    """Tracks a COG / asset download."""

    __tablename__ = "downloads"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    scene_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scenes.id"), nullable=False
    )
    asset_key: Mapped[str] = mapped_column(String(64), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    local_path: Mapped[str | None] = mapped_column(Text)
    size_bytes: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[DownloadStatus] = mapped_column(
        Enum(DownloadStatus), default=DownloadStatus.queued
    )

    # relationships
    scene: Mapped["Scene"] = relationship(back_populates="downloads")


class AgentRun(TimestampMixin, Base):
    """Tracks a LangGraph agent execution."""

    __tablename__ = "agent_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    search_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("search_requests.id"), nullable=False
    )
    run_id: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[RunStatus] = mapped_column(
        Enum(RunStatus), default=RunStatus.pending
    )
    graph_state: Mapped[dict | None] = mapped_column(JSONB)
    tokens_used: Mapped[int | None] = mapped_column(Integer)
    error_message: Mapped[str | None] = mapped_column(Text)

    # relationships
    search_request: Mapped["SearchRequest"] = relationship(back_populates="agent_runs")
