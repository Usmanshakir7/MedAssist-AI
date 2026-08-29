from database.database import get_connection


def save_insight(report_id, summary, recommendation):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM ai_insights WHERE report_id=?", (report_id,))
    cur.execute(
        "INSERT INTO ai_insights (report_id, summary, recommendation) VALUES (?, ?, ?)",
        (report_id, summary, recommendation),
    )
    conn.commit()
    conn.close()


def get_insight(report_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM ai_insights WHERE report_id=? ORDER BY created_at DESC LIMIT 1",
        (report_id,),
    ).fetchone()
    conn.close()
    return row
