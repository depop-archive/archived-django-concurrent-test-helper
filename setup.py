#!/usr/bin/env python
import sys
from codecs import open  # To use a consistent encoding
from os import path
from setuptools import setup
from setuptools.command.test import test as TestCommand


here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

# Get content from __about__.py
about = {}
with open(path.join(here, 'django_concurrent_tests', '__about__.py'), 'r', 'utf-8') as f:
    exec(f.read(), about)


class Tox(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import tox
        errno = tox.cmdline(self.test_args)
        sys.exit(errno)


setup(
    name='django-concurrent-test-helper',
    version=about['__version__'],
    description="Helpers for executing Django app code concurrently within Django tests",
    long_description=long_description,
    author="Anentropic",
    author_email="ego@anentropic.com",
    url="https://github.com/depop/django-concurrent-test-helper",
    packages=[
        'django_concurrent_tests',
        'django_concurrent_tests.management',
        'django_concurrent_tests.management.commands',
    ],
    license='Apache 2.0',
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Framework :: Django',
    ],
    install_requires=[
        'six',
        'tblib',
        'mock',
    ],
    tests_require=[
        'tox>=1.8',
    ],
    cmdclass={'test': Tox},
)
