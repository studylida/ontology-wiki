-- Durable answer runs. Existing foundation and document migrations remain unchanged.
ALTER TABLE messages DROP CONSTRAINT ck_message_content;
ALTER TABLE messages ADD COLUMN status varchar(24) NOT NULL DEFAULT 'completed';
ALTER TABLE messages ADD COLUMN run_id varchar(64);
ALTER TABLE messages ADD COLUMN citations jsonb NOT NULL DEFAULT '[]';
ALTER TABLE messages ADD COLUMN source_revision_ids jsonb NOT NULL DEFAULT '[]';
ALTER TABLE messages ADD COLUMN warnings jsonb NOT NULL DEFAULT '[]';
ALTER TABLE messages ADD CONSTRAINT ck_message_content CHECK (role = 'assistant' OR length(btrim(content)) > 0);
ALTER TABLE messages ADD CONSTRAINT ck_message_status CHECK (status IN ('accepted','retrieving','generating','completed','cancelled','failed','interrupted'));
CREATE TABLE retrieval_runs (
 id varchar(64) PRIMARY KEY,
 owner_id varchar(64) NOT NULL REFERENCES knowledge_users(id) ON DELETE CASCADE,
 conversation_id varchar(64) NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
 query_text text NOT NULL,
 result jsonb NOT NULL DEFAULT '{}',
 created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE answer_runs (
 id varchar(64) PRIMARY KEY,
 owner_id varchar(64) NOT NULL REFERENCES knowledge_users(id) ON DELETE CASCADE,
 conversation_id varchar(64) NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
 user_message_id varchar(64) NOT NULL REFERENCES messages(id),
 message_id varchar(64) NOT NULL UNIQUE REFERENCES messages(id),
 request_id varchar(128) NOT NULL,
 request_hash varchar(64) NOT NULL,
 request_payload jsonb NOT NULL,
 status varchar(24) NOT NULL DEFAULT 'accepted',
 process_epoch varchar(64) NOT NULL,
 durable_seq integer NOT NULL DEFAULT 0 CHECK (durable_seq >= 0),
 retrieval_run_id varchar(64) REFERENCES retrieval_runs(id),
 usage jsonb NOT NULL DEFAULT '{}',
 error jsonb,
 created_at timestamptz NOT NULL DEFAULT now(),
 updated_at timestamptz NOT NULL DEFAULT now(),
 CONSTRAINT uq_answer_owner_request UNIQUE(owner_id, request_id),
 CONSTRAINT ck_answer_status CHECK (status IN ('accepted','retrieving','generating','completed','cancelled','failed','interrupted'))
);
CREATE UNIQUE INDEX uq_answer_active_conversation ON answer_runs(conversation_id) WHERE status IN ('accepted','retrieving','generating');
CREATE INDEX ix_answer_conversation ON answer_runs(conversation_id, created_at);
ALTER TABLE messages ADD CONSTRAINT fk_message_run FOREIGN KEY(run_id) REFERENCES answer_runs(id) DEFERRABLE INITIALLY DEFERRED;
CREATE TABLE answer_event_batches (
 id varchar(64) PRIMARY KEY,
 run_id varchar(64) NOT NULL REFERENCES answer_runs(id) ON DELETE CASCADE,
 first_seq integer NOT NULL,
 last_seq integer NOT NULL,
 events jsonb NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now(),
 CONSTRAINT uq_answer_batch_first UNIQUE(run_id, first_seq),
 CONSTRAINT ck_answer_batch_range CHECK (first_seq > 0 AND last_seq >= first_seq)
);
