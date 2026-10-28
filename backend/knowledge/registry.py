"""Only implemented stage entities belong to the new schema/runtime.

Deferred document/parser/retrieval modules remain reusable source, not startup
requirements. Add their entities here when their implementation stage is wired.
"""
import importlib

ENTITY_MODULES = ("identity", "conversations")


def load_entities():
    for feature in ENTITY_MODULES:
        importlib.import_module(f"knowledge.{feature}.entities")
