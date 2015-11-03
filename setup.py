import os.path
import sys

from setuptools import setup

# Add the CWD to the path so that we get an appropriate versioneer.
sys.path.insert(0, './')
import versioneer


setup(name='Obvious-ci',
      version=versioneer.get_version(),
      cmdclass=versioneer.get_cmdclass(),
      description='Utilities to simplify CI with tools such as travis-ci and appveyor.',
      author='Phil Elson',
      author_email='pelson.pub@gmail.com',
      url='https://github.com/pelson/Obvious-ci',
      scripts=[os.path.join('scripts', script) for script in
               ['obvci_install_conda_build_tools.py', 'obvci_install_miniconda.ps1',
                'obvci_install_miniconda.sh', 'obvci_appveyor_python_build_env.cmd']],
      packages=['obvci', 'obvci.conda_tools', 'obvci.cli'],
      entry_points={
          'console_scripts': [
              'obvci_conda_build_dir = obvci.cli.conda_build_dir:main'
          ]
      },
     )

