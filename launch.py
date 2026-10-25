import sys
from gametest_ai.gui import main

if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--smoke-test":
        from gametest_ai.smoke import run
        raise SystemExit(run(sys.argv[2]))
    main()
