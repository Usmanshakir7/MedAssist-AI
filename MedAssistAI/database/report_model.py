from database.database import get_connection


def create_report(user_id, report_type, hospital_name, report_date, file_path):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO reports
        (user_id, report_type, hospital_name, report_date, file_path)
        VALUES (?, ?, ?, ?, ?)
    """, (
        user_id,
        report_type,
        hospital_name,
        report_date,
        file_path
    ))

    conn.commit()

    report_id = cursor.lastrowid

    conn.close()

    return report_id