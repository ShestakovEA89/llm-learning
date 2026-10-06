--
-- PostgreSQL database dump
--

\restrict v3xje9a0zAExVyaRIx4jgu8RvOgH7wWLvASmTo0ew9T48pQYEbfDK3y6qsqib4k

-- Dumped from database version 17.6
-- Dumped by pg_dump version 18.6

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: public; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA public;


--
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON SCHEMA public IS 'standard public schema';


--
-- Name: rls_auto_enable(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.rls_auto_enable() RETURNS event_trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
DECLARE
  cmd record;
BEGIN
  FOR cmd IN
    SELECT *
    FROM pg_event_trigger_ddl_commands()
    WHERE command_tag IN ('CREATE TABLE', 'CREATE TABLE AS', 'SELECT INTO')
      AND object_type IN ('table','partitioned table')
  LOOP
     IF cmd.schema_name IS NOT NULL AND cmd.schema_name IN ('public') AND cmd.schema_name NOT IN ('pg_catalog','information_schema') AND cmd.schema_name NOT LIKE 'pg_toast%' AND cmd.schema_name NOT LIKE 'pg_temp%' THEN
      BEGIN
        EXECUTE format('alter table if exists %s enable row level security', cmd.object_identity);
        RAISE LOG 'rls_auto_enable: enabled RLS on %', cmd.object_identity;
      EXCEPTION
        WHEN OTHERS THEN
          RAISE LOG 'rls_auto_enable: failed to enable RLS on %', cmd.object_identity;
      END;
     ELSE
        RAISE LOG 'rls_auto_enable: skip % (either system schema or not in enforced list: %.)', cmd.object_identity, cmd.schema_name;
     END IF;
  END LOOP;
END;
$$;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: act_signatories; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.act_signatories (
    act_id integer NOT NULL,
    person_id integer NOT NULL,
    role text NOT NULL,
    CONSTRAINT act_signatories_role_check CHECK ((role = ANY (ARRAY['застройщик, строительный контроль'::text, 'подрядчик'::text, 'подрядчик, строительный контроль'::text, 'субподрядчик, строительный контроль'::text, 'проектировщик, строительный контроль'::text, 'иные лица, строительный контроль'::text])))
);


--
-- Name: acts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.acts (
    id integer NOT NULL,
    act_number text,
    act_date date,
    object_id integer,
    work_name text,
    project_docs_ref text,
    supporting_docs text,
    date_start date,
    date_end date,
    normative_docs text,
    next_works_allowed text,
    additional_info text,
    copies_count integer DEFAULT 2,
    status text DEFAULT 'draft'::text,
    created_at timestamp without time zone DEFAULT now(),
    designer_org_id integer,
    developer_org_id integer,
    contractor_org_id integer
);


--
-- Name: acts_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.acts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: acts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.acts_id_seq OWNED BY public.acts.id;


--
-- Name: commission_act_signatories; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.commission_act_signatories (
    id integer NOT NULL,
    commission_act_id integer,
    person_id integer,
    role text,
    CONSTRAINT commission_act_signatories_role_check CHECK ((role = ANY (ARRAY['генеральный подрядчик'::text, 'монтажная организация'::text, 'строительный контроль'::text, 'технический заказчик'::text, 'технический заказчик по вопросам строительного контроля'::text, 'лицо, осуществляющее строительство'::text, 'лицо, осуществляющее строительство, по вопросам строительного контроля'::text, 'лицо, выполнившее работы'::text])))
);


--
-- Name: commission_act_signatories_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.commission_act_signatories_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: commission_act_signatories_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.commission_act_signatories_id_seq OWNED BY public.commission_act_signatories.id;


--
-- Name: commission_acts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.commission_acts (
    id integer NOT NULL,
    object_id integer,
    act_type text NOT NULL,
    act_date date,
    city text,
    findings_text text,
    created_at timestamp without time zone DEFAULT now()
);


--
-- Name: commission_acts_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.commission_acts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: commission_acts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.commission_acts_id_seq OWNED BY public.commission_acts.id;


--
-- Name: materials; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.materials (
    id integer NOT NULL,
    act_id integer,
    material_name text,
    certificate_number text,
    certificate_valid_from date,
    certificate_valid_to date,
    file_path text
);


--
-- Name: materials_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.materials_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: materials_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.materials_id_seq OWNED BY public.materials.id;


--
-- Name: objects; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.objects (
    id integer NOT NULL,
    name text,
    address text,
    developer_org_id integer,
    contractor_org_id integer
);


--
-- Name: objects_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.objects_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: objects_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.objects_id_seq OWNED BY public.objects.id;


--
-- Name: organization_roles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.organization_roles (
    organization_id integer NOT NULL,
    role text NOT NULL
);


--
-- Name: organizations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.organizations (
    id integer NOT NULL,
    name text,
    role text,
    inn text,
    ogrn text,
    address text,
    phone text,
    sro_info text
);


--
-- Name: organizations_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.organizations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: organizations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.organizations_id_seq OWNED BY public.organizations.id;


--
-- Name: pending_requests; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.pending_requests (
    id integer NOT NULL,
    object_id integer NOT NULL,
    title text NOT NULL,
    requested_from text NOT NULL,
    status text DEFAULT 'ожидает'::text NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    completed_at timestamp without time zone,
    note text,
    CONSTRAINT pending_requests_status_check CHECK ((status = ANY (ARRAY['ожидает'::text, 'получено'::text])))
);


--
-- Name: pending_requests_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.pending_requests_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: pending_requests_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.pending_requests_id_seq OWNED BY public.pending_requests.id;


--
-- Name: registries; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.registries (
    id integer NOT NULL,
    object_id integer,
    registry_number text,
    registry_date date,
    work_section_name text,
    project_marks text,
    created_at timestamp without time zone DEFAULT now()
);


--
-- Name: registries_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.registries_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: registries_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.registries_id_seq OWNED BY public.registries.id;


--
-- Name: registry_documents; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.registry_documents (
    id integer NOT NULL,
    registry_id integer,
    seq_number text,
    is_category_header boolean DEFAULT false,
    document_name text,
    document_number_date text,
    issuing_org text,
    page_count text,
    note text
);


--
-- Name: registry_documents_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.registry_documents_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: registry_documents_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.registry_documents_id_seq OWNED BY public.registry_documents.id;


--
-- Name: responsible_persons; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.responsible_persons (
    id integer NOT NULL,
    full_name text,
    "position" text,
    organization_id integer,
    order_number text,
    order_date date,
    registry_number text
);


--
-- Name: responsible_persons_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.responsible_persons_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: responsible_persons_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.responsible_persons_id_seq OWNED BY public.responsible_persons.id;


--
-- Name: work_journal; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.work_journal (
    id integer NOT NULL,
    object_id integer,
    work_date date,
    location text,
    work_type text,
    description text,
    created_at timestamp without time zone DEFAULT now()
);


--
-- Name: work_journal_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.work_journal_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: work_journal_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.work_journal_id_seq OWNED BY public.work_journal.id;


--
-- Name: work_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.work_logs (
    id integer NOT NULL,
    act_id integer,
    work_date date,
    location text,
    raw_text text,
    parsed_description text,
    created_at timestamp without time zone DEFAULT now()
);


--
-- Name: work_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.work_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: work_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.work_logs_id_seq OWNED BY public.work_logs.id;


--
-- Name: acts id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.acts ALTER COLUMN id SET DEFAULT nextval('public.acts_id_seq'::regclass);


--
-- Name: commission_act_signatories id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.commission_act_signatories ALTER COLUMN id SET DEFAULT nextval('public.commission_act_signatories_id_seq'::regclass);


--
-- Name: commission_acts id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.commission_acts ALTER COLUMN id SET DEFAULT nextval('public.commission_acts_id_seq'::regclass);


--
-- Name: materials id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.materials ALTER COLUMN id SET DEFAULT nextval('public.materials_id_seq'::regclass);


--
-- Name: objects id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.objects ALTER COLUMN id SET DEFAULT nextval('public.objects_id_seq'::regclass);


--
-- Name: organizations id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.organizations ALTER COLUMN id SET DEFAULT nextval('public.organizations_id_seq'::regclass);


--
-- Name: pending_requests id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pending_requests ALTER COLUMN id SET DEFAULT nextval('public.pending_requests_id_seq'::regclass);


--
-- Name: registries id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.registries ALTER COLUMN id SET DEFAULT nextval('public.registries_id_seq'::regclass);


--
-- Name: registry_documents id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.registry_documents ALTER COLUMN id SET DEFAULT nextval('public.registry_documents_id_seq'::regclass);


--
-- Name: responsible_persons id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.responsible_persons ALTER COLUMN id SET DEFAULT nextval('public.responsible_persons_id_seq'::regclass);


--
-- Name: work_journal id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.work_journal ALTER COLUMN id SET DEFAULT nextval('public.work_journal_id_seq'::regclass);


--
-- Name: work_logs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.work_logs ALTER COLUMN id SET DEFAULT nextval('public.work_logs_id_seq'::regclass);


--
-- Name: act_signatories act_signatories_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_signatories
    ADD CONSTRAINT act_signatories_pkey PRIMARY KEY (act_id, person_id, role);


--
-- Name: acts acts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.acts
    ADD CONSTRAINT acts_pkey PRIMARY KEY (id);


--
-- Name: commission_act_signatories commission_act_signatories_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.commission_act_signatories
    ADD CONSTRAINT commission_act_signatories_pkey PRIMARY KEY (id);


--
-- Name: commission_acts commission_acts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.commission_acts
    ADD CONSTRAINT commission_acts_pkey PRIMARY KEY (id);


--
-- Name: materials materials_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.materials
    ADD CONSTRAINT materials_pkey PRIMARY KEY (id);


--
-- Name: objects objects_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.objects
    ADD CONSTRAINT objects_pkey PRIMARY KEY (id);


--
-- Name: organization_roles organization_roles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.organization_roles
    ADD CONSTRAINT organization_roles_pkey PRIMARY KEY (organization_id, role);


--
-- Name: organizations organizations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.organizations
    ADD CONSTRAINT organizations_pkey PRIMARY KEY (id);


--
-- Name: pending_requests pending_requests_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pending_requests
    ADD CONSTRAINT pending_requests_pkey PRIMARY KEY (id);


--
-- Name: registries registries_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.registries
    ADD CONSTRAINT registries_pkey PRIMARY KEY (id);


--
-- Name: registry_documents registry_documents_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.registry_documents
    ADD CONSTRAINT registry_documents_pkey PRIMARY KEY (id);


--
-- Name: responsible_persons responsible_persons_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.responsible_persons
    ADD CONSTRAINT responsible_persons_pkey PRIMARY KEY (id);


--
-- Name: work_journal work_journal_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.work_journal
    ADD CONSTRAINT work_journal_pkey PRIMARY KEY (id);


--
-- Name: work_logs work_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.work_logs
    ADD CONSTRAINT work_logs_pkey PRIMARY KEY (id);


--
-- Name: act_signatories act_signatories_act_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_signatories
    ADD CONSTRAINT act_signatories_act_id_fkey FOREIGN KEY (act_id) REFERENCES public.acts(id);


--
-- Name: act_signatories act_signatories_person_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.act_signatories
    ADD CONSTRAINT act_signatories_person_id_fkey FOREIGN KEY (person_id) REFERENCES public.responsible_persons(id);


--
-- Name: acts acts_contractor_org_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.acts
    ADD CONSTRAINT acts_contractor_org_id_fkey FOREIGN KEY (contractor_org_id) REFERENCES public.organizations(id);


--
-- Name: acts acts_designer_org_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.acts
    ADD CONSTRAINT acts_designer_org_id_fkey FOREIGN KEY (designer_org_id) REFERENCES public.organizations(id);


--
-- Name: acts acts_developer_org_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.acts
    ADD CONSTRAINT acts_developer_org_id_fkey FOREIGN KEY (developer_org_id) REFERENCES public.organizations(id);


--
-- Name: acts acts_object_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.acts
    ADD CONSTRAINT acts_object_id_fkey FOREIGN KEY (object_id) REFERENCES public.objects(id);


--
-- Name: commission_act_signatories commission_act_signatories_commission_act_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.commission_act_signatories
    ADD CONSTRAINT commission_act_signatories_commission_act_id_fkey FOREIGN KEY (commission_act_id) REFERENCES public.commission_acts(id);


--
-- Name: commission_act_signatories commission_act_signatories_person_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.commission_act_signatories
    ADD CONSTRAINT commission_act_signatories_person_id_fkey FOREIGN KEY (person_id) REFERENCES public.responsible_persons(id);


--
-- Name: commission_acts commission_acts_object_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.commission_acts
    ADD CONSTRAINT commission_acts_object_id_fkey FOREIGN KEY (object_id) REFERENCES public.objects(id);


--
-- Name: materials materials_act_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.materials
    ADD CONSTRAINT materials_act_id_fkey FOREIGN KEY (act_id) REFERENCES public.acts(id);


--
-- Name: objects objects_contractor_org_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.objects
    ADD CONSTRAINT objects_contractor_org_id_fkey FOREIGN KEY (contractor_org_id) REFERENCES public.organizations(id);


--
-- Name: objects objects_developer_org_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.objects
    ADD CONSTRAINT objects_developer_org_id_fkey FOREIGN KEY (developer_org_id) REFERENCES public.organizations(id);


--
-- Name: organization_roles organization_roles_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.organization_roles
    ADD CONSTRAINT organization_roles_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id);


--
-- Name: pending_requests pending_requests_object_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pending_requests
    ADD CONSTRAINT pending_requests_object_id_fkey FOREIGN KEY (object_id) REFERENCES public.objects(id);


--
-- Name: registries registries_object_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.registries
    ADD CONSTRAINT registries_object_id_fkey FOREIGN KEY (object_id) REFERENCES public.objects(id);


--
-- Name: registry_documents registry_documents_registry_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.registry_documents
    ADD CONSTRAINT registry_documents_registry_id_fkey FOREIGN KEY (registry_id) REFERENCES public.registries(id);


--
-- Name: responsible_persons responsible_persons_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.responsible_persons
    ADD CONSTRAINT responsible_persons_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id);


--
-- Name: work_journal work_journal_object_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.work_journal
    ADD CONSTRAINT work_journal_object_id_fkey FOREIGN KEY (object_id) REFERENCES public.objects(id);


--
-- Name: work_logs work_logs_act_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.work_logs
    ADD CONSTRAINT work_logs_act_id_fkey FOREIGN KEY (act_id) REFERENCES public.acts(id);


--
-- Name: act_signatories; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.act_signatories ENABLE ROW LEVEL SECURITY;

--
-- Name: acts; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.acts ENABLE ROW LEVEL SECURITY;

--
-- Name: commission_act_signatories; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.commission_act_signatories ENABLE ROW LEVEL SECURITY;

--
-- Name: commission_acts; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.commission_acts ENABLE ROW LEVEL SECURITY;

--
-- Name: materials; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.materials ENABLE ROW LEVEL SECURITY;

--
-- Name: objects; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.objects ENABLE ROW LEVEL SECURITY;

--
-- Name: organization_roles; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.organization_roles ENABLE ROW LEVEL SECURITY;

--
-- Name: organizations; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.organizations ENABLE ROW LEVEL SECURITY;

--
-- Name: pending_requests; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.pending_requests ENABLE ROW LEVEL SECURITY;

--
-- Name: registries; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.registries ENABLE ROW LEVEL SECURITY;

--
-- Name: registry_documents; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.registry_documents ENABLE ROW LEVEL SECURITY;

--
-- Name: responsible_persons; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.responsible_persons ENABLE ROW LEVEL SECURITY;

--
-- Name: work_journal; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.work_journal ENABLE ROW LEVEL SECURITY;

--
-- Name: work_logs; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.work_logs ENABLE ROW LEVEL SECURITY;

--
-- PostgreSQL database dump complete
--

\unrestrict v3xje9a0zAExVyaRIx4jgu8RvOgH7wWLvASmTo0ew9T48pQYEbfDK3y6qsqib4k

