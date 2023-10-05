#!/usr/bin/env python

from os import path, getenv
from setuptools import setup
from codecs import open

VERSION = [0, 14, 2]
readme = open('README.rst').read()

setup(
    name='sqlalchemy-chdb',
    version='.'.join('%d' % v for v in VERSION[0:3]),
    description='ChDB SQLAlchemy Dialect',
    long_description = readme,
    author = 'QXIP BV',
    author_email = 'info@qxip.net',
    license = 'Apache License, Version 2.0',
    url = 'https://github.com/cloudflare/sqlalchemy-chdb',
    keywords = "db database cloud analytics clickhouse",
    download_url = 'https://github.com/cloudflare/sqlalchemy-chdb/releases/tag/v0.14.2',
    install_requires = [
        'chdb>=0.14.2',
        'sqlalchemy>=1.0.0',
        'infi.clickhouse_orm>=1.2.0'
    ],
    packages=[
        'sqlalchemy_chdb',
    ],
    package_dir={
        'sqlalchemy_chdb': '.',
    },
    package_data={
        'sqlalchemy_chdb': ['LICENSE.txt'],
    },
    entry_points={
        'sqlalchemy.dialects': [
            'chdb=sqlalchemy_chdb.base',
        ]
    },
    classifiers = [
        'Development Status :: 5 - Production/Stable',

        'Environment :: Console',
        'Environment :: Other Environment',

        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',

        'License :: OSI Approved :: Apache Software License',

        'Operating System :: OS Independent',

        'Programming Language :: SQL',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',

        'Topic :: Database',
        'Topic :: Software Development',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
