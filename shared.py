from collections import Counter

import streamlit as st

from session_cleanup import delete_tracked_rows

TAB_OBJECT_LABEL = "🏗️ Объект"

NEW_ORG_OPTION = "➕ Добавить новую организацию"

TRACKABLE_TABLES = {
    "objects", "organizations", "organization_roles", "responsible_persons",
    "acts", "act_signatories", "materials",
    "registries", "registry_documents",
    "commission_acts", "commission_act_signatories",
    "work_journal",
    "pending_requests",
}


NEW_ORG_KEY_SUFFIXES = ("name", "inn", "ogrn", "address", "phone", "sro")
NEW_ORG_REQUIRED_FIELDS = ("name", "inn", "ogrn", "address", "phone")


def render_new_org_fields(key_prefix, caption):
    """Поля формы новой организации. Ключи виджетов: {key_prefix}_name, _inn,
    _ogrn, _address, _phone, _sro. Возвращает dict со значениями полей."""
    st.caption(caption)
    org = {}
    org["name"] = st.text_input("Название организации", key=f"{key_prefix}_name")
    inn_col, ogrn_col = st.columns(2)
    with inn_col:
        org["inn"] = st.text_input("ИНН", key=f"{key_prefix}_inn")
    with ogrn_col:
        org["ogrn"] = st.text_input("ОГРН", key=f"{key_prefix}_ogrn")
    org["address"] = st.text_input("Адрес", key=f"{key_prefix}_address")
    org["phone"] = st.text_input("Телефон", key=f"{key_prefix}_phone")
    org["sro_info"] = st.text_input("Данные СРО (необязательно)", key=f"{key_prefix}_sro")
    return org


def new_org_required_filled(org):
    return all(org[field].strip() for field in NEW_ORG_REQUIRED_FIELDS)


def new_org_widget_keys(key_prefix):
    return [f"{key_prefix}_{suffix}" for suffix in NEW_ORG_KEY_SUFFIXES]


def go_to_object_tab():
    st.session_state.force_tab = TAB_OBJECT_LABEL
    st.session_state.tabs_key_counter += 1


def track_created(table, key):
    """Запоминает созданную за эту сессию строку (table + поля для точного WHERE),
    чтобы её можно было безопасно удалить позже кнопкой отмены тестовой сессии."""
    assert table in TRACKABLE_TABLES, f"unknown trackable table: {table}"
    st.session_state.setdefault("session_created", []).append({"table": table, "key": dict(key)})


def render_session_cleanup_panel():
    created = st.session_state.get("session_created", [])
    if not created:
        return

    counts = Counter(entry["table"] for entry in created)
    summary = ", ".join(f"{table}: {count}" for table, count in counts.items())

    with st.expander(f"🧹 Тестовые данные этой сессии ({len(created)})"):
        st.caption(summary)
        for entry in created:
            st.text(f"{entry['table']}  {entry['key']}")

        if st.button("Удалить тестовые данные этой сессии", key="session_cleanup_btn"):
            st.session_state.session_cleanup_confirm = True

        if st.session_state.get("session_cleanup_confirm"):
            st.warning(f"Удалить {len(created)} записей ({summary})? Действие необратимо.")
            confirm_col, cancel_col = st.columns(2)
            if confirm_col.button("Да, удалить", key="session_cleanup_confirm_yes"):
                delete_tracked_rows(created)
                st.cache_data.clear()
                st.session_state.session_created = []
                st.session_state.session_cleanup_confirm = False
                st.success("Тестовые данные этой сессии удалены.")
                st.rerun()
            if cancel_col.button("Отмена", key="session_cleanup_confirm_no"):
                st.session_state.session_cleanup_confirm = False
                st.rerun()
