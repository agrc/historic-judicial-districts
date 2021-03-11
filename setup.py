#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
setup.py
A module that installs lookback as a module
"""
from glob import glob
from os.path import basename, splitext

from setuptools import find_packages, setup

setup(
    name='lookback',
    version='1.0.0',
    license='MIT',
    description='Determine composition of historic judicial districts.',
    author='AGRC',
    author_email='agrc@utah.gov',
    url='https://github.com/agrc/historic-judicial-districts',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    py_modules=[splitext(basename(path))[0] for path in glob('src/*.py')],
    include_package_data=True,
    zip_safe=True,
    classifiers=[
        # complete classifier list: http://pypi.python.org/pypi?%3Aaction=list_classifiers
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Utilities',
    ],
    project_urls={
        'Issue Tracker': 'https://github.com/agrc/historic-judicial-districts/issues',
    },
    keywords=['gis'],
    install_requires=[
        # 'package==1.0.*'
    ],
    extras_require={
        'tests': [
            'pylint-quotes==0.2.*',
            'pylint==2.5.*',
            'pytest-cov==2.9.*',
            'pytest-instafail==0.4.*',
            'pytest-isort==1.0.*',
            'pytest-pylint==0.14.*',
            'pytest-watch==4.2.*',
            'pytest==4.*',
            'yapf==0.30.*',
            'pytest-mock==3.2.*',
        ]
    },
    setup_requires=[
        'pytest-runner',
    ],
    entry_points={'console_scripts': [
        'lookback = lookback.main:main',
    ]},
)
