#!/usr/bin/env python3
"""Compatibility wrapper for users/scripts expecting engine/pipeline.py.

Canonical pipeline entrypoint: engine/run_pipeline.py
"""

from run_pipeline import main


if __name__ == "__main__":
    main()
