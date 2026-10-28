CREATE TABLE knowledge_users (
    id varchar(80) PRIMARY KEY,
    username varchar(128) NOT NULL,
    password_hash varchar(512) NOT NULL,
    role varchar(32) NOT NULL DEFAULT 'user',
    kind varchar(16) NOT NULL DEFAULT 'user',
    permissions jsonb NOT NULL DEFAULT '[]'::jsonb,
    is_active boolean NOT NULL DEFAULT true,
    token_version integer NOT NULL DEFAULT 1,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ck_user_role CHECK (role IN ('user', 'admin')),
    CONSTRAINT ck_user_kind CHECK (kind IN ('user', 'service')),
    CONSTRAINT ck_user_token_version CHECK (token_version >= 1)
);
CREATE UNIQUE INDEX ix_knowledge_users_username ON knowledge_users (username);
CREATE TABLE conversations (
    id varchar(80) PRIMARY KEY,
    owner_id varchar(80) NOT NULL REFERENCES knowledge_users(id) ON DELETE CASCADE,
    title varchar(300) NOT NULL DEFAULT '새 대화',
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ck_conversation_title CHECK (length(btrim(title)) > 0)
);
CREATE INDEX ix_conversations_owner_id ON conversations (owner_id);
CREATE TABLE messages (
    id varchar(80) PRIMARY KEY,
    conversation_id varchar(80) NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role varchar(16) NOT NULL,
    content text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ck_message_role CHECK (role IN ('user', 'assistant')),
    CONSTRAINT ck_message_content CHECK (length(btrim(content)) > 0)
);
CREATE INDEX ix_messages_conversation_created ON messages (conversation_id, created_at, id);
