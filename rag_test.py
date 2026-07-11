from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.llms.anthropic import Anthropic
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import Settings
from llama_index.readers.file import PDFReader
from dotenv import load_dotenv

load_dotenv()

Settings.llm = Anthropic(model="claude-sonnet-4-6")
Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")

print("Загружаю документы...")
reader = SimpleDirectoryReader("documents", file_extractor={".pdf": PDFReader()})
documents = reader.load_data()
print(f"Загружено документов: {len(documents)}")

print("Строю индекс...")
index = VectorStoreIndex.from_documents(documents)

query_engine = index.as_query_engine(similarity_top_k=8)

print("\nГотово! Задавай вопросы (напиши 'выход' чтобы остановить)\n")

while True:
    question = input("Вопрос: ")
    if question == "выход":
        break
    
    response = query_engine.query(question)
    print(f"\nОтвет: {response}\n")