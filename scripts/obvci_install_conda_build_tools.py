#!/usr/bin/env python
"""
Install the packages necessary for building conda
distributions.

Requires conda to be installed and on the path.
There are scripts to help with the installation of
miniconda in the same directory as this script.

"""
from __future__ import print_function
BUILD_PACKAGES = ['conda-build', 'anaconda-client', 'jinja2', 'setuptools']


if __name__ == '__main__':
    import subprocess
    cmd = ['conda', 'install', '--yes', '-n', 'root', '--quiet'] + BUILD_PACKAGES
    subprocess.check_call(cmd)
