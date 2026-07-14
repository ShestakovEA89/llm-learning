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

Settings.llm = Anthropic(model="claude-sonnet-4-6")
Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")

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


def get_objects():
    conn = psycopg2.connect(SUPABASE_CONNECTION)
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM objects ORDER BY name;")
    objects = cur.fetchall()
    cur.close()
    conn.close()
    return objects


def get_organizations(role):
    conn = psycopg2.connect(SUPABASE_CONNECTION)
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM organizations WHERE role = %s ORDER BY name;", (role,))
    orgs = cur.fetchall()
    cur.close()
    conn.close()
    return orgs


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

    objects = get_objects()
    developers = get_organizations("застройщик")
    contractors = get_organizations("подрядчик")

    if not objects:
        st.warning("В таблице objects нет объектов. Сначала добавьте объект.")
    elif not developers or not contractors:
        st.warning("В таблице organizations должны быть организации с ролью «застройщик» и «подрядчик».")
    else:
        with st.form("new_act_form", clear_on_submit=True):
            object_choice = st.selectbox(
                "Объект",
                options=objects,
                format_func=lambda o: o[1],
            )
            developer_choice = st.selectbox(
                "Застройщик",
                options=developers,
                format_func=lambda o: o[1],
            )
            contractor_choice = st.selectbox(
                "Подрядчик",
                options=contractors,
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
                if not act_number.strip():
                    st.error("Укажите номер акта.")
                elif not work_name.strip():
                    st.error("Укажите описание работ.")
                elif date_end < date_start:
                    st.error("Дата окончания не может быть раньше даты начала.")
                else:
                    new_id = create_act(
                        object_id=object_choice[0],
                        developer_org_id=developer_choice[0],
                        contractor_org_id=contractor_choice[0],
                        act_number=act_number.strip(),
                        date_start=date_start,
                        date_end=date_end,
                        work_name=work_name.strip(),
                    )
                    st.success(f"Акт №{act_number} сохранён (id={new_id}).")