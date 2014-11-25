# Install miniconda under Linux and OSX.
# The following environment variables are expected:
# MINICONDA_VERSION - the version as seen in the miniconda URL. e.g. "3.5.5"
# TARGET_ARCH - either x86 or x64. Note that on OSX, x86 is not readily available on binstar.
# CONDA_INSTALL_LOCN - the directory where miniconda should be installed.

MINICONDA_URL="http://repo.continuum.io/miniconda"

if [[ "$TARGET_ARCH" == 'x86' ]]; then
        platform_suffix="x86"
else
        platform_suffix="x86_64"
fi

if [[ "$OSTYPE" == 'linux-gnu' ]]; then
    os='linux'
else
    os='MacOSX'
fi

URL=${MINICONDA_URL}/Miniconda3-${MINICONDA_VERSION}-${os}-${platform_suffix}.sh
wget ${URL} -O miniconda.sh;
bash miniconda.sh -b -p ${CONDA_INSTALL_LOCN}

source ${CONDA_INSTALL_LOCN}/bin/activate root

