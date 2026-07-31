from db import get_db_connection


def get_work_journal_entries(object_id):
    with get_db_connection() as cur:
        cur.execute(
            """
            SELECT work_date, location, work_type, description
            FROM work_journal
            WHERE object_id = %s
            ORDER BY work_date DESC
            LIMIT 20;
            """,
            (object_id,),
        )
        return cur.fetchall()


def get_work_journal_entries_for_period(object_id, date_start, date_end):
    with get_db_connection() as cur:
        cur.execute(
            """
            SELECT work_date, location, work_type, description
            FROM work_journal
            WHERE object_id = %s AND work_date BETWEEN %s AND %s
            ORDER BY work_date ASC;
            """,
            (object_id, date_start, date_end),
        )
        return cur.fetchall()


def create_work_journal_entry(object_id, work_date, location, work_type, description):
    with get_db_connection() as cur:
        cur.execute(
            """
            INSERT INTO work_journal (object_id, work_date, location, work_type, description)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id;
            """,
            (object_id, work_date, location, work_type, description),
        )
        return cur.fetchone()[0]
