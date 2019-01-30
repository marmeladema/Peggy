#!/usr/bin/env python

from setuptools import setup

setup(
    name = 'Peggy',
    version = '0.1',
    description = 'Polyvalent PEG utilities',
    author = 'Elie ROUDNINSKI',
    author_email = 'xademax@gmail.com',
    url = 'https://github.com/marmeladema/Peggy/',
    packages = ['peggy', 'peggy.grammars'],
    package_data = {'peggy': ['grammar.json', 'grammars/waxeye.json']},
    python_requires = '>=3',
    test_suite = 'tests',
    entry_points = {
        'console_scripts': [
            'peggyparse=peggy.__main__:main',
            'peggyconv=peggy.convert:main'
        ],
    }
)
