import logging

from emumon.cli import build_parser, run_once
from emumon.core import (
    ProcessSample,
    alert_message,
    format_table,
    matches,
    over_limit,
    parse_targets,
)


def sample(name="HD-Player.exe", pid=1, ram=500.0, cpu=1.0):
    return ProcessSample(name=name, pid=pid, ram_mb=ram, cpu_percent=cpu)


def test_parse_targets_lowercases_and_drops_empty_pieces():
    assert parse_targets(" BlueStacks, ,Nox ,") == ("bluestacks", "nox")


def test_parse_targets_of_blank_text_is_empty():
    assert parse_targets("  , ") == ()


def test_matches_is_a_case_insensitive_substring_test():
    assert matches("HD-Player.exe", ("hd-player",))
    assert not matches("chrome.exe", ("hd-player", "nox"))


def test_exactly_at_the_limit_is_not_an_alert():
    assert over_limit([sample(ram=2000.0)], 2000.0) == []


def test_just_above_the_limit_is_an_alert():
    s = sample(ram=2000.1)
    assert over_limit([s], 2000.0) == [s]


def test_alert_message_names_process_pid_and_limit():
    msg = alert_message(sample(name="nox.exe", pid=42, ram=3100.0), 2000.0)
    assert "nox.exe" in msg and "42" in msg and "3100" in msg and "2000" in msg


def test_table_lists_biggest_first_and_flags_only_the_ones_over_limit():
    big = sample(name="big.exe", pid=2, ram=3000.0)
    small = sample(name="small.exe", pid=3, ram=100.0)
    lines = format_table([small, big], 2000.0).splitlines()
    assert "big.exe" in lines[1] and "ALERT" in lines[1]
    assert "small.exe" in lines[2] and "ALERT" not in lines[2]
    assert lines[-1].startswith("TOTAL")


def test_table_with_nothing_found_says_so():
    assert format_table([], 2000.0) == "No emulator processes found."


def test_run_once_logs_one_warning_per_process_over_limit(caplog):
    def collector(_targets):
        return [sample(pid=1, ram=3000.0), sample(pid=2, ram=100.0), sample(pid=3, ram=2500.0)]

    logger = logging.getLogger("emumon-test")
    logger.setLevel(logging.WARNING)
    with caplog.at_level(logging.WARNING, logger="emumon-test"):
        table = run_once(collector, ("x",), 2000.0, logger)
    assert len([r for r in caplog.records if r.name == "emumon-test"]) == 2
    assert "TOTAL" in table


def test_parser_defaults():
    args = build_parser().parse_args([])
    assert args.limit_mb == 2000 and args.interval == 10 and not args.once
