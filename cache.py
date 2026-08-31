import streamlit as st

from objects import (
    get_objects as get_objects_uncached,
    get_object_org_links as get_object_org_links_uncached,
)
from organizations import (
    get_organizations as get_organizations_uncached,
    get_all_organizations as get_all_organizations_uncached,
)
from persons import get_responsible_persons as get_responsible_persons_uncached
from acts import (
    get_acts_for_object as get_acts_for_object_uncached,
    get_materials_for_act as get_materials_for_act_uncached,
)
from journal import (
    get_work_journal_entries as get_work_journal_entries_uncached,
    get_work_journal_entries_for_period as get_work_journal_entries_for_period_uncached,
)
from commission_acts import (
    get_commission_acts_for_object as get_commission_acts_for_object_uncached,
    get_commission_act_signatories as get_commission_act_signatories_uncached,
)
from registries import (
    get_registries_for_object as get_registries_for_object_uncached,
    get_registry_documents as get_registry_documents_uncached,
)
from documents import get_document_list as get_document_list_uncached
from pending_requests import get_pending_requests as get_pending_requests_uncached


@st.cache_data(ttl=60)
def get_objects():
    return get_objects_uncached()


@st.cache_data(ttl=60)
def get_object_org_links(object_id):
    return get_object_org_links_uncached(object_id)


@st.cache_data(ttl=60)
def get_organizations(role):
    return get_organizations_uncached(role)


@st.cache_data(ttl=60)
def get_all_organizations():
    return get_all_organizations_uncached()


@st.cache_data(ttl=60)
def get_responsible_persons(organization_ids):
    return get_responsible_persons_uncached(organization_ids)


@st.cache_data(ttl=60)
def get_acts_for_object(object_id):
    return get_acts_for_object_uncached(object_id)


@st.cache_data(ttl=60)
def get_materials_for_act(act_id):
    return get_materials_for_act_uncached(act_id)


@st.cache_data(ttl=60)
def get_work_journal_entries(object_id):
    return get_work_journal_entries_uncached(object_id)


@st.cache_data(ttl=60)
def get_work_journal_entries_for_period(object_id, date_start, date_end):
    return get_work_journal_entries_for_period_uncached(object_id, date_start, date_end)


@st.cache_data(ttl=60)
def get_commission_acts_for_object(object_id):
    return get_commission_acts_for_object_uncached(object_id)


@st.cache_data(ttl=60)
def get_commission_act_signatories(commission_act_id):
    return get_commission_act_signatories_uncached(commission_act_id)


@st.cache_data(ttl=60)
def get_registries_for_object(object_id):
    return get_registries_for_object_uncached(object_id)


@st.cache_data(ttl=60)
def get_registry_documents(registry_id):
    return get_registry_documents_uncached(registry_id)


@st.cache_data(ttl=60)
def get_document_list():
    return get_document_list_uncached()


@st.cache_data(ttl=60)
def get_pending_requests(object_id):
    return get_pending_requests_uncached(object_id)
