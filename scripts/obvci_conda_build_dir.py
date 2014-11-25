#!/usr/bin/env python
import argparse

from obvci.conda_tools.build_directory import main


parser = argparse.ArgumentParser(description="""A script to build and upload all of the conda recipes in
                                                the specified directory.""")
parser.add_argument("recipe-dir", help="""The directory containing (multiple) conda recipes
                                          (i.e. each sub-directory must contain a meta.yaml).""")
parser.add_argument("upload-user", help="""The target user on binstar where build distributions should go.
                                           The BINSTAR_TOKEN environment variable must also be defined.""")
parser.add_argument("--channel", help="""The target channel on binstar where built distributions should go.""",
                    default='main')

args = parser.parse_args()
main(getattr(args, 'recipe-dir'), getattr(args, 'upload-user'), args.channel)