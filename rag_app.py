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


@st.cache_resource
def configure_llm_settings():
    Settings.llm = Anthropic(model="claude-sonnet-4-6")
    Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")


configure_llm_settings()

st.title("Помощник инженера ПТО")
st.write("Документы сохраняются в облаке — не нужно загружать их заново каждый раз")

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
    cur.execute("SELECT id, name FROM objects ORDER BY name;")
    objects = cur.fetchall()
    cur.close()
    conn.close()
    return objects


@st.cache_data(ttl=60)
def get_organizations(role):
    conn = psycopg2.connect(SUPABASE_CONNECTION)
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM organizations WHERE role = %s ORDER BY name;", (role,))
    orgs = cur.fetchall()
    cur.close()
    conn.close()
    return orgs


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


def create_act(object_id, developer_org_id, contractor_org_id, act_number, date_start, date_end, work_name):
    conn = psycopg2.connect(SUPABASE_CONNECTION)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO acts (object_id, developer_org_id, contractor_org_id, act_number, date_start, date_end, work_name)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
        """,
        (object_id, developer_org_id, contractor_org_id, act_number, date_start, date_end, work_name),
    )
    new_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return new_id


tab_chat, tab_new_act = st.tabs(["💬 Чат по документам", "📝 Новый акт скрытых работ"])

with tab_chat:
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

    NEW_ORG_OPTION = "➕ Добавить новую организацию"

    objects = get_objects()
    developers = get_organizations("застройщик")
    contractors = get_organizations("подрядчик")

    if not objects:
        st.warning("В таблице objects нет объектов. Сначала добавьте объект.")
    else:
        developer_options = list(developers) + [(None, NEW_ORG_OPTION)]
        contractor_options = list(contractors) + [(None, NEW_ORG_OPTION)]

        # Выбор застройщика/подрядчика вынесен за пределы формы, чтобы выбор
        # опции "Добавить новую организацию" сразу показывал доп. поля.
        developer_choice = st.selectbox(
            "Застройщик",
            options=developer_options,
            format_func=lambda o: o[1],
        )
        new_developer = {}
        if developer_choice[0] is None:
            st.caption("Новая организация — застройщик")
            new_developer["name"] = st.text_input("Название организации", key="new_developer_name")
            dcol1, dcol2 = st.columns(2)
            with dcol1:
                new_developer["inn"] = st.text_input("ИНН", key="new_developer_inn")
            with dcol2:
                new_developer["ogrn"] = st.text_input("ОГРН", key="new_developer_ogrn")
            new_developer["address"] = st.text_input("Адрес", key="new_developer_address")
            new_developer["phone"] = st.text_input("Телефон", key="new_developer_phone")
            new_developer["sro_info"] = st.text_input("Данные СРО (необязательно)", key="new_developer_sro")

        contractor_choice = st.selectbox(
            "Подрядчик",
            options=contractor_options,
            format_func=lambda o: o[1],
        )
        new_contractor = {}
        if contractor_choice[0] is None:
            st.caption("Новая организация — подрядчик")
            new_contractor["name"] = st.text_input("Название организации", key="new_contractor_name")
            ccol1, ccol2 = st.columns(2)
            with ccol1:
                new_contractor["inn"] = st.text_input("ИНН", key="new_contractor_inn")
            with ccol2:
                new_contractor["ogrn"] = st.text_input("ОГРН", key="new_contractor_ogrn")
            new_contractor["address"] = st.text_input("Адрес", key="new_contractor_address")
            new_contractor["phone"] = st.text_input("Телефон", key="new_contractor_phone")
            new_contractor["sro_info"] = st.text_input("Данные СРО (необязательно)", key="new_contractor_sro")

        with st.form("new_act_form", clear_on_submit=True):
            object_choice = st.selectbox(
                "Объект",
                options=objects,
                format_func=lambda o: o[1],
            )
            act_number = st.text_input("Номер акта")
            col1, col2 = st.columns(2)
            with col1:
                date_start = st.date_input("Дата начала работ", value=datetime.date.today())
            with col2:
                date_end = st.date_input("Дата окончания работ", value=datetime.date.today())
            work_name = st.text_area("Описание работ")

            submitted = st.form_submit_button("Сохранить акт")

            if submitted:
                errors = []
                if not act_number.strip():
                    errors.append("Укажите номер акта.")
                if not work_name.strip():
                    errors.append("Укажите описание работ.")
                if date_end < date_start:
                    errors.append("Дата окончания не может быть раньше даты начала.")

                if developer_choice[0] is None:
                    if not new_developer["name"].strip() or not new_developer["inn"].strip() \
                            or not new_developer["ogrn"].strip() or not new_developer["address"].strip() \
                            or not new_developer["phone"].strip():
                        errors.append("Заполните все обязательные поля новой организации-застройщика.")

                if contractor_choice[0] is None:
                    if not new_contractor["name"].strip() or not new_contractor["inn"].strip() \
                            or not new_contractor["ogrn"].strip() or not new_contractor["address"].strip() \
                            or not new_contractor["phone"].strip():
                        errors.append("Заполните все обязательные поля новой организации-подрядчика.")

                if errors:
                    for err in errors:
                        st.error(err)
                else:
                    if developer_choice[0] is None:
                        developer_org_id = create_organization(
                            name=new_developer["name"].strip(),
                            role="застройщик",
                            inn=new_developer["inn"].strip(),
                            ogrn=new_developer["ogrn"].strip(),
                            address=new_developer["address"].strip(),
                            phone=new_developer["phone"].strip(),
                            sro_info=new_developer["sro_info"].strip(),
                        )
                    else:
                        developer_org_id = developer_choice[0]

                    if contractor_choice[0] is None:
                        contractor_org_id = create_organization(
                            name=new_contractor["name"].strip(),
                            role="подрядчик",
                            inn=new_contractor["inn"].strip(),
                            ogrn=new_contractor["ogrn"].strip(),
                            address=new_contractor["address"].strip(),
                            phone=new_contractor["phone"].strip(),
                            sro_info=new_contractor["sro_info"].strip(),
                        )
                    else:
                        contractor_org_id = contractor_choice[0]

                    new_id = create_act(
                        object_id=object_choice[0],
                        developer_org_id=developer_org_id,
                        contractor_org_id=contractor_org_id,
                        act_number=act_number.strip(),
                        date_start=date_start,
                        date_end=date_end,
                        work_name=work_name.strip(),
                    )
                    st.success(f"Акт №{act_number} сохранён (id={new_id}).")

                    if developer_choice[0] is None or contractor_choice[0] is None:
                        get_organizations.clear()

                    for k in (
                        "new_developer_name", "new_developer_inn", "new_developer_ogrn",
                        "new_developer_address", "new_developer_phone", "new_developer_sro",
                        "new_contractor_name", "new_contractor_inn", "new_contractor_ogrn",
                        "new_contractor_address", "new_contractor_phone", "new_contractor_sro",
                    ):
                        st.session_state.pop(k, None)
                    st.rerun()