from db import get_db_connection


def get_organizations(role):
    with get_db_connection() as cur:
        cur.execute(
            """
            SELECT o.id, o.name
            FROM organizations o
            JOIN organization_roles r ON r.organization_id = o.id
            WHERE r.role = %s
            ORDER BY o.name;
            """,
            (role,),
        )
        return cur.fetchall()


def get_organizations_by_roles(roles):
    with get_db_connection() as cur:
        cur.execute(
            """
            SELECT o.id, o.name, r.role
            FROM organizations o
            JOIN organization_roles r ON r.organization_id = o.id
            WHERE r.role = ANY(%s)
            ORDER BY o.name;
            """,
            (list(roles),),
        )
        rows = cur.fetchall()
    result = {role: [] for role in roles}
    for org_id, org_name, org_role in rows:
        result[org_role].append((org_id, org_name))
    return result


def create_organization(name, roles, inn, ogrn, address, phone, sro_info):
    with get_db_connection() as cur:
        cur.execute(
            """
            INSERT INTO organizations (name, inn, ogrn, address, phone, sro_info)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id;
            """,
            (name, inn, ogrn, address, phone, sro_info or None),
        )
        org_id = cur.fetchone()[0]
        cur.executemany(
            "INSERT INTO organization_roles (organization_id, role) VALUES (%s, %s);",
            [(org_id, role) for role in roles],
        )
        return org_id


def get_all_organizations():
    with get_db_connection() as cur:
        cur.execute(
            """
            SELECT o.id, o.name, string_agg(r.role, ', ' ORDER BY r.role)
            FROM organizations o
            LEFT JOIN organization_roles r ON r.organization_id = o.id
            GROUP BY o.id, o.name
            ORDER BY o.name;
            """
        )
        return cur.fetchall()
