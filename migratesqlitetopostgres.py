"""
migrate_sqlite_to_postgres.py — one-time data migration.

Run this ONCE, after deploying the Postgres-backed code (so all the new
tables already exist — start the server once first, or run the various
init_*_db() functions, so Postgres has every table created) but BEFORE
you point real traffic at Postgres.

WHAT THIS DOES
Copies every row from the old naija_sensei.db SQLite file into the
matching Postgres tables, column-for-column, preserving primary key
values (so foreign keys like chat_history.user_id still point at the
right row). It does NOT touch schema — the Postgres tables must already
exist (run the app once, or call the init_*_db() functions yourself,
before running this).

USAGE
  export DATABASE_URL="postgresql://naijasensei:PASSWORD@host:5432/naijasensei"
  python migrate_sqlite_to_postgres.py /path/to/naija_sensei.db

WHAT IT DOESN'T DO
  - Doesn't migrate the RAG/vector index — that's rebuilt from
    curriculum.py + data/generated_curriculum.py on startup, not stored
    per-user data, so there's nothing to carry over.
  - Doesn't reset Postgres's auto-increment sequences after copying
    explicit id values — this script does that as its last step for
    every BIGSERIAL/SERIAL table it touches, so the next INSERT in the
    live app doesn't collide with a migrated id. If you add a table
    later, add it to TABLES below and it'll be covered automatically.
"""

import sys
import sqlite3
import psycopg2
import psycopg2.extras
import os

# (table_name, id_column_or_None) — id_column is used to reset the
# Postgres sequence after copying explicit id values. None means the
# table has no auto-increment id column (e.g. composite-key tables).
TABLES = [
    ("users", "id"),
    ("chat_history", "id"),
    ("user_activity", None),           # user_id is the PK, no sequence
    ("activity_minutes", "id"),
    ("broadcasts", "id"),
    ("broadcast_reads", None),         # composite PK, no sequence
    ("subject_topics", "id"),
    ("provider_events", "id"),
    ("api_usage_log", "id"),
    ("created_credentials", "id"),
    ("classes", "id"),
    ("class_members", "id"),
    ("parent_links", "id"),
    ("classroom_sessions", "id"),
    ("exam_sessions", "id"),
    ("pq_sessions", "id"),
    ("diagnostic_results", "id"),
    ("student_profiles", None),        # user_id is the PK, no sequence
]


def migrate(sqlite_path: str, database_url: str):
    sconn = sqlite3.connect(sqlite_path)
    sconn.row_factory = sqlite3.Row

    pconn = psycopg2.connect(database_url)
    pconn.autocommit = False
    pcur = pconn.cursor()

    for table, id_col in TABLES:
        try:
            rows = sconn.execute(f"SELECT * FROM {table}").fetchall()
        except sqlite3.OperationalError:
            print(f"[skip] {table}: not present in source SQLite DB")
            continue

        if not rows:
            print(f"[skip] {table}: no rows to migrate")
            continue

        columns = rows[0].keys()
        col_list = ", ".join(columns)
        placeholders = ", ".join(["%s"] * len(columns))
        insert_sql = f"INSERT INTO {table} ({col_list}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"

        data = [tuple(row[c] for c in columns) for row in rows]
        psycopg2.extras.execute_batch(pcur, insert_sql, data, page_size=500)
        pconn.commit()
        print(f"[ok] {table}: migrated {len(rows)} row(s)")

        if id_col:
            # Advance the BIGSERIAL sequence past the highest migrated id,
            # so the app's next INSERT doesn't collide with a copied row.
            pcur.execute(
                f"SELECT setval(pg_get_serial_sequence('{table}', '{id_col}'), "
                f"COALESCE((SELECT MAX({id_col}) FROM {table}), 1))"
            )
            pconn.commit()

    pcur.close()
    pconn.close()
    sconn.close()
    print("\nMigration complete. Spot-check a few tables in Postgres before "
          "cutting traffic over, then keep the old naija_sensei.db file "
          "around as a cold backup for a while rather than deleting it.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python migrate_sqlite_to_postgres.py /path/to/naija_sensei.db")
        sys.exit(1)

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("Set DATABASE_URL first, e.g.:\n"
              '  export DATABASE_URL="postgresql://naijasensei:PASSWORD@host:5432/naijasensei"')
        sys.exit(1)

    migrate(sys.argv[1], database_url)