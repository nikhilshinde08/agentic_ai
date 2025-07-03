#!/usr/bin/env python3
"""
pgsql_to_sqlite.py

Convert a PostgreSQL database to a SQLite database file.
Reads Postgres connection details from a .env file using python-dotenv.

Usage:
    python pgsql_to_sqlite.py --env-file .env --sqlite-file db.sqlite
"""
import os
import argparse
import sys
import json
import decimal
import datetime
import uuid
from dotenv import load_dotenv
import psycopg2
import sqlite3

# Register SQLite adapters for unsupported types
sqlite3.register_adapter(decimal.Decimal, lambda d: float(d))
sqlite3.register_adapter(datetime.datetime, lambda dt: dt.isoformat())
sqlite3.register_adapter(datetime.date, lambda d: d.isoformat())
sqlite3.register_adapter(dict, lambda d: json.dumps(d))
sqlite3.register_adapter(list, lambda l: json.dumps(l))
sqlite3.register_adapter(uuid.UUID, lambda u: str(u))
sqlite3.register_adapter(memoryview, lambda m: m.tobytes())

# Mapping of Postgres types to SQLite types
TYPE_MAPPING = {
    'integer': 'INTEGER',
    'bigint': 'INTEGER',
    'smallint': 'INTEGER',
    'serial': 'INTEGER',
    'bigserial': 'INTEGER',
    'boolean': 'INTEGER',
    'text': 'TEXT',
    'character varying': 'TEXT',
    'varchar': 'TEXT',
    'date': 'TEXT',
    'timestamp without time zone': 'TEXT',
    'timestamp with time zone': 'TEXT',
    'numeric': 'REAL',
    'real': 'REAL',
    'double precision': 'REAL',
    'bytea': 'BLOB',
    'uuid': 'TEXT',
    'json': 'TEXT',
    'jsonb': 'TEXT',
}

def parse_args():
    parser = argparse.ArgumentParser(
        description="Convert Postgres DB to SQLite file."
    )
    parser.add_argument(
        '--env-file', default='.env',
        help='Path to .env file with PG_HOST, PG_PORT, PG_DB, PG_USER, PG_PASSWORD'
    )
    parser.add_argument(
        '--sqlite-file', default='db.sqlite',
        help='Output SQLite database file path'
    )
    return parser.parse_args()


def map_type(pg_type: str) -> str:
    # Return SQLite type or default to TEXT
    return TYPE_MAPPING.get(pg_type.lower(), 'TEXT')


def main():
    args = parse_args()
    # Load environment variables
    load_dotenv(args.env_file)
    host = os.getenv('DB_HOST')
    port = os.getenv('DB_PORT', 5432)
    dbname = os.getenv('DB_NAME')
    user = os.getenv('DB_USER')
    password = os.getenv('DB_PASSWORD')

    if not all([host, dbname, user, password]):
        print("Error: Missing one of PG_HOST, PG_DB, PG_USER, or PG_PASSWORD in .env", file=sys.stderr)
        sys.exit(1)

    # Connect to PostgreSQL
    pg_conn = psycopg2.connect(
        host=host, port=port, dbname=dbname, user=user, password=password
    )
    pg_cur = pg_conn.cursor()

    # Prepare SQLite
    if os.path.exists(args.sqlite_file):
        os.remove(args.sqlite_file)
    sq_conn = sqlite3.connect(args.sqlite_file)
    sq_cur = sq_conn.cursor()
    sq_cur.execute('PRAGMA foreign_keys = OFF;')

    # Get list of tables
    pg_cur.execute(
        """
        SELECT table_name
          FROM information_schema.tables
         WHERE table_schema = 'public'
           AND table_type = 'BASE TABLE';
        """
    )
    tables = [row[0] for row in pg_cur.fetchall()]

    for table in tables:
        # Fetch column definitions
        pg_cur.execute(
            """
            SELECT column_name, data_type, is_nullable
              FROM information_schema.columns
             WHERE table_schema = 'public'
               AND table_name = %s
             ORDER BY ordinal_position;
            """, (table,)
        )
        cols = pg_cur.fetchall()

        # Construct CREATE TABLE statement
        col_defs = []
        for col_name, data_type, is_nullable in cols:
            col_type = map_type(data_type)
            notnull = '' if is_nullable == 'YES' else ' NOT NULL'
            col_defs.append(f'"{col_name}" {col_type}{notnull}')

        create_stmt = f'CREATE TABLE "{table}" ({", ".join(col_defs)});'
        sq_cur.execute(create_stmt)

        # Copy data
        pg_cur.execute(f'SELECT * FROM "{table}";')
        rows = pg_cur.fetchall()
        if rows:
            placeholders = ','.join(['?'] * len(cols))
            insert_stmt = f'INSERT INTO "{table}" VALUES ({placeholders});'
            sq_cur.executemany(insert_stmt, rows)

    # Finalize
    sq_conn.commit()
    sq_cur.execute('PRAGMA foreign_keys = ON;')
    sq_conn.close()
    pg_cur.close()
    pg_conn.close()

    print(f"Successfully created SQLite database: {args.sqlite_file}")


if __name__ == '__main__':
    main()
