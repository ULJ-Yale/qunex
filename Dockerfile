#
#~ND~FORMAT~MARKDOWN~
#~ND~START~
#
# ## COPYRIGHT NOTICE
#
# Copyright (C) 2015 Anticevic Lab, Yale University
# Copyright (C) 2015 MBLAB, University of Ljubljana
#
# ## AUTHORS(s)
#
# * Zailyn Tamayo, Department of Psychiatry, Yale University
#
# ## PRODUCT
#
#  Dockerfile
#
# ## LICENSE
#
# * The Dockerfile = the "Software"
# * This Software conforms to the license outlined in the MNAP Suite:
# * https://bitbucket.org/hidradev/mnaptools/src/master/LICENSE.md
#
# ## TODO
#
#
# ## DESCRIPTION:
#
# * This is a general docker generation script for the MNAP suite
#
# ## PREREQUISITE INSTALLED SOFTWARE
#
# * MNAP Suite and dependencies
#
# ## PREREQUISITE ENVIRONMENT VARIABLES
#
#
# ## PREREQUISITE PRIOR PROCESSING
#
#
#~ND~END~

##
# Tag: ztamayo/mnap:latest
# Dockerfile for MNAP suite
# Sets environment for MNAP
##

# -- Define docker image location
FROM ztamayo/mnap_deps2:latest

# -- Define where the mnaptools repo resides on the image
ADD . /opt/mnaptools
WORKDIR /opt/mnaptools

# -- Set Python path
ENV PYTHONPATH="${PYTONPATH}:/mnaptools" 

# -- Set MNAP tools path
ENV TOOLS="/opt"

# -- Set environment & Set Octave as default & Clear apt cache and other empty folders
RUN echo "source /opt/mnaptools/library/environment/mnap_environment.sh" >> ~/.bashrc && \
    echo "source /opt/mnaptools/library/environment/mnap_environment.sh" >> ~/.bash_profile && \
    touch ~/.mnapuseoctave && \
    echo "pkg load general" >> ~/.octaverc && \
    echo "pkg load io" >> ~/.octaverc && \
    echo "pkg load miscellaneous" >> ~/.octaverc && \
    echo "pkg load optim" >> ~/.octaverc && \
    echo "pkg load struct" >> ~/.octaverc && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* /boot /media /mnt /srv && \
    rm -rf ~/.cache/pip

CMD ["bash"]

