import streamlit as st
import os
import psycopg2
import datetime
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings, StorageContext
from llama_index.llms.anthropic import Anthropic
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.readers.file import PDFReader
from llama_index.vector_stores.supabase import SupabaseVectorStore
from dotenv import load_dotenv

load_dotenv()

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    body,
    p:not([data-testid*="Icon" i]),
    span:not([data-testid*="Icon" i]),
    label:not([data-testid*="Icon" i]),
    button:not([data-testid*="Icon" i]),
    input:not([data-testid*="Icon" i]),
    textarea:not([data-testid*="Icon" i]) {
        font-family: 'Inter', sans-serif !important;
    }

    .stButton > button,
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div {
        border-radius: 12px !important;
    }

    .stButton > button {
        background-color: #0F9D6E !important;
        border-color: #0F9D6E !important;
    }

    .stTextInput *, .stTextArea * {
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
    }

    [data-testid="stTextInput"],
    [data-testid="stTextArea"],
    div:has(> [data-testid="stTextInput"]),
    div:has(> [data-testid="stTextArea"]) {
        overflow: visible !important;
    }

    [data-testid="stTextInput"] > div,
    [data-testid="stTextArea"] > div {
        border: 1px solid transparent !important;
        border-radius: 12px !important;
        overflow: visible !important;
    }

    [data-testid="stTextInput"] > div > div,
    [data-testid="stTextArea"] > div > div {
        border-radius: 12px !important;
    }

    [data-testid="stTextInput"] > div:focus-within,
    [data-testid="stTextArea"] > div:focus-within {
        border: 1px solid transparent !important;
        box-shadow: 0 0 0 1.5px #0F9D6E !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def configure_llm_settings():
    Settings.llm = Anthropic(model="claude-sonnet-4-6")
    Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")


configure_llm_settings()

st.title("Помощник инженера ПТО")

UPLOAD_DIR = "uploaded_docs"
os.makedirs(UPLOAD_DIR, exist_ok=True)

SUPABASE_CONNECTION = os.environ["SUPABASE_CONNECTION"]


def get_vector_store():
    return SupabaseVectorStore(
        postgres_connection_string=SUPABASE_CONNECTION,
        collection_name="pto_documents",
        dimension=384,
    )


@st.cache_data(ttl=60)
def get_document_list():
    try:
        conn = psycopg2.connect(SUPABASE_CONNECTION)
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT metadata->>'file_name' FROM vecs.pto_documents;")
        docs = [row[0] for row in cur.fetchall() if row[0]]
        cur.close()
        conn.close()
        return docs
    except Exception:
        return []


@st.cache_data(ttl=60)
def get_objects():
    conn = psycopg2.connect(SUPABASE_CONNECTION)
    cur = conn.cursor()
    cur.execute("SELECT id, name, address FROM objects ORDER BY name;")
    objects = cur.fetchall()
    cur.close()
    conn.close()
    return objects


@st.cache_data(ttl=60)
def get_object_org_links(object_id):
    conn = psycopg2.connect(SUPABASE_CONNECTION)
    cur = conn.cursor()
    cur.execute(
        "SELECT developer_org_id, contractor_org_id FROM objects WHERE id = %s;",
        (object_id,),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row if row else (None, None)


@st.cache_data(ttl=60)
def get_organizations(role):
    conn = psycopg2.connect(SUPABASE_CONNECTION)
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM organizations WHERE role = %s ORDER BY name;", (role,))
    orgs = cur.fetchall()
    cur.close()
    conn.close()
    return orgs


def create_object(name, address):
    conn = psycopg2.connect(SUPABASE_CONNECTION)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO objects (name, address)
        VALUES (%s, %s)
        RETURNING id;
        """,
        (name, address),
    )
    new_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return new_id


def update_object_org_links(object_id, developer_org_id, contractor_org_id):
    conn = psycopg2.connect(SUPABASE_CONNECTION)
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE objects SET developer_org_id = %s, contractor_org_id = %s
        WHERE id = %s;
        """,
        (developer_org_id, contractor_org_id, object_id),
    )
    conn.commit()
    cur.close()
    conn.close()


def create_organization(name, role, inn, ogrn, address, phone, sro_info):
    conn = psycopg2.connect(SUPABASE_CONNECTION)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO organizations (name, role, inn, ogrn, address, phone, sro_info)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
        """,
        (name, role, inn, ogrn, address, phone, sro_info or None),
    )
    new_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return new_id


@st.cache_data(ttl=60)
def get_work_journal_entries(object_id):
    conn = psycopg2.connect(SUPABASE_CONNECTION)
    cur = conn.cursor()
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
    entries = cur.fetchall()
    cur.close()
    conn.close()
    return entries


@st.cache_data(ttl=60)
def get_work_journal_entries_for_period(object_id, date_start, date_end):
    conn = psycopg2.connect(SUPABASE_CONNECTION)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT work_date, location, work_type, description
        FROM work_journal
        WHERE object_id = %s AND work_date BETWEEN %s AND %s
        ORDER BY work_date ASC;
        """,
        (object_id, date_start, date_end),
    )
    entries = cur.fetchall()
    cur.close()
    conn.close()
    return entries


def create_work_journal_entry(object_id, work_date, location, work_type, description):
    conn = psycopg2.connect(SUPABASE_CONNECTION)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO work_journal (object_id, work_date, location, work_type, description)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id;
        """,
        (object_id, work_date, location, work_type, description),
    )
    new_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return new_id


def create_act(object_id, developer_org_id, contractor_org_id, act_number, date_start, date_end, act_date, work_name, designer_org_id=None):
    conn = psycopg2.connect(SUPABASE_CONNECTION)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO acts (object_id, developer_org_id, contractor_org_id, act_number, date_start, date_end, act_date, work_name, designer_org_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
        """,
        (object_id, developer_org_id, contractor_org_id, act_number, date_start, date_end, act_date, work_name, designer_org_id),
    )
    new_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return new_id


def create_act_signatory(act_id, person_id, role):
    conn = psycopg2.connect(SUPABASE_CONNECTION)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO act_signatories (act_id, person_id, role)
        VALUES (%s, %s, %s);
        """,
        (act_id, person_id, role),
    )
    conn.commit()
    cur.close()
    conn.close()


@st.cache_data(ttl=60)
def get_all_organizations():
    conn = psycopg2.connect(SUPABASE_CONNECTION)
    cur = conn.cursor()
    cur.execute("SELECT id, name, role FROM organizations ORDER BY name;")
    orgs = cur.fetchall()
    cur.close()
    conn.close()
    return orgs


@st.cache_data(ttl=60)
def get_responsible_persons(organization_ids):
    if not organization_ids:
        return []
    conn = psycopg2.connect(SUPABASE_CONNECTION)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, full_name, position, order_number, order_date, registry_number, organization_id
        FROM responsible_persons
        WHERE organization_id = ANY(%s)
        ORDER BY full_name;
        """,
        (list(organization_ids),),
    )
    persons = cur.fetchall()
    cur.close()
    conn.close()
    return persons


def create_responsible_person(organization_id, full_name, position, order_number, order_date, registry_number):
    conn = psycopg2.connect(SUPABASE_CONNECTION)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO responsible_persons (organization_id, full_name, position, order_number, order_date, registry_number)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id;
        """,
        (organization_id, full_name, position, order_number, order_date, registry_number or None),
    )
    new_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return new_id


NEW_OBJECT_OPTION = "➕ Добавить новый объект"
NEW_ORG_OPTION = "➕ Добавить новую организацию"

OBJECT_PLACEHOLDER = "— Выберите объект —"
DEVELOPER_PLACEHOLDER = "— Выберите застройщика —"
CONTRACTOR_PLACEHOLDER = "— Выберите подрядчика —"
OTHER_ORG_OPTION = "— Другая организация из базы —"

TAB_OBJECT_LABEL = "🏗️ Объект"
TAB_JOURNAL_LABEL = "📓 Журнал работ"
TAB_NEW_ACT_LABEL = "📝 Новый акт скрытых работ"
TAB_CHAT_LABEL = "💬 Чат по документам"

if "tabs_key_counter" not in st.session_state:
    st.session_state.tabs_key_counter = 0
if "force_tab" not in st.session_state:
    st.session_state.force_tab = None


def go_to_object_tab():
    st.session_state.force_tab = TAB_OBJECT_LABEL
    st.session_state.tabs_key_counter += 1


tab_object, tab_journal, tab_new_act, tab_chat = st.tabs(
    [TAB_OBJECT_LABEL, TAB_JOURNAL_LABEL, TAB_NEW_ACT_LABEL, TAB_CHAT_LABEL],
    default=st.session_state.force_tab,
    key=f"main_tabs_{st.session_state.tabs_key_counter}",
)

with tab_object:
    st.subheader("Рабочий объект")
    st.caption("Выберите объект, застройщика и подрядчика — они будут использоваться в журнале работ и актах.")

    obj_objects = get_objects()
    obj_developers = get_organizations("застройщик")
    obj_contractors = get_organizations("подрядчик")

    obj_object_options = [(None, OBJECT_PLACEHOLDER)] + list(obj_objects) + [(None, NEW_OBJECT_OPTION)]
    obj_developer_options = [(None, DEVELOPER_PLACEHOLDER)] + list(obj_developers) + [(None, NEW_ORG_OPTION)]
    obj_contractor_options = [(None, CONTRACTOR_PLACEHOLDER)] + list(obj_contractors) + [(None, NEW_ORG_OPTION)]

    obj_object_choice = st.selectbox(
        "Объект",
        options=obj_object_options,
        format_func=lambda o: o[1],
        key="obj_tab_object_choice",
    )
    new_obj_object = {}
    if obj_object_choice[1] == NEW_OBJECT_OPTION:
        st.caption("Новый объект")
        new_obj_object["name"] = st.text_input("Название объекта", key="obj_tab_new_object_name")
        new_obj_object["address"] = st.text_input("Адрес", key="obj_tab_new_object_address")

    if "obj_tab_last_object_id" not in st.session_state:
        st.session_state.obj_tab_last_object_id = None

    if obj_object_choice[0] != st.session_state.obj_tab_last_object_id:
        st.session_state.obj_tab_last_object_id = obj_object_choice[0]
        if obj_object_choice[0] is not None:
            linked_developer_id, linked_contractor_id = get_object_org_links(obj_object_choice[0])
            if linked_developer_id is not None:
                for linked_dev_option in obj_developer_options:
                    if linked_dev_option[0] == linked_developer_id:
                        st.session_state.obj_tab_developer_choice = linked_dev_option
                        break
            if linked_contractor_id is not None:
                for linked_con_option in obj_contractor_options:
                    if linked_con_option[0] == linked_contractor_id:
                        st.session_state.obj_tab_contractor_choice = linked_con_option
                        break

    obj_developer_choice = st.selectbox(
        "Застройщик",
        options=obj_developer_options,
        format_func=lambda o: o[1],
        key="obj_tab_developer_choice",
    )
    new_obj_developer = {}
    if obj_developer_choice[1] == NEW_ORG_OPTION:
        st.caption("Новая организация — застройщик")
        new_obj_developer["name"] = st.text_input("Название организации", key="obj_tab_new_developer_name")
        odcol1, odcol2 = st.columns(2)
        with odcol1:
            new_obj_developer["inn"] = st.text_input("ИНН", key="obj_tab_new_developer_inn")
        with odcol2:
            new_obj_developer["ogrn"] = st.text_input("ОГРН", key="obj_tab_new_developer_ogrn")
        new_obj_developer["address"] = st.text_input("Адрес", key="obj_tab_new_developer_address")
        new_obj_developer["phone"] = st.text_input("Телефон", key="obj_tab_new_developer_phone")
        new_obj_developer["sro_info"] = st.text_input("Данные СРО (необязательно)", key="obj_tab_new_developer_sro")

    obj_contractor_choice = st.selectbox(
        "Подрядчик",
        options=obj_contractor_options,
        format_func=lambda o: o[1],
        key="obj_tab_contractor_choice",
    )
    new_obj_contractor = {}
    if obj_contractor_choice[1] == NEW_ORG_OPTION:
        st.caption("Новая организация — подрядчик")
        new_obj_contractor["name"] = st.text_input("Название организации", key="obj_tab_new_contractor_name")
        occol1, occol2 = st.columns(2)
        with occol1:
            new_obj_contractor["inn"] = st.text_input("ИНН", key="obj_tab_new_contractor_inn")
        with occol2:
            new_obj_contractor["ogrn"] = st.text_input("ОГРН", key="obj_tab_new_contractor_ogrn")
        new_obj_contractor["address"] = st.text_input("Адрес", key="obj_tab_new_contractor_address")
        new_obj_contractor["phone"] = st.text_input("Телефон", key="obj_tab_new_contractor_phone")
        new_obj_contractor["sro_info"] = st.text_input("Данные СРО (необязательно)", key="obj_tab_new_contractor_sro")

    if st.button("Сохранить", key="obj_tab_save"):
        obj_errors = []
        if obj_object_choice[1] == OBJECT_PLACEHOLDER:
            obj_errors.append("Выберите объект или создайте новый.")
        elif obj_object_choice[1] == NEW_OBJECT_OPTION:
            if not new_obj_object["name"].strip() or not new_obj_object["address"].strip():
                obj_errors.append("Заполните все обязательные поля нового объекта.")

        if obj_developer_choice[1] == DEVELOPER_PLACEHOLDER:
            obj_errors.append("Выберите застройщика или создайте новую организацию.")
        elif obj_developer_choice[1] == NEW_ORG_OPTION:
            if not new_obj_developer["name"].strip() or not new_obj_developer["inn"].strip() \
                    or not new_obj_developer["ogrn"].strip() or not new_obj_developer["address"].strip() \
                    or not new_obj_developer["phone"].strip():
                obj_errors.append("Заполните все обязательные поля новой организации-застройщика.")

        if obj_contractor_choice[1] == CONTRACTOR_PLACEHOLDER:
            obj_errors.append("Выберите подрядчика или создайте новую организацию.")
        elif obj_contractor_choice[1] == NEW_ORG_OPTION:
            if not new_obj_contractor["name"].strip() or not new_obj_contractor["inn"].strip() \
                    or not new_obj_contractor["ogrn"].strip() or not new_obj_contractor["address"].strip() \
                    or not new_obj_contractor["phone"].strip():
                obj_errors.append("Заполните все обязательные поля новой организации-подрядчика.")

        if obj_errors:
            for err in obj_errors:
                st.error(err)
        else:
            if obj_object_choice[0] is None:
                object_name_raw = new_obj_object["name"].strip()
                object_address_raw = new_obj_object["address"].strip()
                object_id = create_object(
                    name=object_name_raw,
                    address=object_address_raw,
                )
                object_name = f"{object_name_raw}, {object_address_raw}"
                get_objects.clear()
            else:
                object_id = obj_object_choice[0]
                object_name = f"{obj_object_choice[1]}, {obj_object_choice[2]}"

            if obj_developer_choice[0] is None:
                developer_id = create_organization(
                    name=new_obj_developer["name"].strip(),
                    role="застройщик",
                    inn=new_obj_developer["inn"].strip(),
                    ogrn=new_obj_developer["ogrn"].strip(),
                    address=new_obj_developer["address"].strip(),
                    phone=new_obj_developer["phone"].strip(),
                    sro_info=new_obj_developer["sro_info"].strip(),
                )
                developer_name = new_obj_developer["name"].strip()
                get_organizations.clear()
            else:
                developer_id = obj_developer_choice[0]
                developer_name = obj_developer_choice[1]

            if obj_contractor_choice[0] is None:
                contractor_id = create_organization(
                    name=new_obj_contractor["name"].strip(),
                    role="подрядчик",
                    inn=new_obj_contractor["inn"].strip(),
                    ogrn=new_obj_contractor["ogrn"].strip(),
                    address=new_obj_contractor["address"].strip(),
                    phone=new_obj_contractor["phone"].strip(),
                    sro_info=new_obj_contractor["sro_info"].strip(),
                )
                contractor_name = new_obj_contractor["name"].strip()
                get_organizations.clear()
            else:
                contractor_id = obj_contractor_choice[0]
                contractor_name = obj_contractor_choice[1]

            update_object_org_links(object_id, developer_id, contractor_id)
            get_object_org_links.clear()

            st.session_state.current_object = {
                "object_id": object_id,
                "object_name": object_name,
                "developer_id": developer_id,
                "developer_name": developer_name,
                "contractor_id": contractor_id,
                "contractor_name": contractor_name,
            }

            for k in (
                "obj_tab_new_object_name", "obj_tab_new_object_address",
                "obj_tab_new_developer_name", "obj_tab_new_developer_inn", "obj_tab_new_developer_ogrn",
                "obj_tab_new_developer_address", "obj_tab_new_developer_phone", "obj_tab_new_developer_sro",
                "obj_tab_new_contractor_name", "obj_tab_new_contractor_inn", "obj_tab_new_contractor_ogrn",
                "obj_tab_new_contractor_address", "obj_tab_new_contractor_phone", "obj_tab_new_contractor_sro",
            ):
                st.session_state.pop(k, None)

            st.success(f"Рабочий объект сохранён: {object_name}")
            st.rerun()

    if "current_object" in st.session_state:
        cur_obj = st.session_state.current_object
        st.divider()
        st.markdown(
            f"**Текущий рабочий объект:** {cur_obj['object_name']}  \n"
            f"Застройщик: {cur_obj['developer_name']}  \n"
            f"Подрядчик: {cur_obj['contractor_name']}"
        )

        st.divider()
        st.subheader("Представители организаций")
        st.caption("Добавьте представителей застройщика и подрядчика для текущего объекта.")

        rep_org_options = [
            (cur_obj["developer_id"], f"Застройщик: {cur_obj['developer_name']}"),
            (cur_obj["contractor_id"], f"Подрядчик: {cur_obj['contractor_name']}"),
            (None, OTHER_ORG_OPTION),
        ]
        rep_org_choice = st.selectbox(
            "Организация представителя",
            options=rep_org_options,
            format_func=lambda o: o[1],
            key="rep_org_choice",
        )

        rep_organization_id = rep_org_choice[0]
        if rep_org_choice[1] == OTHER_ORG_OPTION:
            rep_all_orgs = get_all_organizations()
            rep_other_org_options = [(None, "— Выберите организацию —")] + [
                (o[0], f"{o[1]} ({o[2]})") for o in rep_all_orgs
            ]
            rep_other_org_choice = st.selectbox(
                "Организация",
                options=rep_other_org_options,
                format_func=lambda o: o[1],
                key="rep_other_org_choice",
            )
            rep_organization_id = rep_other_org_choice[0]

        rep_full_name = st.text_input("ФИО", key="rep_full_name")
        rep_position = st.text_input("Должность", key="rep_position")
        rep_col1, rep_col2 = st.columns(2)
        with rep_col1:
            rep_order_number = st.text_input("Номер приказа", key="rep_order_number")
        with rep_col2:
            rep_order_date = st.date_input("Дата приказа", value=datetime.date.today(), key="rep_order_date")
        rep_registry_number = st.text_input(
            "№ в реестре специалистов (необязательно)", key="rep_registry_number"
        )

        if st.button("Добавить представителя", key="rep_add_button"):
            rep_errors = []
            if rep_organization_id is None:
                rep_errors.append("Выберите организацию представителя.")
            if not rep_full_name.strip():
                rep_errors.append("Укажите ФИО.")
            if not rep_position.strip():
                rep_errors.append("Укажите должность.")
            if not rep_order_number.strip():
                rep_errors.append("Укажите номер приказа.")

            if rep_errors:
                for err in rep_errors:
                    st.error(err)
            else:
                create_responsible_person(
                    organization_id=rep_organization_id,
                    full_name=rep_full_name.strip(),
                    position=rep_position.strip(),
                    order_number=rep_order_number.strip(),
                    order_date=rep_order_date,
                    registry_number=rep_registry_number.strip(),
                )
                get_responsible_persons.clear()
                for k in ("rep_full_name", "rep_position", "rep_order_number", "rep_registry_number"):
                    st.session_state.pop(k, None)
                st.success(f"Представитель «{rep_full_name.strip()}» добавлен.")
                st.rerun()

        st.divider()
        st.markdown("**Уже добавленные представители**")

        rep_org_ids = [cur_obj["developer_id"], cur_obj["contractor_id"]]
        rep_persons = get_responsible_persons(rep_org_ids)

        if not rep_persons:
            st.info("Представители для этого объекта пока не добавлены.")
        else:
            rep_role_by_org = {
                cur_obj["developer_id"]: f"Застройщик: {cur_obj['developer_name']}",
                cur_obj["contractor_id"]: f"Подрядчик: {cur_obj['contractor_name']}",
            }
            for rep_person in rep_persons:
                (rep_person_id, rep_person_full_name, rep_person_position, rep_person_order_number,
                 rep_person_order_date, rep_person_registry_number, rep_person_org_id) = rep_person
                with st.container(border=True):
                    st.markdown(f"**{rep_person_full_name}** · {rep_person_position}")
                    st.caption(rep_role_by_org.get(rep_person_org_id, "Организация"))
                    rep_order_date_str = (
                        rep_person_order_date.strftime("%d.%m.%Y") if rep_person_order_date else "—"
                    )
                    st.write(f"Приказ №{rep_person_order_number} от {rep_order_date_str}")
                    if rep_person_registry_number:
                        st.write(f"№ в реестре специалистов: {rep_person_registry_number}")

with tab_chat:
    st.write("Документы сохраняются в облаке — не нужно загружать их заново каждый раз")

    # Показываем список документов прямо в интерфейсе
    doc_list = get_document_list()
    if doc_list:
        st.caption(f"📚 Документы в базе: {', '.join(doc_list)}")

    # Подключаемся к существующему индексу в Supabase при старте приложения
    if "index" not in st.session_state:
        with st.spinner("Подключаюсь к базе данных..."):
            vector_store = get_vector_store()
            st.session_state.index = VectorStoreIndex.from_vector_store(vector_store)
        if "history" not in st.session_state:
            st.session_state.history = []

    # Блок загрузки новых документов — сворачиваемый, не мешает основному чату
    with st.expander("➕ Загрузить новые документы"):
        uploaded_files = st.file_uploader(
            "Загрузи PDF документы",
            type="pdf",
            accept_multiple_files=True
        )

        if uploaded_files and st.button("Добавить в базу"):
            file_paths = []
            for uploaded_file in uploaded_files:
                file_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                file_paths.append(file_path)

            with st.spinner(f"Обрабатываю {len(file_paths)} документ(ов) и добавляю в базу..."):
                vector_store = get_vector_store()
                storage_context = StorageContext.from_defaults(vector_store=vector_store)

                reader = SimpleDirectoryReader(
                    input_files=file_paths,
                    file_extractor={".pdf": PDFReader()}
                )
                documents = reader.load_data()

                for doc in documents:
                    st.session_state.index.insert(doc)

            st.success(f"Добавлено документов: {len(uploaded_files)}")
            get_document_list.clear()
            st.rerun()

    # Основной чат
    st.divider()

    query_engine = st.session_state.index.as_query_engine(similarity_top_k=8)

    if "history" not in st.session_state:
        st.session_state.history = []

    for msg in st.session_state.history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    user_input = st.chat_input("Задай вопрос по документам...")

    if user_input:
        st.session_state.history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)

        with st.spinner("Ищу ответ..."):
            response = query_engine.query(user_input)

        answer = str(response)

        sources_text = "\n\n**Источники:**\n"
        for i, node in enumerate(response.source_nodes, 1):
            file_name = node.node.metadata.get("file_name") or node.node.metadata.get("file_path") or "источник"
            score = getattr(node, "score", None)
            raw_text = node.node.text or ""
            preview = raw_text[:150].replace("\n", " ").strip() if raw_text else "(текст недоступен)"
            score_str = f" (релевантность: {score:.2f})" if score is not None else ""
            sources_text += f"\n{i}. **{file_name}**{score_str}\n> {preview}...\n"

        full_answer = answer + sources_text

        st.session_state.history.append({"role": "assistant", "content": full_answer})
        with st.chat_message("assistant"):
            st.write(answer)
            with st.expander("📄 Показать источники"):
                st.markdown(sources_text)

with tab_new_act:
    st.subheader("Новый акт скрытых работ")

    if "current_object" not in st.session_state:
        st.info("Сначала выберите рабочий объект на вкладке «🏗️ Объект».")
    else:
        cur_obj = st.session_state.current_object
        st.markdown(f"Работаем с объектом: **{cur_obj['object_name']}**")
        if st.button("Сменить объект", key="act_change_object"):
            go_to_object_tab()
            st.rerun()

        object_id = cur_obj["object_id"]
        developer_org_id = cur_obj["developer_id"]
        contractor_org_id = cur_obj["contractor_id"]

        col1, col2 = st.columns(2)
        with col1:
            date_start = st.date_input("Дата начала работ", value=datetime.date.today())
        with col2:
            date_end = st.date_input("Дата окончания работ", value=datetime.date.today())

        # Подтягиваем записи журнала работ за период, чтобы предложить готовое описание работ.
        auto_work_name = ""
        if date_end >= date_start:
            journal_matches = get_work_journal_entries_for_period(object_id, date_start, date_end)
            if journal_matches:
                st.caption("Найденные записи журнала работ за период:")
                for entry in journal_matches:
                    entry_date, entry_location, entry_work_type, entry_description = entry
                    with st.container(border=True):
                        st.markdown(
                            f"**{entry_date.strftime('%d.%m.%Y')}** · {entry_location} · {entry_work_type}"
                        )
                        st.write(entry_description)
                auto_work_name = "; ".join(entry[3] for entry in journal_matches)
            else:
                st.warning("Записи в журнале за этот период не найдены.")

        with st.form("new_act_form", clear_on_submit=True):
            act_number = st.text_input("Номер акта")
            work_name = st.text_area(
                "Описание работ",
                value=auto_work_name,
                key=f"act_work_name_{object_id}_{date_start}_{date_end}",
            )

            st.divider()
            st.markdown("**Подписанты акта**")

            act_developer_control_persons = get_responsible_persons([developer_org_id])
            act_contractor_persons = get_responsible_persons([contractor_org_id])

            act_developer_control_person_choice = (None, None)
            if not act_developer_control_persons:
                st.info("Сначала добавьте представителя на вкладке «Объект».")
            else:
                act_developer_control_person_options = [(None, "— Выберите представителя —")] + [
                    (p[0], p[1]) for p in act_developer_control_persons
                ]
                act_developer_control_person_choice = st.selectbox(
                    "Представитель застройщика по строительному контролю",
                    options=act_developer_control_person_options,
                    format_func=lambda o: o[1],
                    key="act_developer_control_person",
                )

            act_contractor_person_choice = (None, None)
            act_contractor_control_person_choice = (None, None)
            if not act_contractor_persons:
                st.info("Сначала добавьте представителя на вкладке «Объект».")
            else:
                act_contractor_person_options = [(None, "— Выберите представителя —")] + [
                    (p[0], p[1]) for p in act_contractor_persons
                ]
                act_contractor_person_choice = st.selectbox(
                    "Представитель подрядчика",
                    options=act_contractor_person_options,
                    format_func=lambda o: o[1],
                    key="act_contractor_person",
                )
                act_contractor_control_person_choice = st.selectbox(
                    "Представитель подрядчика по строительному контролю",
                    options=act_contractor_person_options,
                    format_func=lambda o: o[1],
                    key="act_contractor_control_person",
                )

            st.markdown("**Представитель субподрядчика по строительному контролю (необязательно)**")
            act_subcontractor_orgs = get_organizations("подрядчик")
            act_subcontractor_org_options = [(None, "— Не указывать —")] + list(act_subcontractor_orgs)
            act_subcontractor_org_choice = st.selectbox(
                "Организация субподрядчика",
                options=act_subcontractor_org_options,
                format_func=lambda o: o[1],
                key="act_subcontractor_org",
            )
            act_subcontractor_control_person_choice = (None, None)
            if act_subcontractor_org_choice[0] is not None:
                act_subcontractor_persons = get_responsible_persons([act_subcontractor_org_choice[0]])
                if not act_subcontractor_persons:
                    st.info("Сначала добавьте представителя на вкладке «Объект».")
                else:
                    act_subcontractor_person_options = [(None, "— Выберите представителя —")] + [
                        (p[0], p[1]) for p in act_subcontractor_persons
                    ]
                    act_subcontractor_control_person_choice = st.selectbox(
                        "Представитель субподрядчика",
                        options=act_subcontractor_person_options,
                        format_func=lambda o: o[1],
                        key="act_subcontractor_control_person",
                    )

            st.markdown("**Представитель проектировщика по строительному контролю (необязательно)**")
            act_designer_orgs = get_organizations("проектировщик")
            act_designer_org_options = [(None, "— Не указывать —")] + list(act_designer_orgs)
            act_designer_org_choice = st.selectbox(
                "Организация проектировщика",
                options=act_designer_org_options,
                format_func=lambda o: o[1],
                key="act_designer_org",
            )
            act_designer_control_person_choice = (None, None)
            if act_designer_org_choice[0] is not None:
                act_designer_persons = get_responsible_persons([act_designer_org_choice[0]])
                if not act_designer_persons:
                    st.info("Сначала добавьте представителя на вкладке «Объект».")
                else:
                    act_designer_person_options = [(None, "— Выберите представителя —")] + [
                        (p[0], p[1]) for p in act_designer_persons
                    ]
                    act_designer_control_person_choice = st.selectbox(
                        "Представитель проектировщика",
                        options=act_designer_person_options,
                        format_func=lambda o: o[1],
                        key="act_designer_control_person",
                    )

            submitted = st.form_submit_button("Сохранить акт")

            if submitted:
                errors = []
                if not act_number.strip():
                    errors.append("Укажите номер акта.")
                if not work_name.strip():
                    errors.append("Укажите описание работ.")
                if date_end < date_start:
                    errors.append("Дата окончания не может быть раньше даты начала.")
                if act_developer_control_person_choice[0] is None:
                    errors.append(
                        "Выберите представителя застройщика по строительному контролю "
                        "(сначала добавьте представителя на вкладке «Объект»)."
                    )
                if act_contractor_person_choice[0] is None:
                    errors.append(
                        "Выберите представителя подрядчика "
                        "(сначала добавьте представителя на вкладке «Объект»)."
                    )
                if act_contractor_control_person_choice[0] is None:
                    errors.append(
                        "Выберите представителя подрядчика по строительному контролю "
                        "(сначала добавьте представителя на вкладке «Объект»)."
                    )

                if errors:
                    for err in errors:
                        st.error(err)
                else:
                    new_id = create_act(
                        object_id=object_id,
                        developer_org_id=developer_org_id,
                        contractor_org_id=contractor_org_id,
                        act_number=act_number.strip(),
                        date_start=date_start,
                        date_end=date_end,
                        act_date=date_end,
                        work_name=work_name.strip(),
                        designer_org_id=act_designer_org_choice[0],
                    )
                    create_act_signatory(
                        new_id, act_developer_control_person_choice[0], "застройщик, строительный контроль"
                    )
                    create_act_signatory(new_id, act_contractor_person_choice[0], "подрядчик")
                    create_act_signatory(
                        new_id, act_contractor_control_person_choice[0], "подрядчик, строительный контроль"
                    )
                    if act_subcontractor_control_person_choice[0] is not None:
                        create_act_signatory(
                            new_id, act_subcontractor_control_person_choice[0], "субподрядчик, строительный контроль"
                        )
                    if act_designer_control_person_choice[0] is not None:
                        create_act_signatory(
                            new_id, act_designer_control_person_choice[0], "проектировщик, строительный контроль"
                        )
                    st.success(f"Акт №{act_number} сохранён (id={new_id}).")
                    st.rerun()
with tab_journal:
    st.subheader("Общий журнал работ")

    if "current_object" not in st.session_state:
        st.info("Сначала выберите рабочий объект на вкладке «🏗️ Объект».")
    else:
        cur_obj = st.session_state.current_object
        st.markdown(f"Работаем с объектом: **{cur_obj['object_name']}**")
        if st.button("Сменить объект", key="journal_change_object"):
            go_to_object_tab()
            st.rerun()

        journal_object_id = cur_obj["object_id"]
        journal_object_name = cur_obj["object_name"]

        with st.form("new_journal_entry_form", clear_on_submit=True):
            work_date = st.date_input("Дата работ", value=datetime.date.today())
            location = st.text_input("Место проведения работ")
            work_type = st.text_input("Вид работ")
            description = st.text_area("Подробное описание")

            journal_submitted = st.form_submit_button("Добавить запись")

            if journal_submitted:
                journal_errors = []
                if not location.strip():
                    journal_errors.append("Укажите место проведения работ.")
                if not work_type.strip():
                    journal_errors.append("Укажите вид работ.")
                if not description.strip():
                    journal_errors.append("Укажите подробное описание.")

                if journal_errors:
                    for err in journal_errors:
                        st.error(err)
                else:
                    create_work_journal_entry(
                        object_id=journal_object_id,
                        work_date=work_date,
                        location=location.strip(),
                        work_type=work_type.strip(),
                        description=description.strip(),
                    )
                    st.success("Запись добавлена в журнал работ.")
                    get_work_journal_entries.clear()
                    get_work_journal_entries_for_period.clear()
                    st.rerun()

        st.divider()
        st.markdown(f"**Последние записи по объекту «{journal_object_name}»**")

        journal_entries = get_work_journal_entries(journal_object_id)
        if journal_entries:
            for entry in journal_entries:
                entry_date, entry_location, entry_work_type, entry_description = entry
                with st.container(border=True):
                    st.markdown(
                        f"**{entry_date.strftime('%d.%m.%Y')}** · {entry_location} · {entry_work_type}"
                    )
                    st.write(entry_description)
        else:
            st.info("Записей по этому объекту пока нет.")