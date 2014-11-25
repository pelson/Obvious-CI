from distutils.core import setup
import os.path


setup(name='Obvious-ci',
      version='1.0',
      description='Utilities to simplify CI with tools such as travis-ci and appveyor.',
      author='Phil Elson',
      author_email='pelson.pub@gmail.com',
      url='https://github.com/pelson/Obvious-ci',
      scripts=[os.path.join('scripts', script) for script in
               ['obvci_install_conda_build_tools.py', 'obvci_install_miniconda.ps1',
                'obvci_install_miniconda.sh', 'obvci_appveyor_python_build_env.cmd',
                'obvci_conda_build_dir.py']],
      packages=['obvci', 'obvci.conda_tools'],
     )

