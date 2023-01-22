#!/usr/bin/env python3
from __future__ import annotations

if __name__ == '__main__':
    from src.Curses.main import main

    try:
        main()
    except KeyboardInterrupt:
        print()
