from database.database import get_connection


def create_report(user_id, report_type, hospital_name, report_date, file_path):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO reports (user_id, report_type, hospital_name, report_date, file_path) VALUES (?, ?, ?, ?, ?)",
        (user_id, report_type, hospital_name, report_date, file_path),
    )
    conn.commit()
    report_id = cur.lastrowid
    conn.close()
    return report_id


def save_test_results(report_id, tests):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM test_results WHERE report_id = ?", (report_id,))
    for test in tests or []:
        cur.execute(
            """INSERT INTO test_results
            (report_id, test_name, value, unit, reference_low, reference_high, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (test["test_name"],) if False else (
                report_id, test["test_name"], test.get("value"), test.get("unit", ""),
                test.get("reference_low"), test.get("reference_high"), test.get("status", "Unknown")
            ),
        )
    conn.commit()
    conn.close()


def get_reports_for_user(user_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM reports WHERE user_id = ? ORDER BY uploaded_at DESC",
        (user_id,),
    ).fetchall()
    conn.close()
    return rows


def get_report_by_id(report_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM reports WHERE report_id = ?", (report_id,)).fetchone()
    conn.close()
    return row


def get_test_results(report_id):
    conn = get_connection()
    rows = conn.execute("SELECT * FROM test_results WHERE report_id = ? ORDER BY id", (report_id,)).fetchall()
    conn.close()
    return rows


def count_abnormal_results_for_user(user_id):
    conn = get_connection()
    row = conn.execute(
        """SELECT COUNT(*) AS cnt FROM test_results tr JOIN reports r ON tr.report_id=r.report_id
        WHERE r.user_id=? AND tr.status IN ('Low','High')""", (user_id,)
    ).fetchone()
    conn.close()
    return int(row["cnt"] if row else 0)


def get_status_breakdown_for_user(user_id):
    conn = get_connection()
    rows = conn.execute(
        """SELECT tr.status, COUNT(*) AS cnt FROM test_results tr JOIN reports r ON tr.report_id=r.report_id
        WHERE r.user_id=? GROUP BY tr.status""", (user_id,)
    ).fetchall()
    conn.close()
    out = {"Normal": 0, "Low": 0, "High": 0, "Unknown": 0}
    for row in rows:
        if row["status"] in out:
            out[row["status"]] = int(row["cnt"])
    return out


def get_distinct_test_names(user_id):
    conn = get_connection()
    rows = conn.execute(
        """SELECT DISTINCT tr.test_name FROM test_results tr JOIN reports r ON tr.report_id=r.report_id
        WHERE r.user_id=? ORDER BY tr.test_name COLLATE NOCASE""", (user_id,)
    ).fetchall()
    conn.close()
    return [row["test_name"] for row in rows]


def get_test_history(user_id, test_name):
    conn = get_connection()
    rows = conn.execute(
        """SELECT r.report_date, tr.value, tr.unit, tr.reference_low, tr.reference_high, tr.status
        FROM test_results tr JOIN reports r ON tr.report_id=r.report_id
        WHERE r.user_id=? AND tr.test_name=? ORDER BY r.report_date ASC""", (user_id, test_name)
    ).fetchall()
    conn.close()
    return rows


def delete_report(report_id, user_id):
    import os
    conn = get_connection()
    cur = conn.cursor()
    row = cur.execute(
        "SELECT file_path FROM reports WHERE report_id=? AND user_id=?", (report_id, user_id)
    ).fetchone()
    if not row:
        conn.close()
        return False
    path = row["file_path"]
    cur.execute("DELETE FROM ai_insights WHERE report_id=?", (report_id,))
    cur.execute("DELETE FROM test_results WHERE report_id=?", (report_id,))
    cur.execute("DELETE FROM reports WHERE report_id=? AND user_id=?", (report_id, user_id))
    conn.commit()
    conn.close()
    if path and os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass
    return True
