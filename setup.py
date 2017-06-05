#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

readme = open('README.rst').read()
history = open('docs/HISTORY.rst').read()
version = "1.0"

requirements_file = [line.strip() for line in open('requirements.txt').readlines()
                     if line.strip() and not line.startswith('#')]
requirements = requirements_file

setup(
    name='''netconf-checker''',
    version=version,
    description='''A tool to load, commit check and diff vendor router/switch configs''',
    long_description=readme + '\nFirst release just does Juniper devices\n\n' + history,
    author='''Ed Crewe''',
    author_email='''edmundcrewe@gmail.com''',
    url='''https://github.com/edcrewe/netconf-checker''',
    packages=find_packages(where='.', exclude=('tests',)),
    package_dir={'''netconf-checker''':
                 '''netconfchecker'''},
    include_package_data=True,
    install_requires=requirements,
    license="Apache 2.0",
    zip_safe=False,
    keywords='''netconf-checker''',
    classifiers=[
        'Development Status :: Perpetual Beta',
        'License :: Apache 2.0',
        'Natural Language :: English',
        'Programming Language :: Python :: 2.7',
    ],
    test_suite='tests'
)
