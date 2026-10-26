-- Frozen initial schema for the separately provisioned v2 database.

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE embedding_records (
	id VARCHAR(80) NOT NULL, 
	scope VARCHAR(100) NOT NULL, 
	profile_id VARCHAR(160) NOT NULL, 
	input_hash VARCHAR(64) NOT NULL, 
	vector VECTOR(1536) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (scope, profile_id, input_hash)
);

CREATE INDEX ix_embedding_records_input_hash ON embedding_records (input_hash);

CREATE INDEX ix_embedding_records_profile_id ON embedding_records (profile_id);

CREATE TABLE knowledge_users (
	id VARCHAR(80) NOT NULL, 
	username VARCHAR(128) NOT NULL, 
	password_hash VARCHAR(512) NOT NULL, 
	role VARCHAR(32) NOT NULL, 
	kind VARCHAR(16) NOT NULL, 
	permissions JSONB NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	auto_wiki BOOLEAN NOT NULL, 
	token_version INTEGER NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
);

CREATE UNIQUE INDEX ix_knowledge_users_username ON knowledge_users (username);

CREATE TABLE legacy_archive (
	id VARCHAR(80) NOT NULL, 
	source_system VARCHAR(160) NOT NULL, 
	source_table VARCHAR(160) NOT NULL, 
	source_id TEXT NOT NULL, 
	record_hash VARCHAR(64) NOT NULL, 
	payload JSONB NOT NULL, 
	access_classification VARCHAR(80) NOT NULL, 
	imported_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (source_system, source_table, source_id, record_hash)
);

CREATE TABLE legacy_mappings (
	id VARCHAR(80) NOT NULL, 
	source_system VARCHAR(160) NOT NULL, 
	source_table VARCHAR(160) NOT NULL, 
	source_id TEXT NOT NULL, 
	target_type VARCHAR(80), 
	target_id VARCHAR(80), 
	disposition VARCHAR(80) NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (source_system, source_table, source_id)
);

CREATE TABLE ontology_concepts (
	id VARCHAR(80) NOT NULL, 
	name TEXT NOT NULL, 
	names JSONB NOT NULL, 
	aliases JSONB NOT NULL, 
	type VARCHAR(80) NOT NULL, 
	description TEXT, 
	evidence_refs JSONB NOT NULL, 
	revision INTEGER NOT NULL, 
	origin VARCHAR(80) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
);

CREATE INDEX ix_ontology_concepts_name ON ontology_concepts (name);

CREATE TABLE scheduler_state (
	key VARCHAR(100) NOT NULL, 
	value TEXT NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (key)
);

CREATE TABLE conversations (
	id VARCHAR(80) NOT NULL, 
	owner_id VARCHAR(80) NOT NULL, 
	title VARCHAR(300) NOT NULL, 
	auto_wiki BOOLEAN NOT NULL, 
	next_settings JSONB NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(owner_id) REFERENCES knowledge_users (id)
);

CREATE INDEX ix_conversations_owner_id ON conversations (owner_id);

CREATE INDEX ix_conversations_updated_at ON conversations (updated_at);

CREATE TABLE documents (
	id VARCHAR(80) NOT NULL, 
	owner_id VARCHAR(80) NOT NULL, 
	title TEXT NOT NULL, 
	visibility VARCHAR(32) NOT NULL, 
	current_revision_id VARCHAR(80), 
	active_revision_id VARCHAR(80), 
	withdrawn BOOLEAN NOT NULL, 
	origin_key TEXT, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(owner_id) REFERENCES knowledge_users (id), 
	UNIQUE (origin_key)
);

CREATE INDEX ix_documents_owner_id ON documents (owner_id);

CREATE TABLE knowledge_jobs (
	id VARCHAR(80) NOT NULL, 
	kind VARCHAR(48) NOT NULL, 
	owner_id VARCHAR(80), 
	dedupe_key VARCHAR(256) NOT NULL, 
	payload JSONB NOT NULL, 
	status VARCHAR(32) NOT NULL, 
	available_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	started_at TIMESTAMP WITH TIME ZONE, 
	finished_at TIMESTAMP WITH TIME ZONE, 
	attempts INTEGER NOT NULL, 
	progress JSONB NOT NULL, 
	result JSONB, 
	error JSONB, 
	usage JSONB, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(owner_id) REFERENCES knowledge_users (id), 
	UNIQUE (dedupe_key)
);

CREATE INDEX ix_knowledge_jobs_available_at ON knowledge_jobs (available_at);

CREATE INDEX ix_knowledge_jobs_kind ON knowledge_jobs (kind);

CREATE INDEX ix_knowledge_jobs_owner_id ON knowledge_jobs (owner_id);

CREATE INDEX ix_knowledge_jobs_status ON knowledge_jobs (status);

CREATE TABLE ontology_relations (
	id VARCHAR(80) NOT NULL, 
	from_concept_id VARCHAR(80) NOT NULL, 
	to_concept_id VARCHAR(80) NOT NULL, 
	type VARCHAR(48) NOT NULL, 
	summary TEXT, 
	conditions TEXT, 
	status VARCHAR(48) NOT NULL, 
	origin VARCHAR(80) NOT NULL, 
	evidence_refs JSONB NOT NULL, 
	extractor JSONB NOT NULL, 
	revision INTEGER NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(from_concept_id) REFERENCES ontology_concepts (id), 
	FOREIGN KEY(to_concept_id) REFERENCES ontology_concepts (id)
);

CREATE INDEX ix_ontology_relations_from_concept_id ON ontology_relations (from_concept_id);

CREATE INDEX ix_ontology_relations_to_concept_id ON ontology_relations (to_concept_id);

CREATE TABLE personal_wiki_pages (
	id VARCHAR(80) NOT NULL, 
	owner_id VARCHAR(80) NOT NULL, 
	topic VARCHAR(200) NOT NULL, 
	topic_key VARCHAR(64) NOT NULL, 
	title VARCHAR(300) NOT NULL, 
	summary TEXT NOT NULL, 
	content TEXT NOT NULL, 
	conditions JSONB NOT NULL, 
	limitations JSONB NOT NULL, 
	citations JSONB NOT NULL, 
	source_revision_ids JSONB NOT NULL, 
	origin_messages JSONB NOT NULL, 
	version INTEGER NOT NULL, 
	user_edited BOOLEAN NOT NULL, 
	deleted_at TIMESTAMP WITH TIME ZONE, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(owner_id) REFERENCES knowledge_users (id)
);

CREATE INDEX ix_personal_wiki_pages_owner_id ON personal_wiki_pages (owner_id);

CREATE INDEX ix_personal_wiki_pages_updated_at ON personal_wiki_pages (updated_at);

CREATE UNIQUE INDEX uq_personal_wiki_active_topic ON personal_wiki_pages (owner_id, topic_key) WHERE deleted_at IS NULL;

CREATE TABLE retrieval_runs (
	id VARCHAR(80) NOT NULL, 
	owner_id VARCHAR(80) NOT NULL, 
	request JSONB NOT NULL, 
	snapshot_id VARCHAR(80) NOT NULL, 
	revision_ids JSONB NOT NULL, 
	result JSONB NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(owner_id) REFERENCES knowledge_users (id)
);

CREATE INDEX ix_retrieval_runs_owner_id ON retrieval_runs (owner_id);

CREATE TABLE document_revisions (
	id VARCHAR(80) NOT NULL, 
	document_id VARCHAR(80) NOT NULL, 
	revision INTEGER NOT NULL, 
	content TEXT NOT NULL, 
	content_hash VARCHAR(64) NOT NULL, 
	raw_path TEXT NOT NULL, 
	media_type VARCHAR(100) NOT NULL, 
	metadata_json JSONB NOT NULL, 
	metadata_version INTEGER NOT NULL, 
	metadata_hash VARCHAR(64) NOT NULL, 
	review_status VARCHAR(32) NOT NULL, 
	index_status VARCHAR(32) NOT NULL, 
	index_snapshot_id VARCHAR(80), 
	read_scope VARCHAR(32) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (document_id, revision), 
	FOREIGN KEY(document_id) REFERENCES documents (id)
);

CREATE INDEX ix_document_revisions_document_id ON document_revisions (document_id);

CREATE INDEX ix_document_revisions_review_status ON document_revisions (review_status);

CREATE TABLE messages (
	id VARCHAR(80) NOT NULL, 
	conversation_id VARCHAR(80) NOT NULL, 
	role VARCHAR(16) NOT NULL, 
	content TEXT NOT NULL, 
	response_mode VARCHAR(16), 
	extended BOOLEAN, 
	run_id VARCHAR(80), 
	status VARCHAR(32) NOT NULL, 
	citations JSONB NOT NULL, 
	relations JSONB NOT NULL, 
	source_views JSONB NOT NULL, 
	warnings JSONB NOT NULL, 
	usage JSONB, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(conversation_id) REFERENCES conversations (id)
);

CREATE INDEX ix_messages_conversation_id ON messages (conversation_id);

CREATE INDEX ix_messages_conversation_order ON messages (conversation_id, created_at, id);

CREATE INDEX ix_messages_run_id ON messages (run_id);

CREATE TABLE personal_wiki_revisions (
	id VARCHAR(80) NOT NULL, 
	page_id VARCHAR(80) NOT NULL, 
	version INTEGER NOT NULL, 
	parent_version INTEGER, 
	restored_from_version INTEGER, 
	operation VARCHAR(32) NOT NULL, 
	job_id VARCHAR(80), 
	snapshot JSONB NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (page_id, version), 
	FOREIGN KEY(page_id) REFERENCES personal_wiki_pages (id), 
	FOREIGN KEY(job_id) REFERENCES knowledge_jobs (id)
);

CREATE INDEX ix_personal_wiki_revisions_page_id ON personal_wiki_revisions (page_id);

CREATE TABLE answer_runs (
	id VARCHAR(80) NOT NULL, 
	owner_id VARCHAR(80) NOT NULL, 
	conversation_id VARCHAR(80) NOT NULL, 
	user_message_id VARCHAR(80) NOT NULL, 
	message_id VARCHAR(80) NOT NULL, 
	client_request_id VARCHAR(128) NOT NULL, 
	request_hash VARCHAR(64) NOT NULL, 
	request JSONB NOT NULL, 
	retry_of_run_id VARCHAR(80), 
	status VARCHAR(32) NOT NULL, 
	last_seq INTEGER NOT NULL, 
	error JSONB, 
	usage JSONB, 
	warnings JSONB NOT NULL, 
	metrics JSONB NOT NULL, 
	generation_config JSONB NOT NULL, 
	retrieval_run_id VARCHAR(80), 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	started_at TIMESTAMP WITH TIME ZONE, 
	finished_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_answer_owner_request UNIQUE (owner_id, client_request_id), 
	FOREIGN KEY(owner_id) REFERENCES knowledge_users (id), 
	FOREIGN KEY(conversation_id) REFERENCES conversations (id), 
	FOREIGN KEY(user_message_id) REFERENCES messages (id), 
	FOREIGN KEY(message_id) REFERENCES messages (id), 
	FOREIGN KEY(retry_of_run_id) REFERENCES answer_runs (id), 
	FOREIGN KEY(retrieval_run_id) REFERENCES retrieval_runs (id)
);

CREATE INDEX ix_answer_runs_conversation_id ON answer_runs (conversation_id);

CREATE INDEX ix_answer_runs_owner_id ON answer_runs (owner_id);

CREATE INDEX ix_answer_runs_status ON answer_runs (status);

CREATE TABLE concept_source_views (
	id VARCHAR(80) NOT NULL, 
	concept_id VARCHAR(80) NOT NULL, 
	source_revision_id VARCHAR(80) NOT NULL, 
	aspect VARCHAR(80) NOT NULL, 
	summary TEXT NOT NULL, 
	conditions TEXT, 
	attribution JSONB NOT NULL, 
	metadata_version INTEGER NOT NULL, 
	metadata_hash VARCHAR(64) NOT NULL, 
	input_hash VARCHAR(64) NOT NULL, 
	evidence_refs JSONB NOT NULL, 
	status VARCHAR(48) NOT NULL, 
	extraction_status VARCHAR(48) NOT NULL, 
	extractor JSONB NOT NULL, 
	supersedes_id VARCHAR(80), 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(concept_id) REFERENCES ontology_concepts (id), 
	FOREIGN KEY(source_revision_id) REFERENCES document_revisions (id)
);

CREATE INDEX ix_concept_source_views_concept_id ON concept_source_views (concept_id);

CREATE INDEX ix_concept_source_views_source_revision_id ON concept_source_views (source_revision_id);

CREATE INDEX ix_concept_source_views_status ON concept_source_views (status);

CREATE TABLE document_attachments (
	id VARCHAR(80) NOT NULL, 
	owner_id VARCHAR(80) NOT NULL, 
	conversation_id VARCHAR(80) NOT NULL, 
	source_revision_id VARCHAR(80) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(owner_id) REFERENCES knowledge_users (id), 
	FOREIGN KEY(conversation_id) REFERENCES conversations (id), 
	FOREIGN KEY(source_revision_id) REFERENCES document_revisions (id)
);

CREATE INDEX ix_document_attachments_conversation_id ON document_attachments (conversation_id);

CREATE INDEX ix_document_attachments_owner_id ON document_attachments (owner_id);

CREATE TABLE document_metadata_history (
	id VARCHAR(80) NOT NULL, 
	source_revision_id VARCHAR(80) NOT NULL, 
	version INTEGER NOT NULL, 
	metadata_json JSONB NOT NULL, 
	changed_by VARCHAR(80) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (source_revision_id, version), 
	FOREIGN KEY(source_revision_id) REFERENCES document_revisions (id), 
	FOREIGN KEY(changed_by) REFERENCES knowledge_users (id)
);

CREATE TABLE document_review_decisions (
	id VARCHAR(80) NOT NULL, 
	source_revision_id VARCHAR(80) NOT NULL, 
	reviewer_id VARCHAR(80) NOT NULL, 
	decision VARCHAR(32) NOT NULL, 
	reason TEXT NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(source_revision_id) REFERENCES document_revisions (id), 
	FOREIGN KEY(reviewer_id) REFERENCES knowledge_users (id)
);

CREATE INDEX ix_document_review_decisions_source_revision_id ON document_review_decisions (source_revision_id);

CREATE TABLE passages (
	id VARCHAR(80) NOT NULL, 
	source_revision_id VARCHAR(80) NOT NULL, 
	ordinal INTEGER NOT NULL, 
	text TEXT NOT NULL, 
	locator TEXT NOT NULL, 
	start_offset INTEGER, 
	end_offset INTEGER, 
	embedding_text TEXT NOT NULL, 
	input_hash VARCHAR(64) NOT NULL, 
	excluded BOOLEAN NOT NULL, 
	exclusion_reason TEXT, 
	PRIMARY KEY (id), 
	UNIQUE (source_revision_id, ordinal), 
	FOREIGN KEY(source_revision_id) REFERENCES document_revisions (id)
);

CREATE INDEX ix_passages_input_hash ON passages (input_hash);

CREATE INDEX ix_passages_source_revision_id ON passages (source_revision_id);

CREATE TABLE personal_wiki_message_states (
	owner_id VARCHAR(80) NOT NULL, 
	message_id VARCHAR(80) NOT NULL, 
	conversation_id VARCHAR(80) NOT NULL, 
	page_id VARCHAR(80), 
	generation INTEGER NOT NULL, 
	is_suppressed BOOLEAN NOT NULL, 
	suppression_reason VARCHAR(64), 
	suppressed_at TIMESTAMP WITH TIME ZONE, 
	last_job_id VARCHAR(80), 
	last_policy VARCHAR(64), 
	last_outcome VARCHAR(32), 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (owner_id, message_id), 
	FOREIGN KEY(owner_id) REFERENCES knowledge_users (id), 
	FOREIGN KEY(message_id) REFERENCES messages (id), 
	FOREIGN KEY(conversation_id) REFERENCES conversations (id), 
	FOREIGN KEY(page_id) REFERENCES personal_wiki_pages (id), 
	FOREIGN KEY(last_job_id) REFERENCES knowledge_jobs (id)
);

CREATE INDEX ix_personal_wiki_message_states_conversation_id ON personal_wiki_message_states (conversation_id);

CREATE TABLE research_items (
	id VARCHAR(80) NOT NULL, 
	owner_id VARCHAR(80) NOT NULL, 
	conversation_id VARCHAR(80), 
	query TEXT NOT NULL, 
	title TEXT NOT NULL, 
	url TEXT NOT NULL, 
	metadata_json JSONB NOT NULL, 
	content TEXT, 
	read_scope VARCHAR(32) NOT NULL, 
	relevance TEXT, 
	limitations JSONB NOT NULL, 
	usage JSONB, 
	transferred_revision_id VARCHAR(80), 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(owner_id) REFERENCES knowledge_users (id), 
	FOREIGN KEY(conversation_id) REFERENCES conversations (id), 
	FOREIGN KEY(transferred_revision_id) REFERENCES document_revisions (id)
);

CREATE INDEX ix_research_items_owner_id ON research_items (owner_id);

CREATE TABLE answer_event_batches (
	id VARCHAR(80) NOT NULL, 
	run_id VARCHAR(80) NOT NULL, 
	first_seq INTEGER NOT NULL, 
	last_seq INTEGER NOT NULL, 
	events JSONB NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_answer_event_start UNIQUE (run_id, first_seq), 
	FOREIGN KEY(run_id) REFERENCES answer_runs (id)
);

CREATE INDEX ix_answer_event_batches_run_id ON answer_event_batches (run_id);

CREATE INDEX ix_answer_event_replay ON answer_event_batches (run_id, last_seq);

CREATE TABLE passage_embeddings (
	id VARCHAR(80) NOT NULL, 
	passage_id VARCHAR(80) NOT NULL, 
	profile_id VARCHAR(160) NOT NULL, 
	embedding_id VARCHAR(80) NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (passage_id, profile_id), 
	FOREIGN KEY(passage_id) REFERENCES passages (id), 
	FOREIGN KEY(embedding_id) REFERENCES embedding_records (id)
);

CREATE INDEX ix_passage_embeddings_passage_id ON passage_embeddings (passage_id);
