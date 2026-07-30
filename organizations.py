import streamlit as st
from db import get_db_connection


@st.cache_data(ttl=60)
def get_organizations(role):
    with get_db_connection() as cur:
        cur.execute("SELECT id, name FROM organizations WHERE role = %s ORDER BY name;", (role,))
        return cur.fetchall()


def create_organization(name, role, inn, ogrn, address, phone, sro_info):
    with get_db_connection() as cur:
        cur.execute(
            """
            INSERT INTO organizations (name, role, inn, ogrn, address, phone, sro_info)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
            """,
            (name, role, inn, ogrn, address, phone, sro_info or None),
        )
        return cur.fetchone()[0]


@st.cache_data(ttl=60)
def get_all_organizations():
    with get_db_connection() as cur:
        cur.execute("SELECT id, name, role FROM organizations ORDER BY name;")
        return cur.fetchall()
