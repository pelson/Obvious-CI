#!/usr/bin/env python
import argparse


DEFAULT_CLASS = 'obvci.conda_tools.build_directory.Builder'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="""A script to build and upload all of the conda recipes in
                                                    the specified directory.""")
    parser.add_argument("recipe-dir", help="""The directory containing (multiple) conda recipes
                                              (i.e. each sub-directory must contain a meta.yaml).""")
    parser.add_argument("upload-user", help="""The target user on binstar where build distributions should go.
                                               The BINSTAR_TOKEN environment variable must also be defined.""")
    parser.add_argument("--channel", help="""The target channel on binstar where built distributions should go.""",
                        default='main')
    parser.add_argument("--disable-upload", help="""Disable the uploading of built packages.""",
                        action='store_true')
    parser.add_argument("--builder-class", help="""Fully resolved name of the builder class.""",
                        default=DEFAULT_CLASS)

    args = parser.parse_args()

    mod, name = getattr(args, 'builder_class').rsplit('.', 1)
    module = __import__(mod)
    for sub_mod in mod.split('.')[1:]:
        module = getattr(module, sub_mod)
    cls = getattr(module, name)

    cls(getattr(args, 'recipe-dir'), getattr(args, 'upload-user'), args.channel).main()
