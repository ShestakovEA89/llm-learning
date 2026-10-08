from db import get_db_connection

# Коллекция векторов RAG-чата в схеме vecs. Имя привязано к модели
# эмбеддингов: векторы разных моделей несовместимы, поэтому при смене
# модели заводится новая коллекция, а старая остаётся нетронутой.
RAG_COLLECTION_NAME = "pto_documents_e5"


def get_document_list():
    try:
        with get_db_connection() as cur:
            cur.execute(
                f"SELECT DISTINCT metadata->>'file_name' FROM vecs.{RAG_COLLECTION_NAME};"
            )
            return [row[0] for row in cur.fetchall() if row[0]]
    except Exception:
        return []
