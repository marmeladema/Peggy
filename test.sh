#!/bin/bash

TMPDIR=$(mktemp -d)

echo "Testing grammar tests/a.peg"
./peggen tests/a.peg -l python -o $TMPDIR/a -a tests/python/test_a.py && python $TMPDIR/a.py

rm -rf $TMPDIR