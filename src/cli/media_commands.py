import logging

import click
from flask import Flask
from flask.cli import with_appcontext

from composition.container_access import get_application_container

_logger = logging.getLogger(__name__)


@click.group("media")
def media_cli() -> None:
    """Run internal media maintenance jobs."""


@media_cli.command("cleanup-orphans")
@with_appcontext
def cleanup_orphans() -> None:
    """Delete old media objects that are not referenced by PostgreSQL."""
    try:
        result = get_application_container().media.cleanup_orphans.execute()
    except Exception as error:
        _logger.exception("Orphaned media cleanup failed")
        raise click.ClickException("Orphaned media cleanup failed") from error

    click.echo(
        "Cleanup completed: "
        f"scanned={result.scanned}, "
        f"eligible={result.eligible}, "
        f"used={result.used}, "
        f"deleted={result.deleted}, "
        f"failed={result.failed}, "
        "expired_reservations_deleted="
        f"{result.expired_reservations_deleted}"
    )

    if result.failed:
        raise click.ClickException(
            f"Failed to delete {result.failed} orphaned media objects"
        )


def register_media_commands(app: Flask) -> None:
    app.cli.add_command(media_cli)
