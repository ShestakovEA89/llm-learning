import streamlit as st

TAB_OBJECT_LABEL = "🏗️ Объект"

NEW_ORG_OPTION = "➕ Добавить новую организацию"


def go_to_object_tab():
    st.session_state.force_tab = TAB_OBJECT_LABEL
    st.session_state.tabs_key_counter += 1
