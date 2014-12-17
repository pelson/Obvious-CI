"""
Build all the conda recipes in the given directory sequentially if they do not
already exist on the given binstar channel.
Building is done in order of dependencies (circular dependencies are not supported).
Once a build is complete, the distribution will be uploaded (provided BINSTAR_TOKEN is
defined), and the next package will be processed.

"""
import os
import subprocess
import sys


from binstar_client.utils import get_binstar
import binstar_client
from conda_build.metadata import MetaData
from conda_build.build import bldpkg_path
import conda.config

from . import build_all


def package_built_name(package, root_dir):
    package_dir = os.path.join(root_dir, package)
    meta = MetaData(package_dir)
    return bldpkg_path(meta)


def distribution_exists(binstar_cli, owner, recipe_dir):
    meta = MetaData(recipe_dir)
    info = meta.info_index()

    fname = '{}/{}.tar.bz2'.format(conda.config.subdir, meta.dist())
    try:
        binstar_cli.distribution(owner, meta.name(), meta.version(),
                                 fname)
        exists = True
    except binstar_client.errors.NotFound:
        exists = False
    return exists


class NamedDict(object):
    def __init__(self, **kwargs):
        for k, v in kwargs.iteritems():
            setattr(self, k, v)


def main(conda_recipes_root, upload_owner, upload_channel):
    print('Looking for packages in {}'.format(conda_recipes_root))
    packages = sorted(build_all.conda_packages(conda_recipes_root))

    if os.name == 'nt':
        build_script = 'bld.bat'
    else:
        build_script = 'build.sh'

    # TODO: Force the installation of the provided channel.

    # Only include packages which have an appropriate build script.
    # TODO: This could become more flexible by allowing a exclude.lst
    # file in the recipe?
    packages = [package for package in packages
		        if os.path.exists(os.path.join(package[1], build_script))]

    package_dependencies = build_all.conda_package_dependencies(packages)
    resolved_dependencies = list(build_all.resolve_dependencies(package_dependencies))

    binstar_token = os.environ.get('BINSTAR_TOKEN', None)
    can_upload = binstar_token is not None

    if not can_upload:
        print('**Build will continue, but no uploads will take place.**')
        print('To automatically upload from this script, define the BINSTAR_TOKEN env variable.')
        print('This is done automatically on the travis-ci system once the PR has been merged.')
    else:
        print('conda build currently leaks all environment variables, therefore the BINSTAR_TOKEN '
              'is being reset. See https://github.com/conda/conda-build/pull/274 for progress.')
        os.environ['BINSTAR_TOKEN'] = 'Hidden by Obvious-CI'

    binstar_cli = get_binstar(NamedDict(token=binstar_token, site=None))

    # Check to see if the distribution that would be built already exists in any
    # channel belonging to the target owner.
    distributions_exist = [distribution_exists(binstar_cli, upload_owner, os.path.join(conda_recipes_root, package))
                           for package in resolved_dependencies]

    if can_upload:
        distributions_on_channel = [dist['basename'] for dist in
                                    binstar_cli.show_channel(upload_channel, upload_owner)['files']]

    print('Resolved dependencies, will be built in the following order: \n\t{}'.format(
               '\n\t'.join(['{} (will be built: {})'.format(package, not already_built)
                            for package, already_built in zip(resolved_dependencies, distributions_exist)])))

    for package, already_exists in zip(resolved_dependencies, distributions_exist):
        package_fname = package_built_name(package, conda_recipes_root)

        if already_exists:
            if can_upload and package_fname not in distributions_on_channel:
                # Simply link to the given channel if it isn't already showing this distribution.
                print('Adding {} to {}'.format(package, upload_channel))
                binstar_cli.add_channel(upload_channel, upload_owner, package, filename=package_fname)
        else:
            build_all.build_package(package, conda_recipes_root)
            if can_upload:
                try:
                    # TODO: Use binstar_cli.upload?
                    subprocess.check_call(['binstar', '-t', binstar_token, 'upload', '--no-progress',
                                           '-u', upload_owner, '-c', upload_channel, package_fname],
                                          cwd=conda_recipes_root)
                except:
                    raise RuntimeError('EXCEPTION OCCURED. Exception hidden to prevent token leakage.')
