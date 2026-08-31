from db import get_db_connection


def create_pending_request(object_id, title, requested_from, note=None):
    with get_db_connection() as cur:
        cur.execute(
            """
            INSERT INTO pending_requests (object_id, title, requested_from, note)
            VALUES (%s, %s, %s, %s)
            RETURNING id;
            """,
            (object_id, title, requested_from, note),
        )
        return cur.fetchone()[0]


def get_pending_requests(object_id):
    with get_db_connection() as cur:
        cur.execute(
            """
            SELECT id, title, requested_from, status, created_at, completed_at, note
            FROM pending_requests
            WHERE object_id = %s
            ORDER BY (status = 'ожидает') DESC, created_at ASC;
            """,
            (object_id,),
        )
        return cur.fetchall()


def mark_request_completed(request_id):
    with get_db_connection() as cur:
        cur.execute(
            """
            UPDATE pending_requests
            SET status = 'получено', completed_at = now()
            WHERE id = %s;
            """,
            (request_id,),
        )
