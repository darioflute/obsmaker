[![Anaconda-Server Badge](https://anaconda.org/darioflute/obsmaker/badges/version.svg?branch=master&kill_cache=1&service=github)](https://anaconda.org/darioflute/obsmaker)
[![Anaconda-Server Badge](https://anaconda.org/darioflute/obsmaker/badges/latest_release_date.svg?branch=master&kill_cache=1&service=github)](https://anaconda.org/darioflute/obsmaker)
[![Anaconda-Server Badge](https://anaconda.org/darioflute/obsmaker/badges/license.svg)](https://anaconda.org/darioflute/obsmaker)
[![Anaconda-Server Badge](https://anaconda.org/darioflute/obsmaker/badges/platforms.svg)](https://anaconda.org/darioflute/obsmaker)


# obsmaker
Tool to program FIFI-LS observations starting from AOR files produced with USPOT.

The latest version requires to install python-docx:

conda install -c conda-forge python-docx


# Creating a separate environment
It is advisable to create a separate environment to install and run obsmaker.

```
conda crate -n obsmaker anaconda python=3.7
conda activate
conda install -c conda-forge python-docx
conda install -c darioflute obsmaker
```

to exit from the environment:
```
conda deactivate
```

to remove the environment:
```
conda env remove -n obsmaker
```
# Troubleshooting

On mac-osx it can happen that the lxml does not link properly the lxml2 libraries.
To check if this work, try:

```
python -c 'from lxml import etree'
```

It this does not work, a solution is to reinstall lxml with pip with static libraries:


```
STATIC_DEPS=true pip install lxml==4.6.1
```
