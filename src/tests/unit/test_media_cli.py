from types import SimpleNamespace
from unittest.mock import Mock

from flask import Flask

from application.media.cleanup_orphaned_media_use_case import (
    OrphanCleanupResult,
)
from cli.media_commands import register_media_commands
from composition.container_access import APPLICATION_CONTAINER_KEY


def _app(execute: Mock) -> Flask:
    app = Flask(__name__)
    app.extensions[APPLICATION_CONTAINER_KEY] = SimpleNamespace(
        media=SimpleNamespace(cleanup_orphans=SimpleNamespace(execute=execute))
    )
    register_media_commands(app)
    return app


def test_cleanup_orphans_cli_executes_use_case_and_prints_result() -> None:
    execute = Mock(
        return_value=OrphanCleanupResult(
            scanned=10,
            eligible=8,
            used=3,
            deleted=5,
            failed=0,
        )
    )

    result = (
        _app(execute)
        .test_cli_runner()
        .invoke(args=["media", "cleanup-orphans"])
    )

    assert result.exit_code == 0
    execute.assert_called_once_with()
    assert "Cleanup completed" in result.output
    assert "scanned=10" in result.output
    assert "eligible=8" in result.output
    assert "used=3" in result.output
    assert "deleted=5" in result.output
    assert "failed=0" in result.output
    assert "expired_reservations_deleted=0" in result.output


def test_cleanup_orphans_cli_returns_nonzero_when_deletions_failed() -> None:
    execute = Mock(
        return_value=OrphanCleanupResult(
            scanned=10,
            eligible=8,
            used=3,
            deleted=4,
            failed=1,
        )
    )

    result = (
        _app(execute)
        .test_cli_runner()
        .invoke(args=["media", "cleanup-orphans"])
    )

    assert result.exit_code != 0
    execute.assert_called_once_with()
    assert "failed=1" in result.output
    assert "Failed to delete 1 orphaned media objects" in result.output


def test_cleanup_orphans_cli_returns_nonzero_on_fatal_error() -> None:
    execute = Mock(side_effect=RuntimeError("database unavailable"))

    result = (
        _app(execute)
        .test_cli_runner()
        .invoke(args=["media", "cleanup-orphans"])
    )

    assert result.exit_code != 0
    execute.assert_called_once_with()
    assert "Orphaned media cleanup failed" in result.output
