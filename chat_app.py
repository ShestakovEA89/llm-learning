import streamlit as st
import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic()

SYSTEM_PROMPT = """Ты — помощник инженера проектно-технического отдела. 
Твоя задача — отвечать на вопросы о проектной и исполнительной документации, документах на применяемые материалы, оборудование, сертификаты, строительные нормы и правила, а также других вопросах, связанных с проектированием и строительством.
Отвечай чётко и по делу. Используй профессиональную терминологию но объясняй сложные термины.
Если вопрос не связан со строительством — вежливо направь пользователя к теме."""

st.title("Строительный ассистент")

if "history" not in st.session_state:
    st.session_state.history = []

for message in st.session_state.history:
    with st.chat_message(message["role"]):
        st.write(message["content"])

user_input = st.chat_input("Задай вопрос по строительству...")

if user_input:
    st.session_state.history.append({"role": "user", "content": user_input})
    
    with st.chat_message("user"):
        st.write(user_input)

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        temperature=0.3,
        system=SYSTEM_PROMPT,
        messages=st.session_state.history
    )
    
    answer = ""
    for block in response.content:
        if block.type == "text":
            answer = block.text
            break
    st.session_state.history.append({"role": "assistant", "content": answer})
    
    with st.chat_message("assistant"):
        st.write(answer)