#!/usr/bin/env python

import os, glob
from setuptools import setup, find_packages

install_requires = [line.rstrip() for line in open(os.path.join(os.path.dirname(__file__), "requirements.txt"))]

setup(
    name="chained-aws-lambda",
    version="0.0.8",
    url='https://github.com/chanzuckerberg/chained-aws-lambda',
    license='Apache Software License',
    author='Human Cell Atlas contributors',
    author_email='tonytung@chanzuckerberg.com',
    description='chain work using AWS lambdas',
    long_description=open('README.md').read(),
    install_requires=install_requires,
    extras_require={},
    packages=find_packages("src"),
    package_dir={"":"src"},
    scripts=glob.glob('scripts/*.py'),
    data_files=[('share/chained-aws-lambda/templates', glob.glob('templates/*'))],
    platforms=['MacOS X', 'Posix'],
    zip_safe=False,
    test_suite='test',
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
