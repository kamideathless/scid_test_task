from __future__ import annotations

import logging

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from .migrator import SchemaMigrator
from .models import SyncReport
from .reflector import SchemaReflector

logger = logging.getLogger(__name__)


class DbSchemaSynchronizer:
    """Корректирует схему целевой БД по образцу исходной БД.

    Первая БД (source) - образец (тестовая).
    Вторая БД (target) - основная; данные не затрагиваются."""

    def __init__(self, source_dsn: str, target_dsn: str) -> None:
        self._source_engine: Engine = create_engine(source_dsn)
        self._target_engine: Engine = create_engine(target_dsn)

    def sync(self, dry_run: bool = False) -> SyncReport:
        report = SyncReport(dry_run=dry_run)

        source_meta = SchemaReflector(self._source_engine).reflect()

        with self._target_engine.connect() as conn:
            migrator = SchemaMigrator(conn)
            report.upgrade_sql = migrator.render(source_meta)

            if not report.has_changes:
                logger.info('Схемы идентичны, изменений нет.')
                return report

            if dry_run:
                logger.info('[DRY RUN] Изменения не применяются.')
                return report

            logger.info('Применение изменений схемы.')
            try:
                migrator.apply(source_meta)
                conn.commit()
            except Exception as exc:
                conn.rollback()
                report.errors.append(str(exc))
                logger.error('Ошибка при синхронизации: %s', exc)

        return report

    def diff(self) -> str:
        return str(self.sync(dry_run=True))
