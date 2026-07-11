import streamlit as st
import os
import hashlib
from llama_index.core import (
    VectorStoreIndex, SimpleDirectoryReader, Settings,
    StorageContext, load_index_from_storage
)
from llama_index.llms.anthropic import Anthropic
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.readers.file import PDFReader
from dotenv import load_dotenv

load_dotenv()

Settings.llm = Anthropic(model="claude-sonnet-4-6")
Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")

st.title("Помощник ПТО-инженера")
st.write("Загрузи один или несколько PDF-документов и задавай вопросы")

UPLOAD_DIR = "uploaded_docs"
INDEX_DIR = "saved_indexes"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(INDEX_DIR, exist_ok=True)

uploaded_files = st.file_uploader(
    "Загрузи PDF документы",
    type="pdf",
    accept_multiple_files=True
)

if uploaded_files:
    file_names = sorted([f.name for f in uploaded_files])
    
    # Уникальный "отпечаток" для этого набора файлов
    combo_key = hashlib.md5("_".join(file_names).encode()).hexdigest()[:10]
    index_path = os.path.join(INDEX_DIR, combo_key)
    
    file_paths = []
    for uploaded_file in uploaded_files:
        file_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        file_paths.append(file_path)
    
    st.success(f"Загружено файлов: {len(uploaded_files)} — {', '.join(file_names)}")
    
    if "index" not in st.session_state or st.session_state.get("current_files") != file_names:
        
        if os.path.exists(index_path):
            # Индекс уже был построен раньше — просто загружаем
            with st.spinner("Загружаю сохранённый индекс..."):
                storage_context = StorageContext.from_defaults(persist_dir=index_path)
                st.session_state.index = load_index_from_storage(storage_context)
            st.success("Индекс загружен из кеша (мгновенно, без пересчёта)!")
        else:
            # Строим индекс впервые и сохраняем на будущее
            with st.spinner(f"Обрабатываю {len(file_paths)} документ(ов) впервые..."):
                reader = SimpleDirectoryReader(
                    input_files=file_paths,
                    file_extractor={".pdf": PDFReader()}
                )
                documents = reader.load_data()
                st.session_state.index = VectorStoreIndex.from_documents(documents)
                st.session_state.index.storage_context.persist(persist_dir=index_path)
            st.success("Документы обработаны и сохранены в кеш!")
        
        st.session_state.current_files = file_names
        st.session_state.history = []

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
            file_name = node.node.metadata.get("file_name", "неизвестный файл")
            score = node.score if hasattr(node, "score") else None
            preview = node.node.text[:150].replace("\n", " ")
            score_str = f" (релевантность: {score:.2f})" if score else ""
            sources_text += f"\n{i}. **{file_name}**{score_str}\n> {preview}...\n"
        
        full_answer = answer + sources_text
        
        st.session_state.history.append({"role": "assistant", "content": full_answer})
        with st.chat_message("assistant"):
            st.write(answer)
            with st.expander("📄 Показать источники"):
                st.markdown(sources_text)
else:
    st.info("Загрузи один или несколько PDF документов чтобы начать")