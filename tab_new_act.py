import datetime
import io
import traceback

import streamlit as st

from generate_act_final import generate_act as generate_act_docx
from acts import create_act, create_act_signatory, create_material
from cache import (
    get_organizations,
    get_responsible_persons,
    get_acts_for_object,
    get_materials_for_act,
    get_work_journal_entries_for_period,
)
from shared import go_to_object_tab


def render():
    st.subheader("Новый акт скрытых работ")

    if "current_object" not in st.session_state:
        st.info("Сначала выберите рабочий объект на вкладке «🏗️ Объект».")
    else:
        cur_obj = st.session_state.current_object
        st.markdown(f"Работаем с объектом: **{cur_obj['object_name']}**")
        if st.button("Сменить объект", key="act_change_object"):
            go_to_object_tab()
            st.rerun()

        object_id = cur_obj["object_id"]
        developer_org_id = cur_obj["developer_id"]
        contractor_org_id = cur_obj["contractor_id"]

        col1, col2 = st.columns(2)
        with col1:
            date_start = st.date_input("Дата начала работ", value=datetime.date.today())
        with col2:
            date_end = st.date_input("Дата окончания работ", value=datetime.date.today())

        # Подтягиваем записи журнала работ за период, чтобы предложить готовое описание работ.
        auto_work_name = ""
        if date_end >= date_start:
            journal_matches = get_work_journal_entries_for_period(object_id, date_start, date_end)
            if journal_matches:
                st.caption("Найденные записи журнала работ за период:")
                for entry in journal_matches:
                    entry_date, entry_location, entry_work_type, entry_description = entry
                    with st.container(border=True):
                        st.markdown(
                            f"**{entry_date.strftime('%d.%m.%Y')}** · {entry_location} · {entry_work_type}"
                        )
                        st.write(entry_description)
                auto_work_name = "; ".join(entry[3] for entry in journal_matches)
            else:
                st.warning("Записи в журнале за этот период не найдены.")

        with st.form("new_act_form", clear_on_submit=True):
            act_number = st.text_input("Номер акта")
            work_name = st.text_area(
                "Описание работ",
                value=auto_work_name,
                key=f"act_work_name_{object_id}_{date_start}_{date_end}",
            )
            project_docs_ref = st.text_area("Шифр проектной документации", key="act_project_docs_ref")
            normative_docs = st.text_area("Нормативные документы", key="act_normative_docs")
            supporting_docs = st.text_area("Прилагаемые документы", key="act_supporting_docs")

            st.divider()
            st.markdown("**Подписанты акта**")

            act_developer_control_persons = get_responsible_persons([developer_org_id])
            act_contractor_persons = get_responsible_persons([contractor_org_id])

            act_developer_control_person_choice = (None, None)
            if not act_developer_control_persons:
                st.info("Сначала добавьте представителя на вкладке «Объект».")
            else:
                act_developer_control_person_options = [(None, "— Выберите представителя —")] + [
                    (p[0], p[1]) for p in act_developer_control_persons
                ]
                act_developer_control_person_choice = st.selectbox(
                    "Представитель застройщика по строительному контролю",
                    options=act_developer_control_person_options,
                    format_func=lambda o: o[1],
                    key="act_developer_control_person",
                )

            act_contractor_person_choice = (None, None)
            act_contractor_control_person_choice = (None, None)
            if not act_contractor_persons:
                st.info("Сначала добавьте представителя на вкладке «Объект».")
            else:
                act_contractor_person_options = [(None, "— Выберите представителя —")] + [
                    (p[0], p[1]) for p in act_contractor_persons
                ]
                act_contractor_person_choice = st.selectbox(
                    "Представитель подрядчика",
                    options=act_contractor_person_options,
                    format_func=lambda o: o[1],
                    key="act_contractor_person",
                )
                act_contractor_control_person_choice = st.selectbox(
                    "Представитель подрядчика по строительному контролю",
                    options=act_contractor_person_options,
                    format_func=lambda o: o[1],
                    key="act_contractor_control_person",
                )

            st.markdown("**Представитель субподрядчика по строительному контролю (необязательно)**")
            act_subcontractor_orgs = get_organizations("подрядчик")
            act_subcontractor_org_options = [(None, "— Не указывать —")] + list(act_subcontractor_orgs)
            act_subcontractor_org_choice = st.selectbox(
                "Организация субподрядчика",
                options=act_subcontractor_org_options,
                format_func=lambda o: o[1],
                key="act_subcontractor_org",
            )
            act_subcontractor_control_person_choice = (None, None)
            if act_subcontractor_org_choice[0] is not None:
                act_subcontractor_persons = get_responsible_persons([act_subcontractor_org_choice[0]])
                if not act_subcontractor_persons:
                    st.info("Сначала добавьте представителя на вкладке «Объект».")
                else:
                    act_subcontractor_person_options = [(None, "— Выберите представителя —")] + [
                        (p[0], p[1]) for p in act_subcontractor_persons
                    ]
                    act_subcontractor_control_person_choice = st.selectbox(
                        "Представитель субподрядчика",
                        options=act_subcontractor_person_options,
                        format_func=lambda o: o[1],
                        key="act_subcontractor_control_person",
                    )

            st.markdown("**Представитель проектировщика по строительному контролю (необязательно)**")
            act_designer_orgs = get_organizations("проектировщик")
            act_designer_org_options = [(None, "— Не указывать —")] + list(act_designer_orgs)
            act_designer_org_choice = st.selectbox(
                "Организация проектировщика",
                options=act_designer_org_options,
                format_func=lambda o: o[1],
                key="act_designer_org",
            )
            act_designer_control_person_choice = (None, None)
            if act_designer_org_choice[0] is not None:
                act_designer_persons = get_responsible_persons([act_designer_org_choice[0]])
                if not act_designer_persons:
                    st.info("Сначала добавьте представителя на вкладке «Объект».")
                else:
                    act_designer_person_options = [(None, "— Выберите представителя —")] + [
                        (p[0], p[1]) for p in act_designer_persons
                    ]
                    act_designer_control_person_choice = st.selectbox(
                        "Представитель проектировщика",
                        options=act_designer_person_options,
                        format_func=lambda o: o[1],
                        key="act_designer_control_person",
                    )

            submitted = st.form_submit_button("Сохранить акт")

            if submitted:
                errors = []
                if not act_number.strip():
                    errors.append("Укажите номер акта.")
                if not work_name.strip():
                    errors.append("Укажите описание работ.")
                if date_end < date_start:
                    errors.append("Дата окончания не может быть раньше даты начала.")
                if act_developer_control_person_choice[0] is None:
                    errors.append(
                        "Выберите представителя застройщика по строительному контролю "
                        "(сначала добавьте представителя на вкладке «Объект»)."
                    )
                if act_contractor_person_choice[0] is None:
                    errors.append(
                        "Выберите представителя подрядчика "
                        "(сначала добавьте представителя на вкладке «Объект»)."
                    )
                if act_contractor_control_person_choice[0] is None:
                    errors.append(
                        "Выберите представителя подрядчика по строительному контролю "
                        "(сначала добавьте представителя на вкладке «Объект»)."
                    )

                if errors:
                    for err in errors:
                        st.error(err)
                else:
                    act_save_ok = True
                    try:
                        new_id = create_act(
                            object_id=object_id,
                            developer_org_id=developer_org_id,
                            contractor_org_id=contractor_org_id,
                            act_number=act_number.strip(),
                            date_start=date_start,
                            date_end=date_end,
                            act_date=date_end,
                            work_name=work_name.strip(),
                            designer_org_id=act_designer_org_choice[0],
                            project_docs_ref=project_docs_ref.strip() or None,
                            normative_docs=normative_docs.strip() or None,
                            supporting_docs=supporting_docs.strip() or None,
                        )
                        create_act_signatory(
                            new_id, act_developer_control_person_choice[0], "застройщик, строительный контроль"
                        )
                        create_act_signatory(new_id, act_contractor_person_choice[0], "подрядчик")
                        create_act_signatory(
                            new_id, act_contractor_control_person_choice[0], "подрядчик, строительный контроль"
                        )
                        if act_subcontractor_control_person_choice[0] is not None:
                            create_act_signatory(
                                new_id, act_subcontractor_control_person_choice[0], "субподрядчик, строительный контроль"
                            )
                        if act_designer_control_person_choice[0] is not None:
                            create_act_signatory(
                                new_id, act_designer_control_person_choice[0], "проектировщик, строительный контроль"
                            )
                    except Exception as db_exc:
                        act_save_ok = False
                        print(f"[DB ERROR] Не удалось сохранить акт №{act_number.strip()}: {db_exc}")
                        traceback.print_exc()
                        st.error(
                            "Не удалось сохранить акт. "
                            "Проверьте соединение с базой данных и попробуйте ещё раз."
                        )

                    if act_save_ok:
                        st.session_state.current_act = {
                            "act_id": new_id,
                            "act_number": act_number.strip(),
                        }
                        st.success(f"Акт №{act_number} сохранён (id={new_id}).")
                        st.rerun()

        if "current_act" in st.session_state:
            cur_act = st.session_state.current_act

            st.divider()
            st.subheader("Скачать акт")
            cur_act_docx_key = f"act_docx_bytes_{cur_act['act_id']}"
            if st.button("Подготовить .docx", key=f"prepare_act_{cur_act['act_id']}"):
                act_docx_buffer = io.BytesIO()
                generate_act_docx(cur_act["act_id"], act_docx_buffer)
                st.session_state[cur_act_docx_key] = act_docx_buffer.getvalue()
            if cur_act_docx_key in st.session_state:
                st.download_button(
                    "Скачать акт .docx",
                    data=st.session_state[cur_act_docx_key],
                    file_name=f"Акт_{cur_act['act_number']}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    key=f"download_act_{cur_act['act_id']}",
                )

            st.divider()
            st.subheader("Добавить материалы")
            st.caption(f"Материалы для акта №{cur_act['act_number']} (id={cur_act['act_id']}).")

            with st.form(f"add_material_form_{cur_act['act_id']}", clear_on_submit=True):
                material_name = st.text_input("Название материала", key="material_name")
                certificate_number = st.text_input("Номер сертификата", key="material_certificate_number")
                mat_col1, mat_col2 = st.columns(2)
                with mat_col1:
                    certificate_valid_from = st.date_input(
                        "Срок действия с", value=None, key="material_valid_from"
                    )
                with mat_col2:
                    certificate_valid_to = st.date_input(
                        "Срок действия по", value=None, key="material_valid_to"
                    )

                material_submitted = st.form_submit_button("Добавить материал")

                if material_submitted:
                    if not material_name.strip():
                        st.error("Укажите название материала.")
                    else:
                        material_save_ok = True
                        try:
                            create_material(
                                act_id=cur_act["act_id"],
                                material_name=material_name.strip(),
                                certificate_number=certificate_number.strip() or None,
                                valid_from=certificate_valid_from,
                                valid_to=certificate_valid_to,
                            )
                        except Exception as db_exc:
                            material_save_ok = False
                            print(f"[DB ERROR] Не удалось сохранить материал «{material_name.strip()}»: {db_exc}")
                            traceback.print_exc()
                            st.error(
                                "Не удалось сохранить материал. "
                                "Проверьте соединение с базой данных и попробуйте ещё раз."
                            )

                        if material_save_ok:
                            get_materials_for_act.clear()
                            st.success(f"Материал «{material_name.strip()}» добавлен.")
                            st.rerun()

            st.markdown("**Уже добавленные материалы**")
            act_materials = get_materials_for_act(cur_act["act_id"])
            if not act_materials:
                st.info("Материалы для этого акта пока не добавлены.")
            else:
                for mat in act_materials:
                    mat_id, mat_name, mat_cert_number, mat_valid_from, mat_valid_to = mat
                    with st.container(border=True):
                        st.markdown(f"**{mat_name}**")
                        if mat_cert_number:
                            st.write(f"Сертификат: {mat_cert_number}")
                        if mat_valid_from or mat_valid_to:
                            from_str = mat_valid_from.strftime("%d.%m.%Y") if mat_valid_from else "—"
                            to_str = mat_valid_to.strftime("%d.%m.%Y") if mat_valid_to else "—"
                            st.write(f"Срок действия: {from_str} — {to_str}")

        st.divider()
        st.subheader("Ранее созданные акты")
        object_acts = get_acts_for_object(object_id)
        if not object_acts:
            st.info("Для этого объекта пока нет созданных актов.")
        else:
            for obj_act_id, obj_act_number, obj_act_date, obj_act_work_name in object_acts:
                with st.container(border=True):
                    st.markdown(f"**Акт №{obj_act_number}** от {obj_act_date.strftime('%d.%m.%Y')}")
                    st.write(obj_act_work_name)
                    obj_act_docx_key = f"act_docx_bytes_{obj_act_id}"
                    if st.button("Подготовить .docx", key=f"prepare_act_object_{obj_act_id}"):
                        obj_act_docx_buffer = io.BytesIO()
                        generate_act_docx(obj_act_id, obj_act_docx_buffer)
                        st.session_state[obj_act_docx_key] = obj_act_docx_buffer.getvalue()
                    if obj_act_docx_key in st.session_state:
                        st.download_button(
                            "Скачать акт .docx",
                            data=st.session_state[obj_act_docx_key],
                            file_name=f"Акт_{obj_act_number}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            key=f"download_act_object_{obj_act_id}",
                        )
