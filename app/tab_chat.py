import os

import streamlit as st
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings, StorageContext
from llama_index.llms.anthropic import Anthropic
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.readers.file import PDFReader
from llama_index.vector_stores.supabase import SupabaseVectorStore

from app.db import get_connection_string
from app.cache import get_document_list
from app.documents import RAG_COLLECTION_NAME

# Мультиязычная модель: нормативные документы (СП, ГОСТы) на русском.
# Размерность вектора 384, лимит модели — 512 токенов на фрагмент.
EMBED_MODEL_NAME = "intfloat/multilingual-e5-small"
EMBED_DIMENSION = 384
# Размер фрагмента в токенах LlamaIndex. Русский текст при 512 таких
# токенах укладывается в лимит модели с запасом; при дефолтных 1024
# хвост фрагмента обрезался бы и не попадал в вектор.
CHUNK_SIZE = 512
CHUNK_OVERLAP = 64

UPLOAD_DIR = "uploaded_docs"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def get_vector_store():
    return SupabaseVectorStore(
        postgres_connection_string=get_connection_string(),
        collection_name=RAG_COLLECTION_NAME,
        dimension=EMBED_DIMENSION,
    )


@st.cache_resource
def configure_llm_settings():
    Settings.llm = Anthropic(model="claude-sonnet-5")
    # Модели семейства E5 обучены с префиксами: без них качество поиска падает.
    Settings.embed_model = HuggingFaceEmbedding(
        model_name=EMBED_MODEL_NAME,
        query_instruction="query: ",
        text_instruction="passage: ",
    )
    Settings.chunk_size = CHUNK_SIZE
    Settings.chunk_overlap = CHUNK_OVERLAP


configure_llm_settings()


def render():
    st.write("Документы сохраняются в облаке — не нужно загружать их заново каждый раз")

    # Показываем список документов прямо в интерфейсе
    doc_list = get_document_list()
    if doc_list:
        st.caption(f"📚 Документы в базе: {', '.join(doc_list)}")
    else:
        st.info("В базе пока нет документов — загрузите PDF ниже, чтобы задавать по ним вопросы.")

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
