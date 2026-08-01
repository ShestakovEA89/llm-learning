import datetime
import traceback

import anthropic
import streamlit as st

from objects import create_object, update_object_org_links
from organizations import create_organization
from persons import create_responsible_person
from registries import (
    create_registry,
    parse_registry_text,
    create_registry_documents_bulk,
)
from cache import (
    get_objects,
    get_object_org_links,
    get_organizations,
    get_all_organizations,
    get_responsible_persons,
    get_registries_for_object,
    get_registry_documents,
)
from shared import NEW_ORG_OPTION

NEW_OBJECT_OPTION = "➕ Добавить новый объект"

OBJECT_PLACEHOLDER = "— Выберите объект —"
DEVELOPER_PLACEHOLDER = "— Выберите застройщика —"
CONTRACTOR_PLACEHOLDER = "— Выберите подрядчика —"
OTHER_ORG_OPTION = "— Другая организация из базы —"


def render():
    st.subheader("Объект")
    st.caption("Выберите объект, застройщика и подрядчика — они будут использоваться в журнале работ и актах.")

    obj_objects = get_objects()
    obj_developers = get_organizations("застройщик")
    obj_contractors = get_organizations("подрядчик")

    obj_object_options = [(None, OBJECT_PLACEHOLDER)] + list(obj_objects) + [(None, NEW_OBJECT_OPTION)]
    obj_developer_options = [(None, DEVELOPER_PLACEHOLDER)] + list(obj_developers) + [(None, NEW_ORG_OPTION)]
    obj_contractor_options = [(None, CONTRACTOR_PLACEHOLDER)] + list(obj_contractors) + [(None, NEW_ORG_OPTION)]

    obj_object_choice = st.selectbox(
        "Объект",
        options=obj_object_options,
        format_func=lambda o: f"{o[1]}, {o[2]}" if o[0] is not None else o[1],
        key="obj_tab_object_choice",
    )
    new_obj_object = {}
    if obj_object_choice[1] == NEW_OBJECT_OPTION:
        st.caption("Новый объект")
        new_obj_object["name"] = st.text_input("Название объекта", key="obj_tab_new_object_name")
        new_obj_object["address"] = st.text_input("Адрес", key="obj_tab_new_object_address")

    if "obj_tab_last_object_id" not in st.session_state:
        st.session_state.obj_tab_last_object_id = None

    if obj_object_choice[0] != st.session_state.obj_tab_last_object_id:
        st.session_state.obj_tab_last_object_id = obj_object_choice[0]
        if obj_object_choice[0] is not None:
            linked_developer_id, linked_contractor_id = get_object_org_links(obj_object_choice[0])
            if linked_developer_id is not None:
                for linked_dev_option in obj_developer_options:
                    if linked_dev_option[0] == linked_developer_id:
                        st.session_state.obj_tab_developer_choice = linked_dev_option
                        break
            if linked_contractor_id is not None:
                for linked_con_option in obj_contractor_options:
                    if linked_con_option[0] == linked_contractor_id:
                        st.session_state.obj_tab_contractor_choice = linked_con_option
                        break

    obj_developer_choice = st.selectbox(
        "Застройщик",
        options=obj_developer_options,
        format_func=lambda o: o[1],
        key="obj_tab_developer_choice",
    )
    new_obj_developer = {}
    if obj_developer_choice[1] == NEW_ORG_OPTION:
        st.caption("Новая организация — застройщик")
        new_obj_developer["name"] = st.text_input("Название организации", key="obj_tab_new_developer_name")
        odcol1, odcol2 = st.columns(2)
        with odcol1:
            new_obj_developer["inn"] = st.text_input("ИНН", key="obj_tab_new_developer_inn")
        with odcol2:
            new_obj_developer["ogrn"] = st.text_input("ОГРН", key="obj_tab_new_developer_ogrn")
        new_obj_developer["address"] = st.text_input("Адрес", key="obj_tab_new_developer_address")
        new_obj_developer["phone"] = st.text_input("Телефон", key="obj_tab_new_developer_phone")
        new_obj_developer["sro_info"] = st.text_input("Данные СРО (необязательно)", key="obj_tab_new_developer_sro")

    obj_contractor_choice = st.selectbox(
        "Подрядчик",
        options=obj_contractor_options,
        format_func=lambda o: o[1],
        key="obj_tab_contractor_choice",
    )
    new_obj_contractor = {}
    if obj_contractor_choice[1] == NEW_ORG_OPTION:
        st.caption("Новая организация — подрядчик")
        new_obj_contractor["name"] = st.text_input("Название организации", key="obj_tab_new_contractor_name")
        occol1, occol2 = st.columns(2)
        with occol1:
            new_obj_contractor["inn"] = st.text_input("ИНН", key="obj_tab_new_contractor_inn")
        with occol2:
            new_obj_contractor["ogrn"] = st.text_input("ОГРН", key="obj_tab_new_contractor_ogrn")
        new_obj_contractor["address"] = st.text_input("Адрес", key="obj_tab_new_contractor_address")
        new_obj_contractor["phone"] = st.text_input("Телефон", key="obj_tab_new_contractor_phone")
        new_obj_contractor["sro_info"] = st.text_input("Данные СРО (необязательно)", key="obj_tab_new_contractor_sro")

    if st.button("Сохранить", key="obj_tab_save"):
        obj_errors = []
        if obj_object_choice[1] == OBJECT_PLACEHOLDER:
            obj_errors.append("Выберите объект или создайте новый.")
        elif obj_object_choice[1] == NEW_OBJECT_OPTION:
            if not new_obj_object["name"].strip() or not new_obj_object["address"].strip():
                obj_errors.append("Заполните все обязательные поля нового объекта.")

        if obj_developer_choice[1] == DEVELOPER_PLACEHOLDER:
            obj_errors.append("Выберите застройщика или создайте новую организацию.")
        elif obj_developer_choice[1] == NEW_ORG_OPTION:
            if not new_obj_developer["name"].strip() or not new_obj_developer["inn"].strip() \
                    or not new_obj_developer["ogrn"].strip() or not new_obj_developer["address"].strip() \
                    or not new_obj_developer["phone"].strip():
                obj_errors.append("Заполните все обязательные поля новой организации-застройщика.")

        if obj_contractor_choice[1] == CONTRACTOR_PLACEHOLDER:
            obj_errors.append("Выберите подрядчика или создайте новую организацию.")
        elif obj_contractor_choice[1] == NEW_ORG_OPTION:
            if not new_obj_contractor["name"].strip() or not new_obj_contractor["inn"].strip() \
                    or not new_obj_contractor["ogrn"].strip() or not new_obj_contractor["address"].strip() \
                    or not new_obj_contractor["phone"].strip():
                obj_errors.append("Заполните все обязательные поля новой организации-подрядчика.")

        if obj_errors:
            for err in obj_errors:
                st.error(err)
        else:
            db_save_ok = True
            try:
                if obj_object_choice[0] is None:
                    object_name_raw = new_obj_object["name"].strip()
                    object_address_raw = new_obj_object["address"].strip()
                    object_id = create_object(
                        name=object_name_raw,
                        address=object_address_raw,
                    )
                    object_name = f"{object_name_raw}, {object_address_raw}"
                    get_objects.clear()
                else:
                    object_id = obj_object_choice[0]
                    object_name = f"{obj_object_choice[1]}, {obj_object_choice[2]}"

                if obj_developer_choice[0] is None:
                    developer_id = create_organization(
                        name=new_obj_developer["name"].strip(),
                        roles=["застройщик"],
                        inn=new_obj_developer["inn"].strip(),
                        ogrn=new_obj_developer["ogrn"].strip(),
                        address=new_obj_developer["address"].strip(),
                        phone=new_obj_developer["phone"].strip(),
                        sro_info=new_obj_developer["sro_info"].strip(),
                    )
                    developer_name = new_obj_developer["name"].strip()
                    get_organizations.clear()
                else:
                    developer_id = obj_developer_choice[0]
                    developer_name = obj_developer_choice[1]

                if obj_contractor_choice[0] is None:
                    contractor_id = create_organization(
                        name=new_obj_contractor["name"].strip(),
                        roles=["подрядчик"],
                        inn=new_obj_contractor["inn"].strip(),
                        ogrn=new_obj_contractor["ogrn"].strip(),
                        address=new_obj_contractor["address"].strip(),
                        phone=new_obj_contractor["phone"].strip(),
                        sro_info=new_obj_contractor["sro_info"].strip(),
                    )
                    contractor_name = new_obj_contractor["name"].strip()
                    get_organizations.clear()
                else:
                    contractor_id = obj_contractor_choice[0]
                    contractor_name = obj_contractor_choice[1]

                update_object_org_links(object_id, developer_id, contractor_id)
                get_object_org_links.clear()
            except Exception as db_exc:
                db_save_ok = False
                print(f"[DB ERROR] Не удалось сохранить рабочий объект/организации: {db_exc}")
                traceback.print_exc()
                st.error(
                    "Не удалось сохранить рабочий объект. "
                    "Проверьте соединение с базой данных и попробуйте ещё раз."
                )

            if db_save_ok:
                st.session_state.current_object = {
                    "object_id": object_id,
                    "object_name": object_name,
                    "developer_id": developer_id,
                    "developer_name": developer_name,
                    "contractor_id": contractor_id,
                    "contractor_name": contractor_name,
                }

                for k in (
                    "obj_tab_new_object_name", "obj_tab_new_object_address",
                    "obj_tab_new_developer_name", "obj_tab_new_developer_inn", "obj_tab_new_developer_ogrn",
                    "obj_tab_new_developer_address", "obj_tab_new_developer_phone", "obj_tab_new_developer_sro",
                    "obj_tab_new_contractor_name", "obj_tab_new_contractor_inn", "obj_tab_new_contractor_ogrn",
                    "obj_tab_new_contractor_address", "obj_tab_new_contractor_phone", "obj_tab_new_contractor_sro",
                ):
                    st.session_state.pop(k, None)

                st.success(f"Объект сохранён: {object_name}")
                st.rerun()

    if "current_object" in st.session_state:
        cur_obj = st.session_state.current_object
        st.divider()
        st.markdown(
            f"**Текущий рабочий объект:** {cur_obj['object_name']}  \n"
            f"Застройщик: {cur_obj['developer_name']}  \n"
            f"Подрядчик: {cur_obj['contractor_name']}"
        )

        st.divider()
        st.subheader("📋 Реестры исполнительной документации")

        with st.expander("➕ Создать новый реестр"):
            new_registry_section_name = st.text_input(
                "Название раздела", key="new_registry_section_name"
            )
            new_registry_project_marks = st.text_input(
                "Шифр проекта (необязательно)", key="new_registry_project_marks"
            )
            if st.button("Создать реестр", key="create_registry_btn"):
                if not new_registry_section_name.strip():
                    st.error("Укажите название раздела.")
                else:
                    registry_save_ok = True
                    try:
                        create_registry(
                            cur_obj["object_id"],
                            new_registry_section_name.strip(),
                            new_registry_project_marks.strip() or None,
                        )
                    except Exception as db_exc:
                        registry_save_ok = False
                        print(f"[DB ERROR] Не удалось сохранить реестр «{new_registry_section_name.strip()}»: {db_exc}")
                        traceback.print_exc()
                        st.error(
                            "Не удалось сохранить реестр. "
                            "Проверьте соединение с базой данных и попробуйте ещё раз."
                        )

                    if registry_save_ok:
                        get_registries_for_object.clear()
                        st.session_state.pop("new_registry_section_name", None)
                        st.session_state.pop("new_registry_project_marks", None)
                        st.success(f"Реестр создан: {new_registry_section_name.strip()}")
                        st.rerun()

        obj_registries = get_registries_for_object(cur_obj["object_id"])
        if not obj_registries:
            st.info("Реестры для этого объекта пока не добавлены.")
        else:
            registry_options = [(None, "— Выберите реестр —")] + [
                (r[0], f"{r[1]} ({r[2]})" if r[2] else r[1]) for r in obj_registries
            ]
            registry_choice = st.selectbox(
                "Реестр",
                options=registry_options,
                format_func=lambda o: o[1],
                key="registry_choice",
            )
            if registry_choice[0] is not None:
                registry_docs = get_registry_documents(registry_choice[0])
                if not registry_docs:
                    st.info("В этом реестре пока нет документов.")
                for reg_doc in registry_docs:
                    (reg_doc_id, reg_doc_seq, reg_doc_is_header, reg_doc_name, reg_doc_number_date,
                     reg_doc_issuing_org, reg_doc_page_count, reg_doc_note) = reg_doc
                    if reg_doc_is_header:
                        st.markdown(f"**{reg_doc_seq}. {reg_doc_name}**" if reg_doc_seq else f"**{reg_doc_name}**")
                    else:
                        reg_cols = st.columns([0.6, 3, 2, 2, 0.8])
                        reg_cols[0].write(reg_doc_seq or "")
                        reg_cols[1].write(reg_doc_name or "")
                        reg_cols[2].write(reg_doc_number_date or "")
                        reg_cols[3].write(reg_doc_issuing_org or "")
                        reg_cols[4].write(reg_doc_page_count or "")
                        if reg_doc_note:
                            st.caption(reg_doc_note)

                st.markdown("###### Массовое добавление строк через текст реестра")
                registry_raw_text = st.text_area(
                    "Вставьте текст реестра",
                    height=200,
                    key="registry_raw_text",
                )
                if st.button("Разобрать", key="registry_parse_btn"):
                    if not registry_raw_text.strip():
                        st.error("Вставьте текст реестра для разбора.")
                    else:
                        with st.spinner("Разбираю текст реестра..."):
                            try:
                                parsed_rows = parse_registry_text(registry_raw_text)
                            except ValueError as parse_err:
                                st.error(f"Не удалось разобрать ответ Claude: {parse_err}")
                            except anthropic.APIError as api_err:
                                st.error(f"Ошибка обращения к Claude API: {api_err}")
                            else:
                                if not isinstance(parsed_rows, list):
                                    st.error("Claude вернул не список строк — попробуйте ещё раз.")
                                else:
                                    st.session_state.registry_parsed_rows = parsed_rows
                                    st.session_state.registry_parsed_for_id = registry_choice[0]
                                    st.success(f"Разобрано строк: {len(parsed_rows)}")

                if (
                    st.session_state.get("registry_parsed_rows")
                    and st.session_state.get("registry_parsed_for_id") == registry_choice[0]
                ):
                    parsed_preview_rows = st.session_state.registry_parsed_rows
                    st.markdown(f"**Предпросмотр: {len(parsed_preview_rows)} строк**")
                    st.dataframe(
                        parsed_preview_rows,
                        use_container_width=True,
                        column_order=[
                            "seq_number", "is_category_header", "document_name",
                            "document_number_date", "issuing_org", "page_count", "note",
                        ],
                    )

                    if st.button("Сохранить все строки", key="registry_save_parsed_btn"):
                        registry_bulk_save_ok = True
                        try:
                            create_registry_documents_bulk(registry_choice[0], parsed_preview_rows)
                        except Exception as db_exc:
                            registry_bulk_save_ok = False
                            print(f"[DB ERROR] Не удалось сохранить строки реестра: {db_exc}")
                            traceback.print_exc()
                            st.error(
                                "Не удалось сохранить строки реестра. "
                                "Разобранные данные не потеряны — проверьте соединение с базой данных "
                                "и попробуйте сохранить ещё раз."
                            )

                        if registry_bulk_save_ok:
                            get_registry_documents.clear()
                            st.session_state.pop("registry_parsed_rows", None)
                            st.session_state.pop("registry_parsed_for_id", None)
                            st.session_state.pop("registry_raw_text", None)
                            st.success(f"Сохранено строк: {len(parsed_preview_rows)}")
                            st.rerun()

        st.divider()
        st.subheader("Представители организаций")
        st.caption("Добавьте представителей застройщика и подрядчика для текущего объекта.")

        rep_org_options = [
            (cur_obj["developer_id"], f"Застройщик: {cur_obj['developer_name']}"),
            (cur_obj["contractor_id"], f"Подрядчик: {cur_obj['contractor_name']}"),
            (None, OTHER_ORG_OPTION),
        ]
        rep_org_choice = st.selectbox(
            "Организация представителя",
            options=rep_org_options,
            format_func=lambda o: o[1],
            key="rep_org_choice",
        )

        rep_organization_id = rep_org_choice[0]
        if rep_org_choice[1] == OTHER_ORG_OPTION:
            rep_all_orgs = get_all_organizations()
            rep_other_org_options = [(None, "— Выберите организацию —")] + [
                (o[0], f"{o[1]} ({o[2]})") for o in rep_all_orgs
            ]
            rep_other_org_choice = st.selectbox(
                "Организация",
                options=rep_other_org_options,
                format_func=lambda o: o[1],
                key="rep_other_org_choice",
            )
            rep_organization_id = rep_other_org_choice[0]

        rep_full_name = st.text_input("ФИО", key="rep_full_name")
        rep_position = st.text_input("Должность", key="rep_position")
        rep_col1, rep_col2 = st.columns(2)
        with rep_col1:
            rep_order_number = st.text_input("Номер приказа", key="rep_order_number")
        with rep_col2:
            rep_order_date = st.date_input("Дата приказа", value=datetime.date.today(), key="rep_order_date")
        rep_registry_number = st.text_input(
            "№ в реестре специалистов (необязательно)", key="rep_registry_number"
        )

        if st.button("Добавить представителя", key="rep_add_button"):
            rep_errors = []
            if rep_organization_id is None:
                rep_errors.append("Выберите организацию представителя.")
            if not rep_full_name.strip():
                rep_errors.append("Укажите ФИО.")
            if not rep_position.strip():
                rep_errors.append("Укажите должность.")
            if not rep_order_number.strip():
                rep_errors.append("Укажите номер приказа.")

            if rep_errors:
                for err in rep_errors:
                    st.error(err)
            else:
                rep_save_ok = True
                try:
                    create_responsible_person(
                        organization_id=rep_organization_id,
                        full_name=rep_full_name.strip(),
                        position=rep_position.strip(),
                        order_number=rep_order_number.strip(),
                        order_date=rep_order_date,
                        registry_number=rep_registry_number.strip(),
                    )
                except Exception as db_exc:
                    rep_save_ok = False
                    print(f"[DB ERROR] Не удалось сохранить представителя «{rep_full_name.strip()}»: {db_exc}")
                    traceback.print_exc()
                    st.error(
                        "Не удалось сохранить представителя. "
                        "Проверьте соединение с базой данных и попробуйте ещё раз."
                    )

                if rep_save_ok:
                    get_responsible_persons.clear()
                    for k in ("rep_full_name", "rep_position", "rep_order_number", "rep_registry_number"):
                        st.session_state.pop(k, None)
                    st.success(f"Представитель «{rep_full_name.strip()}» добавлен.")
                    st.rerun()

        st.divider()
        st.markdown("**Уже добавленные представители**")

        rep_org_ids = [cur_obj["developer_id"], cur_obj["contractor_id"]]
        rep_persons = get_responsible_persons(rep_org_ids)

        if not rep_persons:
            st.info("Представители для этого объекта пока не добавлены.")
        else:
            rep_role_by_org = {
                cur_obj["developer_id"]: f"Застройщик: {cur_obj['developer_name']}",
                cur_obj["contractor_id"]: f"Подрядчик: {cur_obj['contractor_name']}",
            }
            for rep_person in rep_persons:
                (rep_person_id, rep_person_full_name, rep_person_position, rep_person_order_number,
                 rep_person_order_date, rep_person_registry_number, rep_person_org_id) = rep_person
                with st.container(border=True):
                    st.markdown(f"**{rep_person_full_name}** · {rep_person_position}")
                    st.caption(rep_role_by_org.get(rep_person_org_id, "Организация"))
                    rep_order_date_str = (
                        rep_person_order_date.strftime("%d.%m.%Y") if rep_person_order_date else "—"
                    )
                    st.write(f"Приказ №{rep_person_order_number} от {rep_order_date_str}")
                    if rep_person_registry_number:
                        st.write(f"№ в реестре специалистов: {rep_person_registry_number}")
