# Offline regression evaluation

These are the two user regression questions, not an independent holdout set. Keep the same approved source revisions and metadata for a technology comparison. Test newly added original documents separately as an expanded-corpus run.

`evaluate_rag_pipeline.py` uses an existing active account and the normal access checks. It records a dedicated retrieval run and local artifacts; it does not create a login session, conversation, user, or password. It loads the existing server configuration internally. Never pass secrets on the command line or publish `.env`.

Run from the repository root with the application virtual environment:

```powershell
.\.venv\Scripts\python.exe scripts\v2\evaluate_rag_pipeline.py --label baseline --baseline-ref HEAD --output var\rag-evaluation\RUN\baseline
.\.venv\Scripts\python.exe scripts\v2\evaluate_rag_pipeline.py --label after --manifest var\rag-evaluation\RUN\baseline\corpus-manifest.json --runtime-config .env.rag.local --output var\rag-evaluation\RUN\after
```

Select retrieval settings through `OW_RERANKER_*` and `OW_RETRIEVAL_*`. `--runtime-config` loads only these non-secret settings without changing generation or identity settings. `pipelineConfig` and `retrieval.pipeline` record the selected configuration and actual reranking execution. A changed manifest fails the comparison. Code hashes and generated prompt messages are recorded for new runs, while a baseline from Git also retains its extracted backend snapshot. The former LightRAG experiment and its graph-mode CLI option were removed at the user's request; saved experiment records are historical evidence, not active commands.

RAGChecker runs in a separate environment so its research dependencies do not alter the application environment:

```powershell
.\.venv\Scripts\python.exe -m venv var\rag-evaluation\.venv-checker
.\var\rag-evaluation\.venv-checker\Scripts\python.exe -m pip install -r backend\requirements-ragchecker.txt
.\var\rag-evaluation\.venv-checker\Scripts\python.exe scripts\v2\check_rag_results.py var\rag-evaluation\RUN\baseline\results.json --output var\rag-evaluation\RUN\baseline\ragchecker.json --cache var\rag-evaluation\RUN\judge-cache
```

The official package performs claim extraction and entailment through its supported custom callback, using the application's actual Responses provider. The checker rejects incomplete question sets, empty extraction, and incorrect label counts instead of accepting RefChecker's default `Neutral` padding. It caps provider calls and caches valid responses. A failed run is preserved; resume with a fresh output path and the same cache. Include both attempts' paid usage in total evaluation cost. Cache hits have no new provider usage.

`claim_recall`, `context_precision`, and `faithfulness` are model judgments. Read the extracted claims and use the manual checks in `regression_reference.json` before drawing conclusions. Korean readability, citation correctness, and experiment-condition alignment are not proven by a score. Using the same model family for answering and judging can correlate errors. The concise reference requires core facts; it does not require every optional experiment detail.

Report measured wall time and observed tokens separately from estimated dollar costs. Local CPU stages have elapsed time but no API token charge; that does not mean zero compute cost. Index construction and evaluation calls are separate from per-question serving cost. Unknown provider usage stays unknown. A two-question single run is a smoke comparison, not a statistical performance estimate.
