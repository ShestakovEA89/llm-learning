import re
import streamlit as st
from db import get_db_connection


@st.cache_data(ttl=60)
def get_registries_for_object(object_id):
    with get_db_connection() as cur:
        cur.execute(
            """
            SELECT id, work_section_name, project_marks
            FROM registries
            WHERE object_id = %s
            ORDER BY id;
            """,
            (object_id,),
        )
        return cur.fetchall()


def _natural_sort_key(seq_number):
    seq_number = seq_number or ""
    return [int(part) if part.isdigit() else part for part in re.split(r"(\d+)", seq_number)]


@st.cache_data(ttl=60)
def get_registry_documents(registry_id):
    with get_db_connection() as cur:
        cur.execute(
            """
            SELECT id, seq_number, is_category_header, document_name, document_number_date,
                   issuing_org, page_count, note
            FROM registry_documents
            WHERE registry_id = %s;
            """,
            (registry_id,),
        )
        documents = cur.fetchall()
    documents.sort(key=lambda row: _natural_sort_key(row[1]))
    return documents
