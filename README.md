# emumon

A small command line tool that watches the memory and CPU of Android emulator processes
(BlueStacks, LDPlayer, Nox, MEmu and `adb`) and writes a warning to a log file when one of
them goes over a memory limit.

It is useful when an emulator runs for many hours, for example during automated testing or
long unattended sessions, and you want to notice a memory leak before it freezes the machine.

## Install

```bash
pip install .
```

Python 3.10 or newer. The only dependency is [psutil](https://pypi.org/project/psutil/).

## Use

```bash
emumon                            # live table, refreshed every 10 s, alert above 2000 MB
emumon --limit-mb 4000 --interval 5
emumon --targets "bluestacks,nox" # only these process names (substring, any case)
emumon --once                     # one scan, then exit (good for scripts and cron)
```

Alerts are appended to `~/.emumon/alerts.log` (change it with `--log-file`):

```
2026-10-21 09:14:02,311 WARNING HD-Player.exe (pid 8120) is using 3120 MB, above the 2000 MB limit
```

## How it is organised

- `core.py` is pure logic: matching names, finding processes over the limit, formatting the
  table. It has no screen output and does not touch processes, so it is tested without any
  emulator.
- `cli.py` reads real processes with psutil, prints, and logs.

## Tests

```bash
pip install -e ".[dev]"
pytest
```

## Notes

Memory is the resident set size (RSS) of each process. CPU is measured over a short sample,
because the first reading psutil returns for a process is always 0.

## License

MIT
