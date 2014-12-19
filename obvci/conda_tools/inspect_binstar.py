import conda.config
import binstar_client
from conda_build.build import bldpkg_path


def distribution_exists(binstar_cli, owner, metadata):
    """
    Determine whether a distribution exists.

    This does not check specific channels - it is either on binstar or it is not.
    """
    fname = '{}/{}.tar.bz2'.format(conda.config.subdir, metadata.dist())
    try:
        r = binstar_cli.distribution(owner, metadata.name(), metadata.version(),
                                     fname)
        print(r)
        exists = True
    except binstar_client.NotFound:
        exists = False
    return exists


def distribution_exists_on_channel(binstar_cli, owner, metadata, channel='main'):
    """
    Determine whether a distribution exists on a specific channel.

    Note from @pelson: As far as I can see, there is no easy way to do this on binstar.

    """
    fname = '{}/{}.tar.bz2'.format(conda.config.subdir, metadata.dist())
    distributions_on_channel = [dist['basename'] for dist in
                                binstar_cli.show_channel(channel, owner)['files']]
    return fname in distributions_on_channel


def add_distribution_to_channel(binstar_cli, owner, metadata, channel='main'):
    """Add a(n already existing) distribution on binstar to another channel."""
    print('Adding {} to {}'.format(metadata.name(), channel))
    package_fname = '{}/{}.tar.bz2'.format(conda.config.subdir, metadata.dist())
    print('WARNING!!!!\n' * 5)
    print("Don't use this function! The binstar client adds **all** package of this name "
          "to the desired channel - there is no per-distribution control. ")

    binstar_cli.add_channel(channel, owner, metadata.name(), filename=package_fname)
