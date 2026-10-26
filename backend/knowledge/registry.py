"""Explicit entity registration for migrations. App startup never creates tables."""
import importlib

ENTITY_MODULES = (
    "identity", "conversations", "answers", "rag", "documents", "ontology",
    "personal_wiki", "research", "jobs", "migration",
)


def load_entities():
    for feature in ENTITY_MODULES:
        importlib.import_module(f"knowledge.{feature}.entities")
