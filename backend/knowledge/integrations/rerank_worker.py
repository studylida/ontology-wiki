"""Offline JSON-lines CrossEncoder worker; run using requirements-rerank.txt."""
import argparse
from importlib.metadata import version
import json
import sys
from time import monotonic


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cpu")
    parser.add_argument("--max-length", type=int, default=1024)
    parser.add_argument("--batch-size", type=int, default=4)
    args = parser.parse_args()
    started = monotonic()
    import torch
    from sentence_transformers import CrossEncoder

    torch.set_num_threads(4)
    model = CrossEncoder(args.model, device=args.device, max_length=args.max_length,
                         local_files_only=True, trust_remote_code=False, token=False,
                         activation_fn=torch.nn.Identity(),
                         model_kwargs={"dtype": torch.float16 if args.device == "cuda" else torch.float32})
    print(json.dumps({"ready": True, "device": args.device,
                      "modelLoadMs": round((monotonic() - started) * 1000, 2),
                      "runtime": {name: version(name) for name in ("sentence-transformers", "transformers", "torch")}}), flush=True)
    for line in sys.stdin:
        request = json.loads(line)
        started = monotonic()
        if args.device == "cuda":
            torch.cuda.reset_peak_memory_stats()
        pairs = [(request["query"], text) for text in request["texts"]]
        lengths = [len(tokens) for tokens in model.tokenizer(pairs, truncation=False)["input_ids"]]
        scores = model.predict(pairs, batch_size=args.batch_size, show_progress_bar=False,
                               convert_to_numpy=True).reshape(-1).tolist()
        print(json.dumps({"id": request["id"], "scores": scores,
                          "inferenceMs": round((monotonic() - started) * 1000, 2),
                          "truncatedPairs": sum(length > args.max_length for length in lengths),
                          "totalPairs": len(pairs), "inputTokens": sum(lengths),
                          "processedTokens": sum(min(length, args.max_length) for length in lengths),
                          "gpuPeakMemoryMiB": round(torch.cuda.max_memory_allocated() / 1024**2, 2)
                          if args.device == "cuda" else None}), flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        # Do not echo candidate text or environment values into application logs.
        print(json.dumps({"error": type(exc).__name__}), flush=True)
        raise SystemExit(1)
