#!/usr/bin/env python3
"""Utility script to export request.egrul_data rows grouped by Type."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Iterable, List

import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor


def parse_types(raw: Iterable[int]) -> List[int]:
    unique = sorted({int(value) for value in raw})
    return [value for value in unique if 0 <= value <= 9]


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Export JSONB payloads from request.egrul_data by Type field"
    )
    parser.add_argument(
        "--dsn",
        default=os.getenv("DATABASE_URL"),
        help="Full Postgres DSN. Overrides individual connection params if set.",
    )
    parser.add_argument(
        "--host",
        default=os.getenv("PGHOST", "localhost"),
        help="Postgres host (ignored when --dsn is provided)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("PGPORT", "5432")),
        help="Postgres port",
    )
    parser.add_argument(
        "--dbname",
        default=os.getenv("PGDATABASE"),
        help="Database name",
    )
    parser.add_argument(
        "--user",
        default=os.getenv("PGUSER"),
        help="Database user",
    )
    parser.add_argument(
        "--password",
        default=os.getenv("PGPASSWORD"),
        help="Database password",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("exports/egrul_types"),
        help="Directory to store JSONL exports",
    )
    parser.add_argument(
        "--types",
        nargs="*",
        type=int,
        default=list(range(10)),
        help="Type values to export (defaults to 0..9)",
    )
    parser.add_argument(
        "--table",
        default="request",
        help="Source table name (defaults to request)",
    )
    parser.add_argument(
        "--column",
        default="egrul_data",
        help="JSONB column containing the payload",
    )
    parser.add_argument(
        "--include-empty",
        action="store_true",
        help="Create empty files even when no rows match the requested Type",
    )
    return parser


def build_conn_kwargs(args: argparse.Namespace) -> dict:
    if args.dsn:
        return {"dsn": args.dsn}

    required = []
    for key in ("dbname", "user", "password"):
        if getattr(args, key) is None:
            required.append(f"--{key}")
    if required:
        missing = ", ".join(required)
        raise SystemExit(f"Missing required connection parameters: {missing}")

    return {
        "host": args.host,
        "port": args.port,
        "dbname": args.dbname,
        "user": args.user,
        "password": args.password,
    }


def export_types(conn, query, types: List[int], output_dir: Path, include_empty: bool) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        for value in types:
            cur.execute(query, (str(value),))
            rows = cur.fetchall()

            if not rows and not include_empty:
                continue

            target_path = output_dir / f"type_{value}.jsonl"
            with target_path.open("w", encoding="utf-8") as fh:
                for row in rows:
                    payload = {
                        "request_id": row["id"],
                        "egrul_data": row["egrul_data"],
                    }
                    fh.write(json.dumps(payload, ensure_ascii=False) + "\n")

            print(f"Type {value}: exported {len(rows)} rows to {target_path}")


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()

    types = parse_types(args.types)
    if not types:
        raise SystemExit("No valid Type values requested (expected integers 0-9)")

    query = sql.SQL(
        """
        SELECT id, {column}
        FROM {table}
        WHERE {column} ->> 'Type' = %s
        ORDER BY id
        """
    ).format(column=sql.Identifier(args.column), table=sql.Identifier(args.table))

    conn_kwargs = build_conn_kwargs(args)
    with psycopg2.connect(**conn_kwargs) as conn:
        export_types(conn, query, types, args.output_dir, args.include_empty)


if __name__ == "__main__":
    main()
