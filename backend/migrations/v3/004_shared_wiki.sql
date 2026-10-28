-- Shared, employee-editable wiki. Existing chat/document migrations remain untouched.
CREATE TABLE wiki_pages (
    id varchar(80) PRIMARY KEY,
    creator_id varchar(80) NOT NULL REFERENCES knowledge_users(id),
    current_revision_id varchar(80),
    version integer NOT NULL CHECK (version >= 1),
    is_locked boolean NOT NULL DEFAULT false,
    protection_updated_by varchar(80) REFERENCES knowledge_users(id),
    protection_updated_at timestamptz,
    created_at timestamptz NOT NULL,
    updated_at timestamptz NOT NULL
);
CREATE TABLE wiki_revisions (
    id varchar(80) PRIMARY KEY,
    page_id varchar(80) NOT NULL REFERENCES wiki_pages(id),
    number integer NOT NULL CHECK (number >= 1),
    title varchar(300) NOT NULL CHECK (length(btrim(title)) > 0),
    markdown text NOT NULL CHECK (length(btrim(markdown)) > 0),
    source_note text NOT NULL DEFAULT '',
    change_summary varchar(500) NOT NULL DEFAULT '',
    editor_id varchar(80) NOT NULL REFERENCES knowledge_users(id),
    restored_from_id varchar(80),
    created_at timestamptz NOT NULL,
    UNIQUE (page_id, number),
    UNIQUE (page_id, id),
    FOREIGN KEY (page_id, restored_from_id) REFERENCES wiki_revisions(page_id, id)
);
ALTER TABLE wiki_pages ADD CONSTRAINT wiki_current_revision_fk
    FOREIGN KEY (id, current_revision_id) REFERENCES wiki_revisions(page_id, id)
    DEFERRABLE INITIALLY DEFERRED;
-- A committed page must always name its committed content revision.
ALTER TABLE wiki_pages ALTER COLUMN current_revision_id SET NOT NULL;
CREATE INDEX wiki_pages_recent ON wiki_pages(updated_at DESC, id);
CREATE TABLE wiki_mutations (
    actor_id varchar(80) NOT NULL REFERENCES knowledge_users(id),
    request_id varchar(128) NOT NULL,
    payload_hash varchar(64) NOT NULL,
    page_id varchar(80) NOT NULL REFERENCES wiki_pages(id),
    result jsonb NOT NULL,
    created_at timestamptz NOT NULL,
    PRIMARY KEY (actor_id, request_id)
);
