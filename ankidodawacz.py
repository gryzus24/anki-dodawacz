#!/usr/bin/env python3
from __future__ import annotations

from src.Curses.main import main

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print()
