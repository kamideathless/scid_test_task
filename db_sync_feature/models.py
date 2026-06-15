"""Дтошка для результатов синхронизации."""

from __future__ import annotations

from dataclasses import dataclass, field

# Alembic возвращает эту строку когда изменений нет
_ALEMBIC_EMPTY = {'pass', ''}


@dataclass
class SyncReport:
    dry_run: bool
    upgrade_sql: str = ''
    errors: list[str] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        lines = [
            line.strip() for line in self.upgrade_sql.splitlines() if line.strip() and not line.strip().startswith('#')
        ]
        return bool(lines) and lines != ['pass']

    @property
    def success(self) -> bool:
        return not self.errors

    def __str__(self) -> str:
        mode = '[DRY RUN]' if self.dry_run else '[APPLIED]'
        if not self.has_changes:
            return f'{mode} Схемы идентичны, изменений нет.'
        lines = [f'{mode} Изменения схемы:', self.upgrade_sql]
        if self.errors:
            lines += ['', 'Ошибки:'] + self.errors
        return '\n'.join(lines)
