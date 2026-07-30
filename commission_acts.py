import streamlit as st
from db import get_db_connection


def create_commission_act(object_id, act_type, act_date, city, findings_text):
    with get_db_connection() as cur:
        cur.execute(
            """
            INSERT INTO commission_acts (object_id, act_type, act_date, city, findings_text)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id;
            """,
            (object_id, act_type, act_date, city, findings_text or None),
        )
        return cur.fetchone()[0]


def create_commission_act_signatory(commission_act_id, person_id, role):
    with get_db_connection() as cur:
        cur.execute(
            """
            INSERT INTO commission_act_signatories (commission_act_id, person_id, role)
            VALUES (%s, %s, %s);
            """,
            (commission_act_id, person_id, role),
        )


@st.cache_data(ttl=60)
def get_commission_acts_for_object(object_id):
    with get_db_connection() as cur:
        cur.execute(
            """
            SELECT id, act_type, act_date, city, findings_text, created_at
            FROM commission_acts
            WHERE object_id = %s
            ORDER BY act_type, act_date DESC;
            """,
            (object_id,),
        )
        return cur.fetchall()


@st.cache_data(ttl=60)
def get_commission_act_signatories(commission_act_id):
    with get_db_connection() as cur:
        cur.execute(
            """
            SELECT cas.role, rp.full_name, rp.position
            FROM commission_act_signatories cas
            JOIN responsible_persons rp ON rp.id = cas.person_id
            WHERE cas.commission_act_id = %s
            ORDER BY cas.id;
            """,
            (commission_act_id,),
        )
        return cur.fetchall()
