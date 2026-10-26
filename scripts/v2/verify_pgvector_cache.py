"""Compare PostgreSQL exact cosine with frozen numpy cache; performs no API calls."""
import argparse
import asyncio
import json
from pathlib import Path

import numpy as np
from sqlalchemy import select

from knowledge.core.database import get_engine, get_session_factory
from knowledge.documents.entities import EmbeddingRecord, Passage, PassageEmbedding
from knowledge.migration.evaluation import ZIP_SHA, stable
from knowledge.registry import load_entities


async def verify(args):
    load_entities()
    root = Path(args.evaluation_dir)
    chunks = [json.loads(s) for s in (root / "data/chunks.jsonl").read_text().splitlines()]
    excluded = set(json.loads((root / "navigation_chunk_filter_v1.json").read_text())["excluded_chunk_ids"])
    corpus = np.load(root / "cache" / f"corpus-{args.model}.npz", allow_pickle=False)["vectors"][:, :1536].astype(np.float64)
    queries = np.load(root / "cache" / f"queries-{args.model}.npz", allow_pickle=False)["vectors"][:, :1536].astype(np.float64)
    corpus /= np.linalg.norm(corpus, axis=1, keepdims=True)
    queries /= np.linalg.norm(queries, axis=1, keepdims=True)
    kept = [i for i, c in enumerate(chunks) if c["chunk_id"] not in excluded]
    pid_to_index = {stable("psg", ZIP_SHA + c["chunk_id"]): i for i, c in enumerate(chunks)}
    api_dim, transform = (3072, "prefix_l2") if args.model.endswith("large") else (1536, "native")
    profile = f"openai:{args.model}:api{api_dim}:stored1536:{transform}:v1"
    sessions, maximum_error, violations = get_session_factory(), 0.0, []
    async with sessions() as session:
        for number, query in enumerate(queries):
            distances = 1 - corpus @ query
            cutoff = sorted(distances[kept])[args.top_k - 1]
            distance = EmbeddingRecord.vector.cosine_distance(query.tolist())
            rows = (await session.execute(select(Passage.id, distance.label("distance"))
                .join(PassageEmbedding, PassageEmbedding.passage_id == Passage.id)
                .join(EmbeddingRecord, EmbeddingRecord.id == PassageEmbedding.embedding_id)
                .where(Passage.excluded.is_(False), PassageEmbedding.profile_id == profile)
                .order_by(distance, Passage.id).limit(args.top_k))).all()
            if len(rows) != args.top_k:
                violations.append({"query": number, "reason": "insufficient_indexed_rows"})
            for passage_id, actual in rows:
                index = pid_to_index[passage_id]
                error = abs(float(actual) - float(distances[index]))
                maximum_error = max(maximum_error, error)
                if error > args.tolerance or distances[index] > cutoff + args.tolerance:
                    violations.append({"query": number, "reason": "distance_or_topk_mismatch", "error": error})
    await get_engine().dispose()
    result = {"status": "passed" if not violations else "failed", "queryCount": len(queries),
        "corpusPassages": len(kept), "topK": args.top_k, "tolerance": args.tolerance,
        "maximumCosineDistanceDifference": maximum_error, "profile": profile,
        "violations": violations, "apiCalls": 0,
        "limitation": "Exact cosine storage/search verification; not an independent quality holdout."}
    if args.output:
        Path(args.output).write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return not violations


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--evaluation-dir", required=True)
    p.add_argument("--model", default="text-embedding-3-large", choices=["text-embedding-3-small", "text-embedding-3-large"])
    p.add_argument("--top-k", type=int, default=10)
    p.add_argument("--tolerance", type=float, default=1e-5)
    p.add_argument("--output")
    raise SystemExit(0 if asyncio.run(verify(p.parse_args())) else 1)
