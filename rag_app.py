import streamlit as st
from dotenv import load_dotenv
from shared import TAB_OBJECT_LABEL
import tab_journal
import tab_object
import tab_new_act
import tab_commission_acts
import tab_chat

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


st.title("Помощник инженера ПТО")

TAB_JOURNAL_LABEL = "📓 Журнал работ"
TAB_NEW_ACT_LABEL = "📝 Новый акт скрытых работ"
TAB_COMMISSION_ACTS_LABEL = "📋 Комиссионные акты"
TAB_CHAT_LABEL = "💬 Чат по документам"

if "tabs_key_counter" not in st.session_state:
    st.session_state.tabs_key_counter = 0
if "force_tab" not in st.session_state:
    st.session_state.force_tab = None


object_tab, journal_tab, new_act_tab, commission_acts_tab, chat_tab = st.tabs(
    [TAB_OBJECT_LABEL, TAB_JOURNAL_LABEL, TAB_NEW_ACT_LABEL, TAB_COMMISSION_ACTS_LABEL, TAB_CHAT_LABEL],
    default=st.session_state.force_tab,
    key=f"main_tabs_{st.session_state.tabs_key_counter}",
)

with object_tab:
    tab_object.render()

with chat_tab:
    tab_chat.render()

with new_act_tab:
    tab_new_act.render()

with commission_acts_tab:
    tab_commission_acts.render()

with journal_tab:
    tab_journal.render()