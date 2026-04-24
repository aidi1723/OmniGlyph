import argparse
import statistics
import time

from omniglyph.repository import GlyphRepository


def benchmark(sqlite_path: str, glyph: str, iterations: int) -> dict:
    repository = GlyphRepository(sqlite_path)
    durations = []
    for _ in range(iterations):
        start = time.perf_counter()
        repository.find_by_glyph(glyph)
        durations.append((time.perf_counter() - start) * 1000)
    return {
        "iterations": iterations,
        "p50_ms": statistics.median(durations),
        "p95_ms": statistics.quantiles(durations, n=20)[18],
        "max_ms": max(durations),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="data/omniglyph.sqlite3")
    parser.add_argument("--glyph", default="铝")
    parser.add_argument("--iterations", type=int, default=1000)
    args = parser.parse_args()
    print(benchmark(args.db, args.glyph, args.iterations))


if __name__ == "__main__":
    main()
