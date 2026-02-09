"""
Migration SQLite -> PostgreSQL for AI Orchestrator v8.2.0
Migrates users, conversations, messages, audit_logs.
Tables feedbacks and tools are empty -> no migration needed.
ChromaDB is empty -> no migration needed.
"""

import json
import sqlite3

import psycopg2

SQLITE_PATH = "/home/lalpha/projets/ai-tools/ai-orchestrator/backend/data/orchestrator.db"
PG_DSN = "host=127.0.0.1 port=5432 dbname=ai_orchestrator user=lalpha password=lalpha2024secure"


def migrate():
    sqlite_conn = sqlite3.connect(SQLITE_PATH)
    sqlite_conn.row_factory = sqlite3.Row
    pg_conn = psycopg2.connect(PG_DSN)
    pg_cur = pg_conn.cursor()

    try:
        # 1. Users
        print("Migrating users...")
        rows = sqlite_conn.execute("SELECT * FROM users").fetchall()
        for r in rows:
            pg_cur.execute(
                """
                INSERT INTO users (id, username, email, hashed_password, is_active, is_admin, metadata, created_at, updated_at)
                VALUES (%s::uuid, %s, %s, %s, %s::boolean, %s::boolean, '{}'::jsonb, %s, %s)
                ON CONFLICT (id) DO NOTHING
                """,
                (
                    r["id"],
                    r["username"],
                    r["email"],
                    r["hashed_password"],
                    bool(r["is_active"]),
                    bool(r["is_admin"]),
                    r["created_at"],
                    r["updated_at"],
                ),
            )
        print(f"  -> {len(rows)} users migrated")

        # 2. Conversations
        print("Migrating conversations...")
        rows = sqlite_conn.execute("SELECT * FROM conversations").fetchall()
        for r in rows:
            pg_cur.execute(
                """
                INSERT INTO conversations (id, user_id, title, model, metadata, created_at, updated_at)
                VALUES (%s::uuid, %s::uuid, %s, %s, '{}'::jsonb, %s, %s)
                ON CONFLICT (id) DO NOTHING
                """,
                (
                    r["id"],
                    r["user_id"],
                    r["title"],
                    r["model"],
                    r["created_at"],
                    r["updated_at"],
                ),
            )
        print(f"  -> {len(rows)} conversations migrated")

        # 3. Messages
        print("Migrating messages...")
        rows = sqlite_conn.execute("SELECT * FROM messages").fetchall()
        for r in rows:
            # Convert tools_used TEXT -> JSONB
            tools = "[]"
            if r["tools_used"]:
                try:
                    json.loads(r["tools_used"])
                    tools = r["tools_used"]
                except (json.JSONDecodeError, TypeError):
                    tools = json.dumps([r["tools_used"]])

            # Convert thinking TEXT -> JSONB
            thinking = "{}"
            if r["thinking"]:
                try:
                    json.loads(r["thinking"])
                    thinking = r["thinking"]
                except (json.JSONDecodeError, TypeError):
                    thinking = json.dumps({"raw": r["thinking"]})

            pg_cur.execute(
                """
                INSERT INTO messages (id, conversation_id, role, content, model, tools_used, thinking, metadata, created_at)
                VALUES (%s, %s::uuid, %s, %s, %s, %s::jsonb, %s::jsonb, '{}'::jsonb, %s)
                ON CONFLICT (id) DO NOTHING
                """,
                (
                    r["id"],
                    r["conversation_id"],
                    r["role"],
                    r["content"],
                    r["model"],
                    tools,
                    thinking,
                    r["created_at"],
                ),
            )

        # Reset sequence for SERIAL
        pg_cur.execute(
            "SELECT setval('messages_id_seq', (SELECT COALESCE(MAX(id), 0) FROM messages))"
        )
        print(f"  -> {len(rows)} messages migrated")

        # 4. Audit logs
        print("Migrating audit_logs...")
        rows = sqlite_conn.execute("SELECT * FROM audit_logs").fetchall()
        for r in rows:
            # Merge command, parameters, result -> details JSONB
            details = {}
            if r["command"]:
                details["command"] = r["command"]
            if r["parameters"]:
                try:
                    details["parameters"] = json.loads(r["parameters"])
                except (json.JSONDecodeError, TypeError):
                    details["parameters"] = r["parameters"]
            if r["result"]:
                try:
                    details["result"] = json.loads(r["result"])
                except (json.JSONDecodeError, TypeError):
                    details["result"] = r["result"]

            pg_cur.execute(
                """
                INSERT INTO audit_logs (id, timestamp, user_id, action, resource, allowed, role, details, ip_address, user_agent)
                VALUES (%s, %s, %s::uuid, %s, %s, %s::boolean, %s, %s::jsonb, %s::inet, %s)
                ON CONFLICT (id) DO NOTHING
                """,
                (
                    r["id"],
                    r["timestamp"],
                    r["user_id"],
                    r["action"],
                    r["resource"],
                    bool(r["allowed"]),
                    r["role"],
                    json.dumps(details),
                    r["ip_address"] if r["ip_address"] else None,
                    r["user_agent"],
                ),
            )

        pg_cur.execute(
            "SELECT setval('audit_logs_id_seq', (SELECT COALESCE(MAX(id), 0) FROM audit_logs))"
        )
        print(f"  -> {len(rows)} audit_logs migrated")

        pg_conn.commit()
        print("\nMigration complete!")

        # Verification
        for table in ["users", "conversations", "messages", "audit_logs"]:
            pg_cur.execute(f"SELECT COUNT(*) FROM {table}")  # noqa: S608
            count = pg_cur.fetchone()[0]
            print(f"  {table}: {count} rows")

    except Exception as e:
        pg_conn.rollback()
        print(f"\nMigration failed: {e}")
        raise
    finally:
        sqlite_conn.close()
        pg_cur.close()
        pg_conn.close()


if __name__ == "__main__":
    migrate()
