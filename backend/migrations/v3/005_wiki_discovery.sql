-- Additive wiki names and derived search index. Original Markdown/revisions stay intact.
ALTER TABLE wiki_revisions ADD COLUMN aliases jsonb NOT NULL DEFAULT '[]'::jsonb;
ALTER TABLE wiki_revisions ADD COLUMN meaning varchar(500) NOT NULL DEFAULT '';
ALTER TABLE wiki_revisions ADD COLUMN name_keys jsonb NOT NULL DEFAULT '[]'::jsonb;
UPDATE wiki_revisions SET name_keys = jsonb_build_array(lower(btrim(title)));
CREATE INDEX wiki_revision_names_idx ON wiki_revisions USING gin(name_keys);
ALTER TABLE wiki_pages ADD COLUMN indexed_revision_id varchar(80);
ALTER TABLE wiki_pages ADD CONSTRAINT wiki_indexed_revision_fk FOREIGN KEY (id, indexed_revision_id)
  REFERENCES wiki_revisions(page_id, id) DEFERRABLE INITIALLY DEFERRED;
CREATE TABLE wiki_index_jobs (
 id varchar(80) PRIMARY KEY, page_id varchar(80) NOT NULL REFERENCES wiki_pages(id),
 revision_id varchar(80) NOT NULL UNIQUE,
 status varchar(24) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','running','succeeded','failed','superseded')),
 attempts integer NOT NULL DEFAULT 0 CHECK (attempts >= 0), profile_id varchar(240),
 progress jsonb NOT NULL DEFAULT '{}'::jsonb, error jsonb, usage jsonb NOT NULL DEFAULT '{}'::jsonb,
 created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(),
 FOREIGN KEY (page_id, revision_id) REFERENCES wiki_revisions(page_id, id)
);
CREATE INDEX wiki_jobs_pending_idx ON wiki_index_jobs(created_at, id) WHERE status = 'pending';
CREATE TABLE wiki_passages (
 id varchar(80) PRIMARY KEY, revision_id varchar(80) NOT NULL REFERENCES wiki_revisions(id),
 ordinal integer NOT NULL, text text NOT NULL, locator text NOT NULL,
 start_offset integer NOT NULL, end_offset integer NOT NULL,
 embedding_text text NOT NULL, input_hash varchar(64) NOT NULL,
 excluded boolean NOT NULL DEFAULT false, exclusion_reason text,
 UNIQUE (revision_id, ordinal), CHECK (start_offset >= 0 AND end_offset > start_offset)
);
CREATE TABLE wiki_passage_embeddings (
 id varchar(80) PRIMARY KEY, passage_id varchar(80) NOT NULL REFERENCES wiki_passages(id),
 profile_id varchar(240) NOT NULL, embedding_id varchar(80) NOT NULL REFERENCES embedding_records(id),
 UNIQUE(passage_id, profile_id)
);
-- Already published stage-1 pages are queued once, without generating content or calling a model.
INSERT INTO wiki_index_jobs (id, page_id, revision_id)
 SELECT 'wjob_' || md5(id || current_revision_id), id, current_revision_id FROM wiki_pages;
