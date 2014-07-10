Peggy
====

Peggy is a parser generator for Parsing Expression Grammars (PEGs) written in Python.

Features
--------
* Fast
* Low memory requirement
* Multiple target languages
  - Python
  - C (not yet ready)
* AST generation
* Can handle left-recursion
* No dependencies

Dependencies
------------
* Python (tested on 2.6)
* argparse module for Python

Running
-------
Running this command:
  `$ ./peggen --language python --output example my_grammar.peg`
will create a file `example.py` containing python code
which can parse data according to the grammar describe in `my_grammar.peg`.

To get some help, you can always try:
  `$ ./peggen --help`

License
-------
All files are under the permissive MIT license.
Feel free to contribute, report bugs & improve the beast :)
