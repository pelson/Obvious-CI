#!/usr/bin/env python
"""
A script to build and upload all of the conda recipes in
the specified directory.

"""
import argparse
import sys


from obvci.conda_tools.build_directory import Builder


if __name__ == '__main__':
    description = sys.modules[__name__].__doc__
    parser = argparse.ArgumentParser(description=description)
    Builder.define_args(parser)
    args = parser.parse_args()
    Builder.handle_args(args).main()
