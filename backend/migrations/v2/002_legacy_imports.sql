CREATE TABLE legacy_imports (
    id VARCHAR(80) NOT NULL PRIMARY KEY,
    source_system VARCHAR(160) NOT NULL,
    export_sha256 VARCHAR(64) NOT NULL,
    raw_path TEXT NOT NULL,
    counts JSONB NOT NULL,
    record_count INTEGER NOT NULL,
    imported_at TIMESTAMP WITH TIME ZONE NOT NULL,
    UNIQUE (source_system, export_sha256)
);

CREATE INDEX ix_legacy_imports_source_system ON legacy_imports (source_system);

ALTER TABLE legacy_archive
    ADD COLUMN first_import_id VARCHAR(80) REFERENCES legacy_imports(id);

CREATE INDEX ix_legacy_archive_first_import_id ON legacy_archive (first_import_id);
