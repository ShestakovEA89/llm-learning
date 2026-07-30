import streamlit as st
from db import get_db_connection


@st.cache_data(ttl=60)
def get_document_list():
    try:
        with get_db_connection() as cur:
            cur.execute("SELECT DISTINCT metadata->>'file_name' FROM vecs.pto_documents;")
            return [row[0] for row in cur.fetchall() if row[0]]
    except Exception:
        return []
