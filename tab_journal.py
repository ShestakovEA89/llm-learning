import datetime
import traceback

import streamlit as st

from journal import create_work_journal_entry
from cache import get_work_journal_entries, get_work_journal_entries_for_period
from shared import go_to_object_tab, track_created


def render():
    st.subheader("Общий журнал работ")

    if "current_object" not in st.session_state:
        st.info("Сначала выберите рабочий объект на вкладке «🏗️ Объект».")
    else:
        cur_obj = st.session_state.current_object
        st.markdown(f"Работаем с объектом: **{cur_obj['object_name']}**")
        if st.button("Сменить объект", key="journal_change_object"):
            go_to_object_tab()
            st.rerun()

        journal_object_id = cur_obj["object_id"]
        journal_object_name = cur_obj["object_name"]

        with st.form("new_journal_entry_form", clear_on_submit=True):
            work_date = st.date_input("Дата работ", value=datetime.date.today())
            location = st.text_input("Место проведения работ")
            work_type = st.text_input("Вид работ")
            description = st.text_area("Подробное описание")

            journal_submitted = st.form_submit_button("Добавить запись")

            if journal_submitted:
                journal_errors = []
                if not location.strip():
                    journal_errors.append("Укажите место проведения работ.")
                if not work_type.strip():
                    journal_errors.append("Укажите вид работ.")
                if not description.strip():
                    journal_errors.append("Укажите подробное описание.")

                if journal_errors:
                    for err in journal_errors:
                        st.error(err)
                else:
                    journal_save_ok = True
                    try:
                        new_journal_id = create_work_journal_entry(
                            object_id=journal_object_id,
                            work_date=work_date,
                            location=location.strip(),
                            work_type=work_type.strip(),
                            description=description.strip(),
                        )
                        track_created("work_journal", {"id": new_journal_id})
                    except Exception as db_exc:
                        journal_save_ok = False
                        print(f"[DB ERROR] Не удалось сохранить запись журнала работ: {db_exc}")
                        traceback.print_exc()
                        st.error(
                            "Не удалось сохранить запись в журнале работ. "
                            "Проверьте соединение с базой данных и попробуйте ещё раз."
                        )

                    if journal_save_ok:
                        st.success("Запись добавлена в журнал работ.")
                        get_work_journal_entries.clear()
                        get_work_journal_entries_for_period.clear()
                        st.rerun()

        st.divider()
        st.markdown(f"**Последние записи по объекту «{journal_object_name}»**")

        journal_entries = get_work_journal_entries(journal_object_id)
        if journal_entries:
            for entry in journal_entries:
                entry_date, entry_location, entry_work_type, entry_description = entry
                with st.container(border=True):
                    st.markdown(
                        f"**{entry_date.strftime('%d.%m.%Y')}** · {entry_location} · {entry_work_type}"
                    )
                    st.write(entry_description)
        else:
            st.info("Записей по этому объекту пока нет.")
