-- Withdrawal is distinct from edit protection. Existing content/revisions remain intact.
ALTER TABLE wiki_pages ADD COLUMN withdrawn boolean NOT NULL DEFAULT false;
