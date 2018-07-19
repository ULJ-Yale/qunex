
ckerfile for MNAP
# MNAP code created by: Anticevic Lab, Yale University and Mind and Brain Lab, University of Ljubljana
# Maintainer of Dockerfile: Zailyn Tamayo, Yale University
##

##
# Tag: ztamayo/mnap:latest
# Dockerfile for MNAP suite
# Sets environment for MNAP
##

FROM ztamayo/mnap_deps2:latest

ADD . /opt/mnaptools

WORKDIR /opt/mnaptools

ADD bedpostx_gpu_cuda_6.5/ ${FSLDIR}

# Set Python path
ENV PYTHONPATH="${PYTONPATH}:/mnaptools" 
# Set MNAP tools path
ENV TOOLS="/opt"

RUN echo "source /opt/mnaptools/library/environment/mnap_environment.sh" >> ~/.bashrc && \
    echo "source /opt/mnaptools/library/environment/mnap_environment.sh" >> ~/.bash_profile && \
    touch ~/.mnapuseoctave && \
#    touch ~/.octaverc && \
#    echo "pkg load control"> > ~/.octaverc && \
    echo "pkg load general" >> ~/.octaverc && \
#    echo "pkg load image" >> ~/.octaverc && \
    echo "pkg load io" >> ~/.octaverc && \
    echo "pkg load miscellaneous" >> ~/.octaverc && \
#    echo "pkg load nan" >> ~/.octaverc && \
    echo "pkg load optim" >> ~/.octaverc && \
#    echo "pkg load signal" >> ~/.octaverc && \
#    echo "pkg load statistics" >> ~/.octaverc && \
    echo "pkg load struct" >> ~/.octaverc && \
# Clear apt cache and other empty folders
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* /boot /media /mnt /srv && \
    rm -rf ~/.cache/pip && \
    rm -rf /opt/mnaptools/bedpostx_gpu_cuda_6.5

CMD ["bash"]

