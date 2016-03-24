FROM centos:6

MAINTAINER Phil Elson <pelson.pub@gmail.com>

RUN yum install -y \
                   bzip2 \
                   gcc-c++ \
                   git \
                   make \
                   patch \
                   tar \
                   wget \
                   which \
                   libXext \
                   libXrender \
                   libSM \
                   libX11-devel

RUN wget https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh --no-verbose && \
    bash Miniconda3-latest-Linux-x86_64.sh -b -p /opt/conda && rm Miniconda*.sh && \
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

ENV LANG en_US.UTF-8
