"""Генерация и применение миграций через Alembic autogenerate."""

from __future__ import annotations

import logging

from alembic.autogenerate import produce_migrations, render_python_code
from alembic.operations import Operations
from alembic.operations.ops import MigrationScript, UpgradeOps
from alembic.runtime.migration import MigrationContext
from sqlalchemy import MetaData
from sqlalchemy.engine import Connection

logger = logging.getLogger(__name__)


class SchemaMigrator:
    _CONTEXT_OPTS: dict[str, bool] = {
        "compare_type": True,
        "compare_server_default": True,
    }

    def __init__(self, conn: Connection) -> None:
        self._conn = conn

    def build_migration(self, source_meta: MetaData) -> MigrationScript:
        mc = self._make_context(source_meta)
        return produce_migrations(mc, source_meta)

    def render(self, source_meta: MetaData) -> str:
        migration = self.build_migration(source_meta)
        upgrade_ops = migration.upgrade_ops
        if upgrade_ops is None:
            return ""
        return render_python_code(upgrade_ops)

    def apply(self, source_meta: MetaData) -> None:
        migration = self.build_migration(source_meta)
        upgrade_ops = migration.upgrade_ops
        if upgrade_ops is None or upgrade_ops.is_empty():
            logger.info("Нет изменений для применения.")
            return

        mc = self._make_context(source_meta)
        ops = Operations(mc)
        self._invoke_ops(ops, upgrade_ops)
        logger.info("DDL-операции успешно применены.")

    # ------------------------------------------------------------------

    def _invoke_ops(self, ops: Operations, upgrade_ops: UpgradeOps) -> None:
        for op in upgrade_ops.ops:
            if hasattr(op, "ops"):
                self._invoke_ops(ops, op)
            else:
                ops.invoke(op)

    def _make_context(self, source_meta: MetaData) -> MigrationContext:
        return MigrationContext.configure(
            self._conn,
            opts={**self._CONTEXT_OPTS, "target_metadata": source_meta},
        )