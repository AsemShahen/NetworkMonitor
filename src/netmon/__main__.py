from __future__ import annotations

import sys


def main(argv: list[str] | None = None) -> None:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--collector" in args:
        from .collector import main as collector_main

        raise SystemExit(collector_main(args))
    from .app import run

    run()


if __name__ == "__main__":
    main()
