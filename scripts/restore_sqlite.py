"""Restore a SQLite backup to DATABASE_PATH."""

import argparse
import os
import sqlite3
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="SQLite backup file to restore")
    parser.add_argument("--database-path", type=Path, default=os.getenv("DATABASE_PATH", "cashflow.db"))
    parser.add_argument("--confirm-overwrite", action="store_true")
    args = parser.parse_args()

    source = args.source
    destination = args.database_path
    if source.resolve() == destination.resolve():
        parser.error("source and destination must be different files")
    if not source.is_file():
        parser.error(f"backup does not exist: {source}")
    if destination.exists() and destination.stat().st_size > 0 and not args.confirm_overwrite:
        parser.error(f"refusing to overwrite non-empty target: {destination}; use --confirm-overwrite")

    destination.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(source) as source_connection, sqlite3.connect(destination) as destination_connection:
        source_connection.backup(destination_connection)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())