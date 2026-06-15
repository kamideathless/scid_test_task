from __future__ import annotations

import logging

from sqlalchemy import MetaData
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)


class SchemaReflector:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def reflect(self) -> MetaData:
        meta = MetaData()
        meta.reflect(bind=self._engine)
        logger.info('Отражено %d таблиц из БД.', len(meta.tables))
        return meta
