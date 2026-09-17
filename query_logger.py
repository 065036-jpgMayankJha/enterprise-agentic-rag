import psycopg2
import json
import time

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 5433,
    "dbname": "rag_analytics_db",
    "user": "rag_analytics",
    "password": "ragpass123",
}


def log_query(question: str, department: str, answer: str, duration_s: float):
    """Insert a completed query's result into query_logs. Fails silently (logs to stderr) so a logging issue never breaks the main pipeline."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO query_logs (department, question_text, answer_text, latency_ms)
            VALUES (%s, %s, %s, %s)
            """,
            (department, question, answer, int(duration_s * 1000)),
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"[query_logger] WARNING: failed to log query: {e}")
