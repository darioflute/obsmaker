#!/usr/bin/env python
"""Setup script fo installing the fifipy library."""

from distutils.core import setup
import json

with open('obsmaker/version.json') as fp:
    _info = json.load(fp)

config = {
    'name': 'obsmaker',
    'version': _info['version'],
    'description': 'FIFI-LS AOR maker',
    'long_description': 'Program to make scan description files from AORs for FIFI-LS observations',
    'author': 'Dario Fadda',
    'author_email': 'darioflute@gmail.com',
    'url': 'https://github.com/darioflute/obsmaker.git',
    'download_url': 'https://github.com/darioflute/obsmaker',
    'license': 'GPLv3+',
    'packages': ['obsmaker'],
    'scripts': ['bin/obsmaker'],
    'include_package_data':True,
    'package_data':{'obsmaker':['version.json','data/*']},
    'install_requires': ['numpy', 'pandas', 'unidecode'],
    'classifiers':[
            "Programming Language :: Python :: 3",
            "License :: OSI Approved :: GPLv3+ License",
            "Operating System :: OS Independent",
            "Intended Audience :: Science/Research", 
            "Development Status :: 4 - Beta",
            "Topic :: Scientific/Engineering :: Visualization",
            ]
}

setup(**config)
