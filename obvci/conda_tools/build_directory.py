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

import build_all


def package_built_name(package, root_dir):
    return subprocess.check_output(['conda', 'build', package, '--output'],
                                   cwd=root_dir).strip()


def package_upload_name(package, root_dir):
    package_fname = package_built_name(package, root_dir)

    base_package_fname = os.path.basename(package_fname)
    package_os = os.path.basename(os.path.dirname(package_fname))
    upload_name = '{}/{}'.format(package_os, base_package_fname)
    return upload_name


def channel_distributions(user, channel, binstar_cli=None):
    """
    Return a list of the distributions in the given user's
    (or organisation's) channel.

    """
    if binstar_cli is None:
        binstar_cli = get_binstar()


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
    if binstar_token is None:
        print('**Build will continue, but no uploads will take place.**')
        print('To automatically upload from this script, define the BINSTAR_TOKEN env variable.')
        print('This is done automatically on the travis-ci system once the PR has been merged.')
    
    binstar_cli = get_binstar(NamedDict(token=binstar_token, site=None))
    
    distributions_on_channel = [dist['basename'] for dist in
                                binstar_cli.show_channel(upload_channel, upload_owner)['files']]
    
    channel_dependencies = [package_upload_name(package, conda_recipes_root) in distributions_on_channel
                            for package in resolved_dependencies]
    print('Resolved dependencies, will be built in the following order: \n\t{}'.format(
               '\n\t'.join(['{} (will be built: {})'.format(package, not already_built)
                            for package, already_built in zip(resolved_dependencies, channel_dependencies)])))

    for package, already_on_channel in zip(resolved_dependencies, channel_dependencies):
        package_fname = package_built_name(package, conda_recipes_root)

        if not already_on_channel:
            # The file may already exist on binstar, in which case we just need to link it.
            if file_exists_on_binstar(binstar_cli, upload_owner, package, conda_recipes_root):
                print('BUILD NOT NEEDED (already on binstar on another channel belonging '
                      'to {}): {}'.format(upload_owner, package_fname))
                print('Linking existing package to the {} channel (not building again).'.format(upload_channel))
                binstar_cli.add_channel(upload_channel, upload_owner, package, filename=package_fname)
            else:
                # TODO: Ensure that the channel is available to conda.
                build_all.build_package(package, conda_recipes_root)
                if binstar_token is not None:
                    try:
                        subprocess.check_call(['binstar', '-t', binstar_token, 'upload', '--no-progress',
                                               '-u', upload_owner, '-c', upload_channel, package_fname],
                                              cwd=conda_recipes_root)
                    except:
                        raise RuntimeError('EXCEPTION OCCURED. Exception hidden to prevent token leakage.')


def file_exists_on_binstar(binstar_cli, owner, package, root_dir):
    upload_name = package_upload_name(package, root_dir)

    import binstar_client.errors
    try:
        package_info = binstar_cli.package(owner, package)
    except binstar_client.errors.NotFound:
        package_exists = False
    else:
        package_exists = True

    if package_exists:
        exists = False
        for release in package_info['releases']:
            if upload_name in release['distributions']:
                exists = True
                break
    return exists


if __name__ == '__main__':
    import argparse

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
