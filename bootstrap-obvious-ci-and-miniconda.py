#!/usr/bin/env python
"""
Installs Miniconda with the latest version of Obvious-CI.

This scipt supports Python 2 and 3 (>=2.6 and >=3.2+ respectively) and is
designed to run on OSX, Linux and Windows.

"""
from __future__ import print_function

import argparse
import os
import platform
import subprocess

try:
    from urllib.request import urlretrieve
except ImportError:
    from urllib import urlretrieve

"""

    $filepath = DownloadMiniconda $python_version $platform_suffix
    Write-Host "Installing" $filepath "to" $python_home
    $args = "/InstallationType=AllUsers /S /AddToPath=1 /RegisterPython=1 /D=" + $python_home
    Write-Host $filepath $args
    Start-Process -FilePath $filepath -ArgumentList $args -Wait -Passthru
    #Start-Sleep -s 15
    if (Test-Path $python_home) {
        Write-Host "Miniconda $python_version ($architecture) installation complete"
    } else {
        Write-Host "Failed to install Python in $python_home"
        Exit 1
    }
}

function main () {
    InstallMiniconda $env:MINICONDA_VERSION $env:TARGET_ARCH $env:CONDA_INSTALL_LOCN
}

main
"""


MINICONDA_URL = "http://repo.continuum.io/miniconda"





MINICONDA_URL_TEMPLATE = ('http://repo.continuum.io/miniconda/Miniconda{major_py_version}-'
                          '{miniconda_version}-{OS}-{arch}.{ext}')



# bash miniconda.sh -b -p ${CONDA_INSTALL_LOCN}
# 
# source ${CONDA_INSTALL_LOCN}/bin/activate root


def miniconda_url(target_system, target_arch, major_py_version, miniconda_version='3.7.0'):
    template_values = {'miniconda_version': miniconda_version}

    if target_arch == 'x86':
        template_values['arch'] = "x86"
    elif target_arch == 'x64':
        template_values['arch'] = "x86_64"
    else:
        raise ValueError('Unexpected target arch.')
    
    system_to_miniconda_os = {'Linux': 'Linux',
                              'Darwin': 'MacOSX'}
    if target_system not in system_to_miniconda_os:
        raise ValueError('Unexpected system {!r}.'.format(system))
    template_values['OS'] = system_to_miniconda_os[target_system]

    miniconda_os_ext = {'Linux': 'sh', 'MacOSX': 'sh',
                        'Windows': 'exe'}
    template_values['ext'] = miniconda_os_ext[template_values['OS']]

    if major_py_version not in ['2', '3']:
        raise ValueError('Unexpected major Python version {!r}.'.format(major_py_version))
    template_values['major_py_version'] = major_py_version if major_py_version == '3' else ''
    
    return MINICONDA_URL_TEMPLATE.format(**template_values)


def main(target_dir, target_arch, major_py_version, miniconda_version='3.7.0', install_obvci=True):
    system = platform.system()
    URL = miniconda_url(system, target_arch, major_py_version, miniconda_version)
    if system in ['Linux', 'Darwin']:
        script_fname = 'install_miniconda.sh'
        cmd = ['bash', script_fname, '-b', '-p', target_dir]
    elif system in ['Windows']:
        script_fname = 'install_miniconda.exe'
        # needs to be put on the powershell
#         $args = "/InstallationType=AllUsers /S /AddToPath=1 /RegisterPython=1 /D=" + $python_home
#         Write-Host $filepath $args
#         Start-Process -FilePath $filepath -ArgumentList $args -Wait -Passthru
    else:
        raise ValueError('Unsupported operating system.')
    
    print('Downloading from {}'.format(URL))
    urlretrieve(URL, script_fname)
    
    subprocess.check_call(cmd)
    
    if not os.path.isdir(target_dir):
        raise RuntimeError('Failed to install miniconda :(')

    if install_obvci:
        conda_path = os.path.join(target_dir, 'bin', 'conda')
        subprocess.check_call([conda_path, 'install', '--yes', '--quiet', '-c', 'pelson', 'obvious-ci'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="""A script to download and install miniconda for Linux/OSX/Windows.""")
    parser.add_argument("installation_directory", help="""Where miniconda should be installed.""")
    parser.add_argument("arch", help="""The target architecture of this build. (must be either "x86" or "x64").""",
                        choices=['x86', 'x64'])
    parser.add_argument("major_py_version", help="""The major Python version for the miniconda root env (may
                                                    still subsequently use another Python version).""",
                        choices=['2', '3'])
    parser.add_argument('--without-obvci', help="Disable the installation of Obvious-ci.",
                        action='store_true')
    parser.add_argument('--miniconda-version', default='3.7.0')

    args = parser.parse_args()
    main(args.installation_directory, args.arch, args.major_py_version,
         miniconda_version=args.miniconda_version,
         install_obvci=not args.without_obvci)
