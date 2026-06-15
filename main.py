"""Точка входа с подтверждением синхронизации."""

from __future__ import annotations

import logging

from db_sync_feature import DbSchemaSynchronizer

logging.basicConfig(
    level=logging.WARNING,  # глушим alembic-спам
    format='%(asctime)s %(levelname)s %(message)s',
)

SOURCE_DSN = 'postgresql://postgres:pass@localhost:5432/test_db'
TARGET_DSN = 'postgresql://postgres:pass@localhost:5433/prod_db'


def _format_diff(raw: str) -> str:
    labels = {
        'op.create_table': '  [+] Создать таблицу',
        'op.drop_table': '  [-] Удалить таблицу',
        'op.add_column': '  [+] Добавить колонку',
        'op.drop_column': '  [-] Удалить колонку',
        'op.alter_column': '  [~] Изменить колонку',
        'op.create_index': '  [+] Создать индекс',
        'op.drop_index': '  [-] Удалить индекс',
        'op.create_foreign_key': '  [+] Добавить FK',
        'op.drop_constraint': '  [-] Удалить constraint',
    }

    lines: list[str] = []
    for line in raw.splitlines():
        stripped = line.strip()
        for op_key, label in labels.items():
            if stripped.startswith(op_key):
                try:
                    args = stripped[len(op_key) + 1 :]
                    name = args.split(',')[0].strip().strip('\'"')
                except IndexError:
                    name = ''
                lines.append(f'{label}: {name}')
                break

    return '\n'.join(lines) if lines else '(нет изменений)'


def main() -> None:
    syncer = DbSchemaSynchronizer(
        source_dsn=SOURCE_DSN,
        target_dsn=TARGET_DSN,
    )

    print('DB Schema Synchronizer')
    print(f'source → {SOURCE_DSN.split("@")[-1]}')
    print(f'target → {TARGET_DSN.split("@")[-1]}')

    report = syncer.sync(dry_run=True)

    if not report.has_changes:
        print('\nСхемы идентичны.')
        return

    print('\nОбнаружены изменения:\n')
    print(_format_diff(report.upgrade_sql))
    print()
    print('Подробный план (Alembic ops):')
    for line in report.upgrade_sql.splitlines():
        if line.strip() and not line.strip().startswith('#'):
            print(f'{line}')

    answer = input('\nПрименить изменения к основной БД? [Y/n]: ').strip().lower()

    if answer != 'y':
        print('\nОтменено. Основная БД не изменена.')
        return

    print('\nПрименяем')
    result = syncer.sync(dry_run=False)

    if result.success:
        print('Синхронизация завершена успешно.')
    else:
        print('Ошибки при синхронизации:')
        for err in result.errors:
            print(f'{err}')


if __name__ == '__main__':
    main()
