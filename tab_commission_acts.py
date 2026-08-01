import datetime
import traceback

import streamlit as st

from organizations import create_organization
from commission_acts import create_commission_act, create_commission_act_signatory
from cache import (
    get_organizations,
    get_all_organizations,
    get_responsible_persons,
    get_commission_acts_for_object,
    get_commission_act_signatories,
)
from shared import NEW_ORG_OPTION, go_to_object_tab

COMMISSION_ACT_TYPES = [
    "входной контроль",
    "окончание монтажных работ",
    "индивидуальные испытания",
    "окончание пусконаладочных работ",
    "комплексное испытание",
    "приёмка в эксплуатацию",
]
ORG_ROLE_OPTIONS = ["застройщик", "подрядчик", "проектировщик", "генподрядчик", "строительный контроль"]
COMMISSION_ROLE_SLOTS = [
    ("tech_customer", "Технический заказчик"),
    ("gen_contractor", "Генеральный подрядчик"),
    ("stroy_control", "Строительный контроль"),
    ("montage_org", "Монтажная организация"),
]
ACT_TYPE_PLACEHOLDER = "— Выберите тип акта —"
ORG_PLACEHOLDER = "— Выберите организацию —"
PERSON_PLACEHOLDER = "— Выберите представителя —"


def render():
    st.subheader("Комиссионные акты")

    if "current_object" not in st.session_state:
        st.info("Сначала выберите рабочий объект на вкладке «🏗️ Объект».")
    else:
        cur_obj = st.session_state.current_object
        st.markdown(f"Работаем с объектом: **{cur_obj['object_name']}**")
        if st.button("Сменить объект", key="ca_change_object"):
            go_to_object_tab()
            st.rerun()

        object_id = cur_obj["object_id"]

        ca_act_type_options = [(None, ACT_TYPE_PLACEHOLDER)] + [(t, t) for t in COMMISSION_ACT_TYPES]
        ca_act_type_choice = st.selectbox(
            "Тип комиссионного акта",
            options=ca_act_type_options,
            format_func=lambda o: o[1],
            key="ca_act_type",
        )

        ca_col1, ca_col2 = st.columns(2)
        with ca_col1:
            ca_act_date = st.date_input("Дата акта", value=datetime.date.today(), key="ca_act_date")
        with ca_col2:
            ca_city = st.text_input("Город", key="ca_city")

        ca_findings_text = st.text_area(
            "Текст заключения комиссии (необязательно)",
            placeholder="Например: «Комиссия установила, что...» — для актов вида «Комплексное испытание» и т. п.",
            key="ca_findings_text",
        )

        st.divider()
        st.markdown("**Состав комиссии**")

        ca_all_orgs = get_all_organizations()
        ca_org_options_base = [(o[0], f"{o[1]} ({o[2]})") for o in ca_all_orgs]

        ca_role_person_ids = {}

        for ca_slug, ca_role_label in COMMISSION_ROLE_SLOTS:
            st.markdown(f"*{ca_role_label}*")
            ca_org_options = [(None, ORG_PLACEHOLDER)] + ca_org_options_base + [(None, NEW_ORG_OPTION)]
            ca_org_choice = st.selectbox(
                "Организация",
                options=ca_org_options,
                format_func=lambda o: o[1],
                key=f"ca_{ca_slug}_org",
            )

            ca_org_id = ca_org_choice[0]

            if ca_org_choice[1] == NEW_ORG_OPTION:
                st.caption("Новая организация")
                ca_new_name = st.text_input("Название организации", key=f"ca_{ca_slug}_new_name")
                ca_new_col1, ca_new_col2 = st.columns(2)
                with ca_new_col1:
                    ca_new_inn = st.text_input("ИНН", key=f"ca_{ca_slug}_new_inn")
                with ca_new_col2:
                    ca_new_ogrn = st.text_input("ОГРН", key=f"ca_{ca_slug}_new_ogrn")
                ca_new_address = st.text_input("Адрес", key=f"ca_{ca_slug}_new_address")
                ca_new_phone = st.text_input("Телефон", key=f"ca_{ca_slug}_new_phone")
                ca_new_roles = st.multiselect(
                    "Роли организации",
                    options=ORG_ROLE_OPTIONS,
                    key=f"ca_{ca_slug}_new_role",
                )

                if st.button("Добавить организацию", key=f"ca_{ca_slug}_add_org_btn"):
                    if not ca_new_name.strip() or not ca_new_inn.strip() or not ca_new_ogrn.strip() \
                            or not ca_new_address.strip() or not ca_new_phone.strip():
                        st.error("Заполните все обязательные поля новой организации.")
                    elif not ca_new_roles:
                        st.error("Выберите хотя бы одну роль организации.")
                    else:
                        ca_org_save_ok = True
                        try:
                            create_organization(
                                name=ca_new_name.strip(),
                                roles=ca_new_roles,
                                inn=ca_new_inn.strip(),
                                ogrn=ca_new_ogrn.strip(),
                                address=ca_new_address.strip(),
                                phone=ca_new_phone.strip(),
                                sro_info="",
                            )
                        except Exception as db_exc:
                            ca_org_save_ok = False
                            print(f"[DB ERROR] Не удалось сохранить организацию «{ca_new_name.strip()}»: {db_exc}")
                            traceback.print_exc()
                            st.error(
                                "Не удалось сохранить организацию. "
                                "Проверьте соединение с базой данных и попробуйте ещё раз."
                            )

                        if ca_org_save_ok:
                            get_organizations.clear()
                            get_all_organizations.clear()
                            for k in (
                                f"ca_{ca_slug}_new_name", f"ca_{ca_slug}_new_inn", f"ca_{ca_slug}_new_ogrn",
                                f"ca_{ca_slug}_new_address", f"ca_{ca_slug}_new_phone",
                            ):
                                st.session_state.pop(k, None)
                            st.success(f"Организация «{ca_new_name.strip()}» добавлена.")
                            st.rerun()
                ca_org_id = None

            ca_person_id = None
            if ca_org_id is not None:
                ca_persons = get_responsible_persons([ca_org_id])
                if not ca_persons:
                    st.info(
                        "У этой организации ещё нет представителей — добавьте на вкладке «Объект» "
                        "→ «Представители организаций» (выбрав «Другая организация из базы»)."
                    )
                else:
                    ca_person_options = [(None, PERSON_PLACEHOLDER)] + [(p[0], p[1]) for p in ca_persons]
                    ca_person_choice = st.selectbox(
                        "Представитель",
                        options=ca_person_options,
                        format_func=lambda o: o[1],
                        key=f"ca_{ca_slug}_person",
                    )
                    ca_person_id = ca_person_choice[0]

            ca_role_person_ids[ca_slug] = ca_person_id
            st.divider()

        if st.button("Сохранить комиссионный акт", key="ca_save_button"):
            ca_errors = []
            if ca_act_type_choice[0] is None:
                ca_errors.append("Выберите тип комиссионного акта.")
            if not ca_city.strip():
                ca_errors.append("Укажите город.")
            for ca_slug, ca_role_label in COMMISSION_ROLE_SLOTS:
                if ca_role_person_ids.get(ca_slug) is None:
                    ca_errors.append(f"Выберите представителя для роли «{ca_role_label}».")

            if ca_errors:
                for err in ca_errors:
                    st.error(err)
            else:
                ca_save_ok = True
                try:
                    new_ca_id = create_commission_act(
                        object_id=object_id,
                        act_type=ca_act_type_choice[0],
                        act_date=ca_act_date,
                        city=ca_city.strip(),
                        findings_text=ca_findings_text.strip() or None,
                    )
                    for ca_slug, ca_role_label in COMMISSION_ROLE_SLOTS:
                        create_commission_act_signatory(
                            new_ca_id, ca_role_person_ids[ca_slug], ca_role_label.lower()
                        )
                except Exception as db_exc:
                    ca_save_ok = False
                    print(f"[DB ERROR] Не удалось сохранить комиссионный акт: {db_exc}")
                    traceback.print_exc()
                    st.error(
                        "Не удалось сохранить комиссионный акт. "
                        "Проверьте соединение с базой данных и попробуйте ещё раз."
                    )

                if ca_save_ok:
                    get_commission_acts_for_object.clear()
                    get_commission_act_signatories.clear()
                    for k in ("ca_city", "ca_findings_text"):
                        st.session_state.pop(k, None)
                    st.success(f"Комиссионный акт «{ca_act_type_choice[0]}» сохранён (id={new_ca_id}).")
                    st.rerun()

        st.divider()
        st.subheader("Уже созданные комиссионные акты")

        ca_existing_acts = get_commission_acts_for_object(object_id)
        if not ca_existing_acts:
            st.info("Комиссионные акты для этого объекта пока не созданы.")
        else:
            ca_acts_by_type = {}
            for ca_act in ca_existing_acts:
                ca_acts_by_type.setdefault(ca_act[1], []).append(ca_act)

            for ca_type in COMMISSION_ACT_TYPES:
                if ca_type not in ca_acts_by_type:
                    continue
                st.markdown(f"**{ca_type}**")
                for ca_act in ca_acts_by_type[ca_type]:
                    ca_id, ca_act_type_val, ca_date_val, ca_city_val, ca_findings_val, ca_created_val = ca_act
                    with st.container(border=True):
                        ca_date_str = ca_date_val.strftime("%d.%m.%Y") if ca_date_val else "—"
                        st.markdown(f"**{ca_date_str}** · {ca_city_val or '—'}")
                        if ca_findings_val:
                            st.write(ca_findings_val)
                        ca_signatories = get_commission_act_signatories(ca_id)
                        if ca_signatories:
                            for ca_sig_role, ca_sig_name, ca_sig_position in ca_signatories:
                                st.caption(f"{ca_sig_role}: {ca_sig_name} ({ca_sig_position})")
