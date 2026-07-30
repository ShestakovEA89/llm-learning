import streamlit as st
from db import get_db_connection


@st.cache_data(ttl=60)
def get_objects():
    with get_db_connection() as cur:
        cur.execute("SELECT id, name, address FROM objects ORDER BY name;")
        return cur.fetchall()


@st.cache_data(ttl=60)
def get_object_org_links(object_id):
    with get_db_connection() as cur:
        cur.execute(
            "SELECT developer_org_id, contractor_org_id FROM objects WHERE id = %s;",
            (object_id,),
        )
        row = cur.fetchone()
        return row if row else (None, None)


def create_object(name, address):
    with get_db_connection() as cur:
        cur.execute(
            """
            INSERT INTO objects (name, address)
            VALUES (%s, %s)
            RETURNING id;
            """,
            (name, address),
        )
        return cur.fetchone()[0]


def update_object_org_links(object_id, developer_org_id, contractor_org_id):
    with get_db_connection() as cur:
        cur.execute(
            """
            UPDATE objects SET developer_org_id = %s, contractor_org_id = %s
            WHERE id = %s;
            """,
            (developer_org_id, contractor_org_id, object_id),
        )
