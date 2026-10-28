"""Use the existing isolated database/server helpers, never an existing company corpus."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('evaluation_foundation_support', ROOT / 'tests/foundation/conftest.py')
support = importlib.util.module_from_spec(spec)
spec.loader.exec_module(support)
database_factory = support.database_factory
