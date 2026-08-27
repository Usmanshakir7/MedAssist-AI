from database.database import get_connection


def save_test_results(report_id, parsed_results):

    conn = get_connection()
    cursor = conn.cursor()

    for result in parsed_results:

        cursor.execute("""
            INSERT INTO test_results (
                report_id,
                test_name,
                value,
                unit,
                reference_low,
                reference_high,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            report_id,
            result["test_name"],
            result["value"],
            result["unit"],
            result["reference_low"],
            result["reference_high"],
            None
        ))

    conn.commit()
    conn.close()


def get_test_results(report_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM test_results
        WHERE report_id = ?
    """, (report_id,))

    results = cursor.fetchall()

    conn.close()

    return results