#!/usr/bin/env python

from distutils.core import setup

setup(
    name = 'Peggy',
    version = '0.1',
    description = 'Polyvalent PEG utilities',
    author = 'Elie ROUDNINSKI',
    author_email = 'xademax@gmail.com',
    url = 'https://github.com/marmeladema/Peggy/',
    packages = ['peggy', 'peggy.grammars'],
    package_data = {'peggy': ['grammar.json', 'grammars/waxeye.json']},
    scripts = ['peggyconv', 'peggyparse']
)