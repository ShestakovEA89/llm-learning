import streamlit as st
from db import get_db_connection


@st.cache_data(ttl=60)
def get_responsible_persons(organization_ids):
    if not organization_ids:
        return []
    with get_db_connection() as cur:
        cur.execute(
            """
            SELECT id, full_name, position, order_number, order_date, registry_number, organization_id
            FROM responsible_persons
            WHERE organization_id = ANY(%s)
            ORDER BY full_name;
            """,
            (list(organization_ids),),
        )
        return cur.fetchall()


def create_responsible_person(organization_id, full_name, position, order_number, order_date, registry_number):
    with get_db_connection() as cur:
        cur.execute(
            """
            INSERT INTO responsible_persons (organization_id, full_name, position, order_number, order_date, registry_number)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id;
            """,
            (organization_id, full_name, position, order_number, order_date, registry_number or None),
        )
        new_id = cur.fetchone()[0]
        return new_id
