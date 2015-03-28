"""
Build all the conda recipes in the given directory sequentially if they do not
already exist on the given binstar channel.
Building is done in order of dependencies (circular dependencies are not supported).
Once a build is complete, the distribution will be uploaded (provided BINSTAR_TOKEN is
defined), and the next package will be processed.

"""
from __future__ import print_function

import os
import subprocess
from argparse import Namespace

from binstar_client.utils import get_binstar
import binstar_client
from conda_build.metadata import MetaData
from conda_build.build import bldpkg_path
import conda.config

from . import order_deps
from . import build
from . import inspect_binstar


def package_built_name(package, root_dir):
    package_dir = os.path.join(root_dir, package)
    meta = MetaData(package_dir)
    return bldpkg_path(meta)


def distribution_exists(binstar_cli, owner, metadata):
    fname = '{}/{}.tar.bz2'.format(conda.config.subdir, metadata.dist())
    try:
        r = binstar_cli.distribution(owner, metadata.name(), metadata.version(),
                                     fname)
        exists = True
    except binstar_client.errors.NotFound:
        exists = False
    return exists


def recipes_to_build(binstar_cli, owner, channel, recipe_metas):
    for meta in recipe_metas:
        if not inspect_binstar.distribution_exists(binstar_cli, owner, meta):
            yield meta


def fetch_metas(directory):
    """
    Get the build metadata of all recipes in a directory.

    The recipes will be sorted by the order of their directory name.

    """
    if os.name == 'nt':
        build_script = 'bld.bat'
    else:
        build_script = 'build.sh'

    packages = []
    for package_name in sorted(os.listdir(directory)):
        package_dir = os.path.join(directory, package_name)
        meta_yaml = os.path.join(package_dir, 'meta.yaml') 

        if os.path.isdir(package_dir) and os.path.exists(meta_yaml):
            # Only include packages which have an appropriate build script.
            # TODO: This could become more flexible by allowing a exclude.lst
            # file in the recipe?
            if os.path.exists(os.path.join(package_dir, build_script)):
                packages.append(MetaData(package_dir))

    return packages


def sort_dependency_order(metas):
    """Sort the metas into the order that they must be built."""
    meta_named_deps = {}
    buildable = [meta.name() for meta in metas]
    for meta in metas:
        all_deps = (meta.get_value('requirements/run', []) +
                    meta.get_value('requirements/build', []))
        # Remove version information from the name.
        all_deps = [dep.split(' ', 1)[0] for dep in all_deps]
        meta_named_deps[meta.name()] = [dep for dep in all_deps if dep in buildable]
    sorted_names = list(order_deps.resolve_dependencies(meta_named_deps))
    return sorted(metas, key=lambda meta: sorted_names.index(meta.name()))


class Builder(object):
    def __init__(self, conda_recipes_root, upload_owner, upload_channel):
        """
        Build a directory of conda recipes sequentially, if they don't already exist on the owner's binstar account.
        If the build does exist on the binstar account, but isn't in the targeted channel, it will be added to upload_channel,
        All built distributions will be uploaded to the owner's channel.

        Note: Recipes may not compute their version/build# at build time.

        """
        self.conda_recipes_root = conda_recipes_root
        self.upload_owner = upload_owner
        self.upload_channel = upload_channel

        self.binstar_token = os.environ.get('BINSTAR_TOKEN', None)
        self.can_upload = self.binstar_token is not None

        if not self.can_upload:
            print('**Build will continue, but no uploads will take place.**')
            print('To automatically upload from this script, define the BINSTAR_TOKEN env variable.')
            print('This is done automatically on the travis-ci system once the PR has been merged.')
        else:
            print('conda build currently leaks all environment variables on windows, therefore the BINSTAR_TOKEN '
                  'is being reset. See https://github.com/conda/conda-build/pull/274 for progress.')
            os.environ['BINSTAR_TOKEN'] = 'Hidden by Obvious-CI'

        self.binstar_cli = get_binstar(Namespace(token=self.binstar_token, site=None))

    def fetch_all_metas(self):
        """
        Return the conda recipe metas, in the order they should be built.

        """
        conda_recipes_root = os.path.abspath(os.path.expanduser(self.conda_recipes_root))
        recipe_metas = fetch_metas(conda_recipes_root)
        recipe_metas = sort_dependency_order(recipe_metas)
        return recipe_metas

    def calculate_existing_distributions(self, recipe_metas):
        # Figure out which distributions binstar.org already has.
        existing_distributions = [meta for meta in recipe_metas
                                  if inspect_binstar.distribution_exists(self.binstar_cli, self.upload_owner, meta)]

        print('Resolved dependencies, will be built in the following order: \n\t{}'.format(
                   '\n\t'.join(['{} (will be built: {})'.format(meta.name(), meta not in existing_distributions)
                                for meta in recipe_metas])))
        return existing_distributions

    def build(self, meta):
        print('Building ', meta.name())
        build.build(meta)

    def main(self):
        recipe_metas = self.fetch_all_metas()
        existing_distributions = self.calculate_existing_distributions(recipe_metas)
        for meta in recipe_metas:
            build_dist = meta not in existing_distributions
            if build_dist:
                self.build(meta)
            self.post_build(meta, build_occured=build_dist)

    def post_build(self, meta, build_occured=True):
        if self.can_upload:
            already_on_channel = inspect_binstar.distribution_exists_on_channel(self.binstar_cli,
                                                                                self.upload_owner,
                                                                                meta,
                                                                                channel=self.upload_channel)
            if not build_occured and not already_on_channel:
                # Link a distribution.
                print('Adding existing {} to the {} channel.'.format(meta.name(), self.upload_channel))
                inspect_binstar.add_distribution_to_channel(self.binstar_cli, self.upload_owner, meta, channel=self.upload_channel)
            elif already_on_channel:
                print('Nothing to be done for {} - it is already on {}.'.format(meta.name(), self.upload_channel))
            else:
                # Upload the distribution
                print('Uploading {} to the {} channel.'.format(meta.name(), self.upload_channel))
                build.upload(self.binstar_cli, meta, self.upload_owner, channels=[self.upload_channel])
