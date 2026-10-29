-- Requested drafts are NOT wiki pages, passages or public knowledge.
CREATE TABLE wiki_proposals (
 id varchar(80) PRIMARY KEY,
 owner_id varchar(80) NOT NULL REFERENCES knowledge_users(id),
 request_id varchar(128) NOT NULL,
 request_hash varchar(64) NOT NULL,
 page_id varchar(80) REFERENCES wiki_pages(id),
 base_revision_id varchar(80),
 base_version integer,
 mode varchar(16) NOT NULL CHECK (mode IN ('create','edit','links')),
 status varchar(16) NOT NULL CHECK (status IN ('pending','running','ready','applied','dismissed','failed')),
 input jsonb NOT NULL, base_snapshot jsonb NOT NULL DEFAULT '{}',
 result jsonb NOT NULL DEFAULT '{}', error jsonb, usage jsonb NOT NULL DEFAULT '{}',
 applied_result jsonb, applied_hash varchar(64), applied_by varchar(80) REFERENCES knowledge_users(id),
 created_at timestamptz NOT NULL, updated_at timestamptz NOT NULL,
 UNIQUE(owner_id, request_id),
 FOREIGN KEY(page_id, base_revision_id) REFERENCES wiki_revisions(page_id,id),
 CHECK ((mode='create' AND page_id IS NULL AND base_revision_id IS NULL AND base_version IS NULL)
     OR (mode<>'create' AND page_id IS NOT NULL AND base_revision_id IS NOT NULL AND base_version IS NOT NULL))
);
CREATE INDEX wiki_proposals_queue ON wiki_proposals(created_at,id) WHERE status='pending';
CREATE INDEX wiki_proposals_owner ON wiki_proposals(owner_id,created_at DESC);
ALTER TABLE wiki_revisions ADD COLUMN ai_proposal_id varchar(80) REFERENCES wiki_proposals(id);
ALTER TABLE wiki_revisions ADD COLUMN provenance jsonb NOT NULL DEFAULT '{}';
