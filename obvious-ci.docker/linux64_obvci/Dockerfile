FROM centos:6

MAINTAINER Phil Elson <pelson.pub@gmail.com>

RUN yum install -y \
                   autoconf \
                   bzip2 \
                   gcc-c++ \
                   git \
                   make \
                   patch \
                   tar \ 
                   wget

RUN wget https://repo.continuum.io/miniconda/Miniconda-latest-Linux-x86_64.sh --no-verbose && \
    bash Miniconda-latest-Linux-x86_64.sh -b -p /opt/conda && rm Miniconda*.sh && \
    export PATH=/opt/conda/bin:$PATH && \
    conda config --set show_channel_urls True && \
    conda update --all --yes && conda clean -t -p

RUN export PATH=/opt/conda/bin:$PATH && \
    conda install --yes -c pelson/channel/development obvious-ci && \
    obvci_install_conda_build_tools.py

# udunits2.
# libtool texinfo
# RUN yum install -y expat-devel

ENV PATH /opt/conda/bin:$PATH

# http://bugs.python.org/issue19846
# > At the moment, setting "LANG=C" on a Linux system *fundamentally breaks Python 3*, and that's not OK.
ENV LANG C.UTF-8
