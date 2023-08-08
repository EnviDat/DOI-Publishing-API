
-- TYPE ckan_entity_type

CREATE TYPE public.ckan_entity_type AS ENUM (
    'package',
    'resource'
);
ALTER TYPE public.ckan_entity_type OWNER TO postgres;

-- TABLE ckan_site

CREATE TABLE public.ckan_site (
    site_pk SERIAL PRIMARY KEY,
    site_id text NOT NULL,
    url text,
    description text
);

ALTER TABLE public.ckan_site OWNER TO postgres;
ALTER TABLE ONLY public.ckan_site
    ADD CONSTRAINT unique_ckan_site_id UNIQUE (site_id);

-- TABLE doi_prefix

CREATE TABLE public.doi_prefix (
    prefix_pk SERIAL PRIMARY KEY,
    prefix_id text NOT NULL,
    description text
);

ALTER TABLE public.doi_prefix OWNER TO postgres;
ALTER TABLE ONLY public.doi_prefix
    ADD CONSTRAINT unique_ckan_prefix_id UNIQUE (prefix_id);

-- TABLE doi_realisation

CREATE TABLE public.doi_realisation (
    doi_pk SERIAL PRIMARY KEY,
    prefix_id text NOT NULL,
    suffix_id text NOT NULL,
    ckan_id uuid NOT NULL,
    ckan_name text NOT NULL,
    site_id text NOT NULL,
    tag_id text DEFAULT 'envidat.' NOT NULL,
    ckan_user text DEFAULT 'admin' NOT NULL,
    metadata text NOT NULL,
    metadata_format text DEFAULT 'ckan'::text,
    ckan_entity public.ckan_entity_type DEFAULT 'package'::public.ckan_entity_type NOT NULL,
    date_created timestamp without time zone DEFAULT now() NOT NULL,
    date_modified timestamp without time zone DEFAULT now() NOT NULL
);

ALTER TABLE public.doi_realisation OWNER TO postgres;

ALTER TABLE ONLY public.doi_realisation
    ADD CONSTRAINT unique_ckan_id_site_entity UNIQUE (ckan_id, site_id, ckan_entity);

ALTER TABLE ONLY public.doi_realisation
    ADD CONSTRAINT prefix_fk FOREIGN KEY (prefix_id) REFERENCES public.doi_prefix(prefix_id);

ALTER TABLE ONLY public.doi_realisation
    ADD CONSTRAINT site_id_fk FOREIGN KEY (site_id) REFERENCES public.ckan_site(site_id);

ALTER TABLE public.doi_realisation
ADD CONSTRAINT unique_ckan_id_per_site
UNIQUE (ckan_id, site_id);

-- access rights
REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM postgres;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO PUBLIC;

GRANT ALL ON TABLE public.doi_realisation TO postgres;
