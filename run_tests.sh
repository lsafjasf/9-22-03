#!/bin/sh
# Run the full self-test suite plus the streaming differential check.
set -e
cd "$(dirname "$0")"
python3 -m unittest discover -s tests "$@"
python3 scripts/diff_stream.py --iterations 300
