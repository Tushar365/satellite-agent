"""Tests for src.db — model definitions and table metadata."""

import uuid

import pytest


@pytest.fixture(autouse=True)
def _env_defaults(monkeypatch):
    """Ensure required env vars are set."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-key-1234")
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-test-key-1234")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@localhost/testdb")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    from src.config import get_settings
    get_settings.cache_clear()


def test_all_tables_registered():
    """All expected tables are present in Base.metadata."""
    from src.db.session import Base
    import src.db.models  # noqa: F401

    table_names = set(Base.metadata.tables.keys())
    expected = {"search_requests", "scenes", "quality_checks", "downloads", "agent_runs"}
    assert expected.issubset(table_names), f"Missing tables: {expected - table_names}"


def test_search_request_columns():
    """SearchRequest has the expected columns."""
    from src.db.models import SearchRequest

    mapper = SearchRequest.__table__
    col_names = {c.name for c in mapper.columns}
    for expected in ("id", "natural_query", "aoi", "status", "created_at", "updated_at"):
        assert expected in col_names, f"Missing column: {expected}"


def test_scene_foreign_key():
    """Scene.search_id references search_requests.id."""
    from src.db.models import Scene

    fk = list(Scene.__table__.c.search_id.foreign_keys)
    assert len(fk) == 1
    assert fk[0].target_fullname == "search_requests.id"


def test_quality_check_foreign_key():
    """QualityCheck.scene_id references scenes.id."""
    from src.db.models import QualityCheck

    fk = list(QualityCheck.__table__.c.scene_id.foreign_keys)
    assert len(fk) == 1
    assert fk[0].target_fullname == "scenes.id"


def test_download_foreign_key():
    """Download.scene_id references scenes.id."""
    from src.db.models import Download

    fk = list(Download.__table__.c.scene_id.foreign_keys)
    assert len(fk) == 1
    assert fk[0].target_fullname == "scenes.id"


def test_agent_run_foreign_key():
    """AgentRun.search_id references search_requests.id."""
    from src.db.models import AgentRun

    fk = list(AgentRun.__table__.c.search_id.foreign_keys)
    assert len(fk) == 1
    assert fk[0].target_fullname == "search_requests.id"


def test_enum_values():
    """Status enums have the expected members."""
    from src.db.models import SearchStatus, QualityVerdict, DownloadStatus, RunStatus

    assert set(SearchStatus) == {
        SearchStatus.pending, SearchStatus.running,
        SearchStatus.completed, SearchStatus.failed,
    }
    assert set(QualityVerdict) == {QualityVerdict.passed, QualityVerdict.failed}
    assert set(DownloadStatus) == {
        DownloadStatus.queued, DownloadStatus.downloading,
        DownloadStatus.completed, DownloadStatus.failed,
    }
    assert set(RunStatus) == {
        RunStatus.pending, RunStatus.running,
        RunStatus.completed, RunStatus.failed,
    }


def test_db_package_reexports():
    """src.db.__init__ re-exports all key symbols."""
    from src.db import (
        Base, AsyncSessionLocal, async_engine, get_session,
        AgentRun, Download, QualityCheck, Scene, SearchRequest,
    )
    assert Base is not None
    assert AsyncSessionLocal is not None
