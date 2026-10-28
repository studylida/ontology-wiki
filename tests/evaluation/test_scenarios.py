"""Real ingestion/retrieval tracing. Fixture output is NOT an answer-quality score."""
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import secrets
import subprocess
import time
from uuid import uuid4

from knowledge.core.config import Settings
from knowledge.rag.context import serialized_evidence

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('evaluation_server_support', ROOT / 'tests/foundation/conftest.py')
support = importlib.util.module_from_spec(spec)
spec.loader.exec_module(support)
DATASET = Path(__file__).with_name('cases.json')


def test_synthetic_work_questions_are_traceable(database_factory, tmp_path):
    dataset = json.loads(DATASET.read_text(encoding='utf-8'))
    records, sources, conversations = [], {}, {}
    # Explicit fixtures, no inherited API key, temporary DB and files owned by this test only.
    with database_factory() as database:
        env = {**os.environ, 'PYTHONPATH': str(ROOT / 'backend'), 'OW_DATABASE_URL': database.url,
               'OW_AUTH_SECRET': secrets.token_hex(32), 'OW_BOOTSTRAP_PASSWORD': secrets.token_urlsafe(24),
               'OW_PROVIDER_MODE': 'fixture', 'OW_STORAGE_PATH': str(tmp_path / 'raw'), 'OW_RERANKER_MODE': 'disabled'}
        env.pop('OPENAI_API_KEY', None)
        support.cli(env, 'migrate', '--database-name', database.name)
        support.cli(env, 'create-user', '--username', 'evaluation-employee')
        server = support.Server(env, tmp_path)
        try:
            server.start()
            assert server.request('GET', '/health').json()['providerMode'] == 'fixture'
            login = server.request('POST', '/auth/login', json={'username': 'evaluation-employee', 'password': env['OW_BOOTSTRAP_PASSWORD']})
            assert login.status_code == 200
            token = login.json()['accessToken']

            def request(method, path, **kwargs):
                response = server.request(method, path, token=token, **kwargs)
                assert response.is_success, response.text
                return response.json()

            def ingest():
                for doc in dataset['documents']:
                    raw = doc['content'].encode('utf-8')
                    item = request('POST', '/documents', data={'title': doc['title']},
                                   files={'file': (doc['filename'], raw, 'text/markdown')})
                    processed = json.loads(support.cli(env, 'worker', '--once').stdout)
                    assert processed['status'] == 'succeeded', processed
                    source = request('GET', f"/documents/{item['documentId']}/passages?revisionId={item['revisionId']}")
                    actual = server.request('GET', f"/documents/{item['documentId']}/raw", token=token).content
                    assert actual == raw
                    sources[doc['key']] = {**item, 'rawSha256': hashlib.sha256(raw).hexdigest(),
                        'rawText': doc['content'], 'processed': source}

            for case in dataset['cases']:
                if not case.get('empty_corpus') and not sources:
                    ingest()
                parent = case.get('follow_up_of')
                conv = conversations[parent] if parent else request('POST', '/conversations', json={'title': case['id']})['id']
                conversations[case['id']] = conv
                began = time.monotonic()
                accepted = request('POST', f'/conversations/{conv}/turns',
                    json={'question': case['question'], 'requestId': uuid4().hex})
                deadline = time.monotonic() + 35
                while True:
                    run = request('GET', '/answer-runs/' + accepted['runId'])
                    if run['status'] in ('completed', 'failed', 'cancelled', 'interrupted'):
                        break
                    assert time.monotonic() < deadline, 'Evaluation run did not finish'
                    time.sleep(.05)
                retrieval = run.get('retrieval') or {}
                evidence = retrieval.get('evidence', [])
                candidate_revisions = {c['sourceRevisionId'] for c in retrieval.get('candidates', [])}
                context_revisions = {c['sourceRevisionId'] for c in evidence}
                requirements = [{'documentKey': key, 'inCandidates': sources[key]['revisionId'] in candidate_revisions,
                                 'inFinalContext': sources[key]['revisionId'] in context_revisions}
                                for key in case['required_documents']]
                records.append({'case': case, 'run': run,
                    'observedElapsedMs': round((time.monotonic() - began) * 1000, 2),
                    'serializedModelEvidence': serialized_evidence(evidence),
                    'requiredDocumentPresence': requirements,
                    'review': {'retrievalSemanticAdequacy': None,
                               'answerQuality': 'not_evaluated_fixture_generation',
                               'businessUsefulness': 'not_evaluated_no_employee_review',
                               'reviewer': None, 'notes': []}})
                assert run['status'] == 'completed', run.get('error')
                assert '검증용 fixture' in run['answer']['content']
                assert len({e['passageId'] for e in evidence}) == len(evidence)
                assert len(serialized_evidence(evidence)) <= Settings().context_max_characters
                known = {p['id']: (p, s) for s in sources.values() for p in s['processed']['passages']}
                for e in evidence:
                    p, s = known[e['passageId']]
                    assert not p['excluded'] and s['revisionId'] == e['sourceRevisionId']
                    assert s['processed']['content'][p['startOffset']:p['endOffset']] == p['text'] == e['text']
                assert run['usage']['generation']['promptEvidenceIds'] == [e['passageId'] for e in evidence]
                for citation in run['answer']['citations']:
                    assert citation['passageId'] in {e['passageId'] for e in evidence}
                if case.get('empty_corpus'):
                    assert retrieval['status'] == 'no_evidence' and not evidence
        finally:
            server.stop()
            # Synthetic material only. A custom output directory must not be docs.
            output = Path(os.environ.get('OW_EVALUATION_OUTPUT', str(Path(os.environ.get('RUNNER_TEMP', tmp_path)) / 'evaluation'))).resolve()
            if output == ROOT / 'docs' or ROOT / 'docs' in output.parents:
                raise ValueError('Evaluation artifacts must not be written into docs')
            output.mkdir(parents=True, exist_ok=True)
            sha = os.environ.get('GITHUB_SHA') or subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
            report = {'dataClassification': dataset['dataClassification'], 'evaluatedAt': datetime.now(timezone.utc).isoformat(),
                'codeCommit': sha, 'datasetSha256': hashlib.sha256(DATASET.read_bytes()).hexdigest(),
                'scope': 'real_ingestion_and_retrieval_with_explicit_fixture_providers',
                'semanticQualityEvaluated': False, 'employeeReviewPerformed': False,
                'settings': {'providerMode': 'fixture', 'rerankerMode': 'disabled',
                             'contextMaxCharacters': Settings().context_max_characters},
                'sources': sources, 'cases': records}
            (output / 'trace.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            presence = [r for c in records for r in c['requiredDocumentPresence']]
            summary = {'casesExecuted': len(records), 'expectedCases': len(dataset['cases']),
                'requiredDocumentsInCandidates': sum(r['inCandidates'] for r in presence),
                'requiredDocumentsInFinalContext': sum(r['inFinalContext'] for r in presence),
                'requiredDocumentChecks': len(presence), 'answerQuality': 'not_evaluated_fixture',
                'businessUsefulness': 'not_evaluated', 'isReleaseScore': False}
            (output / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            print(json.dumps(summary, ensure_ascii=False))
