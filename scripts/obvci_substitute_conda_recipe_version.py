#!/usr/bin/env python
import argparse
import os
import subprocess

def load_version_file(fh):
    vn_context = {}
    exec(fh.read(), vn_context)
    return vn_context['__version__']


def identify_branch_name(directory):
    # TODO: Consider using the tag name too (git describe --tags --exact-match)
    return subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                                   cwd=directory).strip()


def main(conda_dir, version_file, include_git_branch_name=True):
    with open(version_file, 'r') as fh:
        version = load_version_file(fh)
    if include_git_branch_name:
        branch_name = identify_branch_name(conda_dir)
        if branch_name != 'HEAD':
            version = '{}.{}'.format(version, branch_name)
    meta_file = os.path.join(conda_dir, 'meta.yaml')
    with open(meta_file, 'r') as fh:
        meta_content = fh.readlines()
    with open(meta_file, 'w') as fh:
        for line in meta_content:
            if line.strip().startswith('version:'):
                line = '{pre}version: {version!r}\n'.format(pre=line[:line.find('version:')],
                                                          version=version)
            fh.write(line)
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="""A script to update the version specified in a conda
                                                    recipe's meta.yaml.""")
    parser.add_argument("recipe_dir", help="""The directory of the conda recipe.""")
    parser.add_argument("version_file", help="""The file containing a python declaration of __version__.""")
    parser.add_argument('--without-branch-name', help="""Include the branch name 
                                                         (only if 'git rev-parse --abbrev-ref HEAD' != HEAD).""",
                        action='store_true')
    args = parser.parse_args()
    main(args.recipe_dir, args.version_file, include_git_branch_name=not args.without_branch_name)
