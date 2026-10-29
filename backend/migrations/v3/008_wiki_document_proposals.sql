-- Document-triggered work is independent of indexing and never publishes a page.
CREATE TABLE wiki_document_jobs (
 id varchar(80) PRIMARY KEY,
 source_revision_id varchar(80) NOT NULL UNIQUE REFERENCES document_revisions(id),
 status varchar(16) NOT NULL CHECK (status IN ('pending','running','succeeded','no_changes','failed','superseded')),
 result jsonb NOT NULL DEFAULT '{}', error jsonb, usage jsonb NOT NULL DEFAULT '{}',
 created_at timestamptz NOT NULL, updated_at timestamptz NOT NULL,
 started_at timestamptz
);
CREATE INDEX wiki_document_jobs_queue ON wiki_document_jobs(created_at,id) WHERE status='pending';
ALTER TABLE wiki_proposals ADD COLUMN origin_revision_id varchar(80) REFERENCES document_revisions(id);
CREATE INDEX wiki_proposals_origin ON wiki_proposals(origin_revision_id,created_at);
