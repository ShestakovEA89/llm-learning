import streamlit as st
from db import get_db_connection


def create_act(object_id, developer_org_id, contractor_org_id, act_number, date_start, date_end, act_date, work_name, designer_org_id=None, project_docs_ref=None, normative_docs=None, supporting_docs=None):
    with get_db_connection() as cur:
        cur.execute(
            """
            INSERT INTO acts (object_id, developer_org_id, contractor_org_id, act_number, date_start, date_end, act_date, work_name, designer_org_id, project_docs_ref, normative_docs, supporting_docs)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
            """,
            (object_id, developer_org_id, contractor_org_id, act_number, date_start, date_end, act_date, work_name, designer_org_id, project_docs_ref, normative_docs, supporting_docs),
        )
        return cur.fetchone()[0]


def create_act_signatory(act_id, person_id, role):
    with get_db_connection() as cur:
        cur.execute(
            """
            INSERT INTO act_signatories (act_id, person_id, role)
            VALUES (%s, %s, %s);
            """,
            (act_id, person_id, role),
        )


def create_material(act_id, material_name, certificate_number, valid_from, valid_to):
    with get_db_connection() as cur:
        cur.execute(
            """
            INSERT INTO materials (act_id, material_name, certificate_number, certificate_valid_from, certificate_valid_to)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id;
            """,
            (act_id, material_name, certificate_number, valid_from, valid_to),
        )
        return cur.fetchone()[0]


@st.cache_data(ttl=60)
def get_acts_for_object(object_id):
    with get_db_connection() as cur:
        cur.execute(
            """
            SELECT id, act_number, act_date, work_name
            FROM acts
            WHERE object_id = %s
            ORDER BY act_date DESC, id DESC;
            """,
            (object_id,),
        )
        return cur.fetchall()


@st.cache_data(ttl=60)
def get_materials_for_act(act_id):
    with get_db_connection() as cur:
        cur.execute(
            """
            SELECT id, material_name, certificate_number, certificate_valid_from, certificate_valid_to
            FROM materials
            WHERE act_id = %s
            ORDER BY id;
            """,
            (act_id,),
        )
        return cur.fetchall()
