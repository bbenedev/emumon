"""Pure logic for emumon: no screen output and no process access, so it can be tested alone."""

from __future__ import annotations

from dataclasses import dataclass

DEFAULT_TARGETS = ("bluestacks", "hd-player", "ldplayer", "nox", "memu", "adb")


@dataclass(frozen=True)
class ProcessSample:
    name: str
    pid: int
    ram_mb: float
    cpu_percent: float


def parse_targets(text: str) -> tuple[str, ...]:
    """'BlueStacks, nox' -> ('bluestacks', 'nox'). Empty pieces are dropped."""
    parts = tuple(p.strip().lower() for p in text.split(","))
    return tuple(p for p in parts if p)


def matches(process_name: str, targets: tuple[str, ...]) -> bool:
    """True if any target is a substring of the process name, ignoring case."""
    lowered = process_name.lower()
    return any(t in lowered for t in targets)


def over_limit(samples: list[ProcessSample], limit_mb: float) -> list[ProcessSample]:
    """Processes strictly above the limit. Exactly at the limit is not an alert."""
    return [s for s in samples if s.ram_mb > limit_mb]


def alert_message(sample: ProcessSample, limit_mb: float) -> str:
    return (
        f"{sample.name} (pid {sample.pid}) is using {sample.ram_mb:.0f} MB, "
        f"above the {limit_mb:.0f} MB limit"
    )


def format_table(samples: list[ProcessSample], limit_mb: float) -> str:
    """Text table, biggest memory user first. Rows above the limit end with '<< ALERT'."""
    if not samples:
        return "No emulator processes found."
    rows = sorted(samples, key=lambda s: s.ram_mb, reverse=True)
    lines = [f"{'PROCESS':<24}{'PID':>8}{'RAM MB':>10}{'CPU %':>8}"]
    for s in rows:
        flag = "  << ALERT" if s.ram_mb > limit_mb else ""
        lines.append(f"{s.name:<24}{s.pid:>8}{s.ram_mb:>10.1f}{s.cpu_percent:>8.1f}{flag}")
    total = sum(s.ram_mb for s in rows)
    lines.append(f"{'TOTAL':<24}{'':>8}{total:>10.1f}")
    return "\n".join(lines)
