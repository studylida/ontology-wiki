"""Active runtime contracts, not a blind ban on historical words in documentation."""
import ast
from pathlib import Path
from knowledge.core.config import Settings

ROOT = Path(__file__).resolve().parents[2]


def test_environment_example_only_sets_supported_runtime_settings():
    fields = {'OW_' + name.upper() for name in Settings.model_fields}
    deployment_only = {'OPENAI_API_KEY', 'OW_DEV_DB_PASSWORD'}
    for line in (ROOT / '.env.example').read_text().splitlines():
        if line.strip() and not line.startswith('#'):
            assert line.split('=', 1)[0] in fields | deployment_only


def test_retired_services_and_compatibility_stores_are_absent():
    for path in ['backend/knowledge/research', 'backend/knowledge/personal_wiki',
                 'backend/knowledge/migration/legacy.py', 'backend/knowledge/migration/entities.py',
                 'backend/knowledge/integrations/public_fetch.py', 'backend/knowledge/integrations/public_egress.py',
                 'backend/migrations/v2', 'frontend/src/views/ResearchView.tsx', 'frontend/src/views/PersonalWikiView.tsx']:
        assert not (ROOT / path).exists(), path
    # Code imports must not reach deleted modules; harmless commentary is not considered code.
    removed = ('knowledge.research', 'knowledge.personal_wiki', 'knowledge.migration.legacy',
               'knowledge.migration.entities', 'knowledge.integrations.public_fetch', 'knowledge.integrations.public_egress')
    for path in (ROOT / 'backend/knowledge').rglob('*.py'):
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith(removed), str(path)


def test_frozen_fixture_is_not_presented_as_business_or_semantic_evaluation():
    import json
    data = json.loads((ROOT / 'tests/evaluation/cases.json').read_text())
    assert data['dataClassification'] == 'synthetic_only_not_company_knowledge'
    assert 15 <= len(data['cases']) <= 20
    keys = {d['key'] for d in data['documents']}
    assert len(keys) == len(data['documents'])
    seen = set()
    for case in data['cases']:
        assert case['id'] not in seen
        assert set(case['required_documents']) <= keys
        assert case['key_facts'] and case['avoid_errors'] and case['allowed_interpretations_or_uncertainty']
        assert not case.get('follow_up_of') or case['follow_up_of'] in seen
        assert 'expectedAnswer' not in case
        seen.add(case['id'])
