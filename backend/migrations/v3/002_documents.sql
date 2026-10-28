-- Shared documents are separate from private conversations. No approval tables.
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE documents (
 id varchar(80) PRIMARY KEY, owner_id varchar(80) NOT NULL REFERENCES knowledge_users(id),
 title varchar(500) NOT NULL, origin_key varchar(64) NOT NULL UNIQUE,
 current_revision_id varchar(80), active_revision_id varchar(80),
 withdrawn boolean NOT NULL DEFAULT false,
 created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE document_revisions (
 id varchar(80) PRIMARY KEY, document_id varchar(80) NOT NULL REFERENCES documents(id),
 revision integer NOT NULL CHECK(revision > 0), title varchar(500) NOT NULL,
 filename varchar(255) NOT NULL, media_type varchar(80) NOT NULL,
 raw_path text NOT NULL, raw_sha256 varchar(64) NOT NULL, input_hash varchar(64) NOT NULL,
 content text, content_hash varchar(64), metadata jsonb NOT NULL DEFAULT '{}',
 processing_metadata jsonb NOT NULL DEFAULT '{}', read_scope varchar(16) NOT NULL DEFAULT 'unknown',
 limitations jsonb NOT NULL DEFAULT '[]', index_status varchar(24) NOT NULL DEFAULT 'queued',
 embedding_profile varchar(240), index_snapshot_id varchar(80),
 created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(document_id, revision), UNIQUE(document_id, input_hash), UNIQUE(document_id, id),
 CHECK(index_status IN ('queued','processing','ready','failed','superseded'))
);
ALTER TABLE documents ADD CONSTRAINT document_current_revision_fk FOREIGN KEY(id,current_revision_id) REFERENCES document_revisions(document_id,id) DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE documents ADD CONSTRAINT document_active_revision_fk FOREIGN KEY(id,active_revision_id) REFERENCES document_revisions(document_id,id) DEFERRABLE INITIALLY DEFERRED;
CREATE TABLE passages (
 id varchar(80) PRIMARY KEY, source_revision_id varchar(80) NOT NULL REFERENCES document_revisions(id),
 ordinal integer NOT NULL CHECK(ordinal >= 0), text text NOT NULL, locator text NOT NULL,
 start_offset integer NOT NULL, end_offset integer NOT NULL,
 embedding_text text NOT NULL, input_hash varchar(64) NOT NULL,
 excluded boolean NOT NULL DEFAULT false, exclusion_reason text,
 source_map jsonb NOT NULL DEFAULT '{}',
 UNIQUE(source_revision_id,ordinal), CHECK(start_offset >= 0 AND end_offset > start_offset)
);
CREATE INDEX passages_revision ON passages(source_revision_id);
CREATE TABLE embedding_records (
 id varchar(80) PRIMARY KEY, scope varchar(16) NOT NULL DEFAULT 'shared',
 profile_id varchar(240) NOT NULL, input_hash varchar(64) NOT NULL, vector vector(1536) NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now(), UNIQUE(scope,profile_id,input_hash)
);
CREATE TABLE passage_embeddings (
 id varchar(80) PRIMARY KEY, passage_id varchar(80) NOT NULL REFERENCES passages(id),
 profile_id varchar(240) NOT NULL, embedding_id varchar(80) NOT NULL REFERENCES embedding_records(id),
 UNIQUE(passage_id,profile_id)
);
CREATE TABLE processing_jobs (
 id varchar(80) PRIMARY KEY, document_id varchar(80) NOT NULL REFERENCES documents(id),
 source_revision_id varchar(80) NOT NULL UNIQUE,
 kind varchar(32) NOT NULL DEFAULT 'document_index' CHECK(kind='document_index'),
 status varchar(24) NOT NULL DEFAULT 'pending', attempts integer NOT NULL DEFAULT 0,
 progress jsonb NOT NULL DEFAULT '{}', error jsonb, usage jsonb NOT NULL DEFAULT '{}',
 created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(),
 FOREIGN KEY(document_id,source_revision_id) REFERENCES document_revisions(document_id,id),
 CHECK(status IN ('pending','running','succeeded','failed','cancelled','superseded'))
);
CREATE INDEX processing_jobs_pending ON processing_jobs(status,created_at);
