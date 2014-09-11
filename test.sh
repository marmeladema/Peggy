#!/bin/bash

TMPDIR=$(mktemp -d)

echo -n "Testing grammar tests/a.peg for Python ..."
if ./peggen tests/a.peg -l python -o $TMPDIR/a -a tests/python/test_a.py && python $TMPDIR/a.py
then
	echo " [OK]"
else
	echo " [KO]"
fi

echo -n "Testing grammar tests/a.peg for C ..."
if ./peggen -l c tests/a.peg -a tests/c/test_a.c 1>& $TMPDIR/a.c && gcc -Wall -Werror $TMPDIR/a.c -o $TMPDIR/a && $TMPDIR/a
then
	echo " [OK]"
else
	echo " [KO]"
fi

#./peggen -l c tests/a.peg -a tests/c/test_a.c 1>& a.c

rm -rf $TMPDIR