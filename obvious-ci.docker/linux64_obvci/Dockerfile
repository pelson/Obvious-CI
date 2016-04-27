FROM centos:6

MAINTAINER Phil Elson <pelson.pub@gmail.com>


# Set an encoding to make things work smoothly.
ENV LANG en_US.UTF-8

# Install basic requirements.
RUN yum update -y && \
    yum install -y \
                   bzip2 \
                   gcc-c++ \
                   git \
                   make \
                   patch \
                   tar \
                   which \
                   libXext-devel \
                   libXrender-devel \
                   libSM-devel \
                   libX11-devel \
                   mesa-libGL-devel && \
    yum clean all

# Install devtoolset 2.
RUN yum update -y && \
    yum install -y \
                   centos-release-scl \
                   yum-utils && \
    yum-config-manager --add-repo http://people.centos.org/tru/devtools-2/devtools-2.repo && \
    yum update -y && \
    yum install -y \
                   devtoolset-2-binutils \
                   devtoolset-2-gcc \
                   devtoolset-2-gcc-c++ && \
    yum clean all

# Download and install tini for zombie reaping.
RUN curl -s -L -O https://github.com/krallin/tini/releases/download/v0.9.0/tini && \
    openssl md5 tini | grep 596b898785d2f169ec969445087c14d6 && \
    chmod +x tini && \
    mv tini /usr/local/bin

# Install the latest Miniconda with Python 3 and update everything.
RUN curl -s -L -O https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh && \
    bash Miniconda3-latest-Linux-x86_64.sh -b -p /opt/conda && rm Miniconda*.sh && \
    export PATH=/opt/conda/bin:$PATH && \
    conda config --set show_channel_urls True && \
    conda update --all --yes && conda clean -tipsy

# Install Obvious-CI.
RUN export PATH="/opt/conda/bin:${PATH}" && \
    conda install --yes -c pelson/channel/development obvious-ci && \
    obvci_install_conda_build_tools.py

# udunits2.
# libtool texinfo
# RUN yum install -y expat-devel

COPY entrypoint_source /opt/docker/bin/entrypoint_source
COPY entrypoint /opt/docker/bin/entrypoint

# Ensure that all containers start with tini and the user selected process.
# Provide a default command (`bash`), which will start if the user doesn't specify one.
ENTRYPOINT [ "/usr/local/bin/tini", "--", "/opt/docker/bin/entrypoint" ]
CMD [ "/bin/bash" ]
