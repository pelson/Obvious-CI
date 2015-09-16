from setuptools import setup
import os.path


tl_package = 'obvci'
vn_context, vn_fname = {}, os.path.join(tl_package, '_version.py')
try:
    with open(vn_fname, 'r') as fh:
        exec(fh.read(), vn_context)
    version = vn_context.get('__version__', 'dev')
except IOError:
    version = 'dev'


setup(name='Obvious-ci',
      version=version,
      description='Utilities to simplify CI with tools such as travis-ci and appveyor.',
      author='Phil Elson',
      author_email='pelson.pub@gmail.com',
      url='https://github.com/pelson/Obvious-ci',
      scripts=[os.path.join('scripts', script) for script in
               ['obvci_install_conda_build_tools.py', 'obvci_install_miniconda.ps1',
                'obvci_install_miniconda.sh', 'obvci_appveyor_python_build_env.cmd',
                'obvci_conda_build_dir.py']],
      packages=['obvci', 'obvci.conda_tools', 'obvci.cli'],
      entry_points={
          'console_scripts': [
              'obvci_conda_build_dir = obvci.cli.conda_build_dir:main'
          ]
      },
     )

