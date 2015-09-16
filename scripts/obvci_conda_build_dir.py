#!/usr/bin/env python
"""
A script to build and upload all of the conda recipes in
the specified directory.

This script is left around as legacy from before entry_points was used for managing executables.
It will be removed at some point in the future.

"""
import obvci.cli.conda_build_dir as bld_dir
import warnings

if __name__ == '__main__':
    warnings.warn('obvci_conda_build_dir.py has been deprecated. Use obvci_conda_build_dir instead.')
    bld_dir.main()
