"""Command line entry point: collect samples, print them, log alerts."""

from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from collections.abc import Callable
from pathlib import Path

from .core import (
    DEFAULT_TARGETS,
    ProcessSample,
    alert_message,
    format_table,
    matches,
    over_limit,
    parse_targets,
)

Collector = Callable[[tuple[str, ...]], list[ProcessSample]]


def collect(targets: tuple[str, ...]) -> list[ProcessSample]:
    """Read matching processes with psutil. Imported here so the rest works without it."""
    import psutil

    found = []
    for proc in psutil.process_iter(["pid", "name", "memory_info"]):
        try:
            name = proc.info["name"] or ""
            if not matches(name, targets):
                continue
            found.append((proc, name))
            proc.cpu_percent(None)  # first call always returns 0.0, so prime it
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    time.sleep(0.2)
    samples = []
    for proc, name in found:
        try:
            samples.append(
                ProcessSample(
                    name=name,
                    pid=proc.pid,
                    ram_mb=proc.memory_info().rss / (1024 * 1024),
                    cpu_percent=proc.cpu_percent(None),
                )
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return samples


def run_once(
    collector: Collector,
    targets: tuple[str, ...],
    limit_mb: float,
    logger: logging.Logger,
) -> str:
    """One scan: returns the table to print and logs one warning per process over the limit."""
    samples = collector(targets)
    for s in over_limit(samples, limit_mb):
        logger.warning(alert_message(s, limit_mb))
    return format_table(samples, limit_mb)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="emumon", description="Watch the memory and CPU of Android emulator processes."
    )
    p.add_argument(
        "--limit-mb", type=float, default=2000, help="alert above this RAM (default 2000)"
    )
    p.add_argument("--interval", type=float, default=10, help="seconds between scans (default 10)")
    p.add_argument(
        "--targets",
        default=",".join(DEFAULT_TARGETS),
        help="comma separated process name fragments to watch",
    )
    p.add_argument("--once", action="store_true", help="scan once and exit")
    p.add_argument(
        "--log-file",
        default=str(Path.home() / ".emumon" / "alerts.log"),
        help="where alerts are appended",
    )
    return p


def make_logger(path: str) -> logging.Logger:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("emumon")
    logger.setLevel(logging.WARNING)
    if not logger.handlers:
        handler = logging.FileHandler(path, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(handler)
    return logger


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.limit_mb <= 0 or args.interval <= 0:
        print("--limit-mb and --interval must be positive", file=sys.stderr)
        return 2
    targets = parse_targets(args.targets)
    if not targets:
        print("--targets is empty", file=sys.stderr)
        return 2
    logger = make_logger(args.log_file)
    try:
        while True:
            table = run_once(collect, targets, args.limit_mb, logger)
            if not args.once:
                os.system("cls" if os.name == "nt" else "clear")
            print(table)
            if args.once:
                return 0
            print(f"\nEvery {args.interval:g}s, limit {args.limit_mb:g} MB. Ctrl+C to quit.")
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print()
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
