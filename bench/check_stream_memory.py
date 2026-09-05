"""Measure real CSV processing in fresh subprocesses; no NER model required.

Run from the repository root: python bench/check_stream_memory.py
RSS includes Python, dependencies, CSV buffers and analyzer caches. The worker
uses fixed-size batches and normal bounded caches; streaming reporting is off.
Results are observations, not hardware-sensitive CI assertions.
"""
import argparse
import csv
import json
import os
import resource
import subprocess
import sys
import tempfile
import time
from pathlib import Path


def worker(rows, chunk_size):
    from allyanonimiser import create_allyanonimiser
    from allyanonimiser.io.stream_processor import StreamProcessor

    ally = create_allyanonimiser(spacy_model=None)
    with tempfile.TemporaryDirectory() as directory:
        source = Path(directory) / "input.csv"
        with source.open("w", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["id", "note"])
            for i in range(rows):
                writer.writerow([i, f"Email person{i}@example.com. " + "plain text " * 80])
        started = time.perf_counter()
        result = StreamProcessor(ally, chunk_size=chunk_size).process_large_file(
            source, "note", Path(directory) / "output.csv",
            active_entity_types=["EMAIL_ADDRESS"], progress_bar=False,
        )
        assert result["total_rows_processed"] == rows
        assert result["total_entities_detected"] == rows
        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        rss_bytes = rss if sys.platform == "darwin" else rss * 1024
        print(json.dumps({"rows": rows, "chunk_size": chunk_size,
                          "input_mib": round(source.stat().st_size / 2**20, 2),
                          "peak_rss_mib": round(rss_bytes / 2**20, 2),
                          "seconds": round(time.perf_counter() - started, 2)}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", nargs="+", type=int, default=[2000, 20000])
    parser.add_argument("--chunk-size", type=int, default=500)
    parser.add_argument("--worker", type=int)
    args = parser.parse_args()
    if args.worker is not None:
        worker(args.worker, args.chunk_size)
        return
    root = str(Path(__file__).resolve().parents[1])
    env = dict(os.environ, PYTHONPATH=os.pathsep.join(filter(None, [root, os.getenv("PYTHONPATH")])))
    for rows in args.rows:
        subprocess.run([sys.executable, __file__, "--worker", str(rows),
                        "--chunk-size", str(args.chunk_size)], env=env, check=True)


if __name__ == "__main__":
    main()
