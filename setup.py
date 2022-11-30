# SPDX-License-Identifier: Apache-2.0
#
# !/usr/bin/env python
import io
import os
from setuptools import setup, find_packages
from src import VERSION

ROOT_DIR = os.path.dirname(__file__)
SOURCE_DIR = os.path.join(ROOT_DIR)

exec(open('src/version.py').read())

with open('./requirements.txt') as reqs_txt:
    requirements = [line for line in reqs_txt]

with open('./requirements-test.txt') as test_reqs_txt:
    test_requirements = [line for line in test_reqs_txt]

setup(
    name='fabric-chaincode-python',
    version=VERSION,
    keywords=['Hyperledger Fabric', 'fabric-chaincode'],
    license='Apache License v2.0',
    description="Hyperledger Fabric Contract and Chaincode implementation for Python.",
    long_description=io.open('README.md', encoding='utf-8').read(),
    author='Hyperledger Community',
    url='https://github.com/ic-matcom/fabric-chaincode-python/',
    download_url='https://github.com/ic-matcom/fabric-chaincode-python/',
    packages=find_packages(exclude=['docs', 'tests*']),
    platforms='any',
    install_requires=requirements,
    tests_require=test_requirements,
    zip_safe=False,
    test_suite='test',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Other Environment',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.8',
        'Topic :: Utilities',
        'License :: OSI Approved :: Apache Software License',
    ],
    include_package_data=True,
)
