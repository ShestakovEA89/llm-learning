import os
from datetime import date
import psycopg2
from docxtpl import DocxTemplate
from dotenv import load_dotenv

load_dotenv()

SUPABASE_CONNECTION = os.environ["SUPABASE_CONNECTION"]

RUSSIAN_MONTHS = {
    1: "января", 2: "февраля", 3: "марта", 4: "апреля",
    5: "мая", 6: "июня", 7: "июля", 8: "августа",
    9: "сентября", 10: "октября", 11: "ноября", 12: "декабря"
}


def fmt_date(d: date) -> str:
    if not d:
        return ""
    month_name = RUSSIAN_MONTHS[d.month]
    return f"«{d.strftime('%d')}» {month_name} {d.year} г."


def get_org_details(cur, act_id, role_keyword):
    cur.execute("""
        SELECT org.name, org.ogrn, org.inn, org.address, org.phone, org.sro_info
        FROM act_signatories s
        JOIN responsible_persons rp ON s.person_id = rp.id
        JOIN organizations org ON rp.organization_id = org.id
        WHERE s.act_id = %s AND s.role ILIKE %s
        LIMIT 1
    """, (act_id, f"%{role_keyword}%"))
    row = cur.fetchone()
    if not row:
        return "", ""
    name, ogrn, inn, address, phone, sro_info = row
    details = f"{name}, ОГРН {ogrn or 'б/н'}, ИНН {inn}, {address}, тел. {phone}"
    if sro_info:
        details += f", {sro_info}"
    return name, details


def get_person(cur, act_id, role_exact):
    cur.execute("""
        SELECT rp.full_name, rp.position, rp.registry_number, rp.order_number, rp.order_date
        FROM act_signatories s
        JOIN responsible_persons rp ON s.person_id = rp.id
        WHERE s.act_id = %s AND s.role = %s
        LIMIT 1
    """, (act_id, role_exact))
    row = cur.fetchone()
    if not row:
        return "", ""
    full_name, position, registry_number, order_number, order_date = row
    full_line = f"{position} {full_name}, приказ №{order_number} от {order_date.strftime('%d.%m.%Y')}"
    if registry_number:
        full_line += f", № в реестре специалистов {registry_number}"
    return full_line, full_name


def generate_act(act_id, output_path, template_path="templates/template.docx"):
    conn = psycopg2.connect(SUPABASE_CONNECTION)
    cur = conn.cursor()

    cur.execute("""
        SELECT a.act_number, a.act_date, a.work_name, a.project_docs_ref,
               a.date_start, a.date_end, a.normative_docs, a.next_works_allowed,
               a.additional_info, a.supporting_docs, a.copies_count,
               o.name, o.address
        FROM acts a
        JOIN objects o ON a.object_id = o.id
        WHERE a.id = %s
    """, (act_id,))
    act = cur.fetchone()
    (act_number, act_date, work_name, project_docs_ref, date_start, date_end,
     normative_docs, next_works_allowed, additional_info, supporting_docs,
     copies_count, obj_name, obj_address) = act

    object_name = f"{obj_name}, {obj_address}"

    cur.execute("SELECT material_name, certificate_number FROM materials WHERE act_id = %s", (act_id,))
    materials = cur.fetchall()
    materials_list = "; ".join(f"{name} ({cert})" for name, cert in materials)

    customer_name, customer_details = get_org_details(cur, act_id, "застройщик")
    contractor_name, contractor_details = get_org_details(cur, act_id, "подрядчик")

    cur.execute("""
        SELECT org.name, org.ogrn, org.inn, org.address, org.phone, org.sro_info
        FROM acts a
        JOIN organizations org ON a.designer_org_id = org.id
        WHERE a.id = %s
    """, (act_id,))
    designer_row = cur.fetchone()
    if designer_row:
        d_name, d_ogrn, d_inn, d_address, d_phone, d_sro_info = designer_row
        designer_details = f"{d_name}, ОГРН {d_ogrn or 'б/н'}, ИНН {d_inn}, {d_address}, тел. {d_phone}"
        if d_sro_info:
            designer_details += f", {d_sro_info}"
    else:
        designer_details = ""

    control_rep_customer, control_rep_customer_short = get_person(cur, act_id, "застройщик, строительный контроль")
    contractor_rep, contractor_rep_short = get_person(cur, act_id, "подрядчик")
    control_rep_contractor, control_rep_contractor_short = get_person(cur, act_id, "подрядчик, строительный контроль")
    control_rep_designer, control_rep_designer_short = get_person(cur, act_id, "проектировщик, строительный контроль")
    control_rep_subcontractor, control_rep_subcontractor_short = get_person(cur, act_id, "субподрядчик, строительный контроль")

    cur.close()
    conn.close()

    context = {
        "object_name": object_name,
        "act_number": act_number,
        "act_date": fmt_date(act_date),
        "customer_details": customer_details,
        "contractor_details": contractor_details,
        "designer_details": designer_details,
        "contractor_name_short": contractor_name,

        "control_rep_customer": control_rep_customer,
        "control_rep_customer_short": control_rep_customer_short,
        "contractor_rep": contractor_rep,
        "contractor_rep_short": contractor_rep_short,
        "control_rep_contractor": control_rep_contractor,
        "control_rep_contractor_short": control_rep_contractor_short,
        "control_rep_designer": control_rep_designer,
        "control_rep_designer_short": control_rep_designer_short,
        "control_rep_subcontractor": control_rep_subcontractor,
        "control_rep_subcontractor_short": control_rep_subcontractor_short,

        "work_name": work_name,
        "project_docs_ref": project_docs_ref or "",
        "materials_list": materials_list,
        "supporting_docs": supporting_docs or "н/п",
        "date_start": fmt_date(date_start),
        "date_end": fmt_date(date_end),
        "normative_docs": normative_docs or "",
        "next_works_allowed": next_works_allowed or "",
        "additional_info": additional_info or "",
        "copies_count": copies_count,
        "attachments": "н/п",
    }

    doc = DocxTemplate(template_path)
    doc.render(context)
    doc.save(output_path)
    print(f"Акт сохранён: {output_path}")


if __name__ == "__main__":
    generate_act(act_id=1, output_path="final_act_1.docx")
    generate_act(act_id=2, output_path="final_act_2.docx")