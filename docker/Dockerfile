FROM nvidia/cuda:10.2-cudnn7-devel-ubuntu18.04
RUN ln -fs /usr/share/zoneinfo/Europe/Moscow /etc/localtime
RUN DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install -yq --no-install-recommends \
         build-essential \
         cmake \
         git \
         curl \
         ca-certificates \
         libjpeg-dev \
         libpng-dev  \
         python3-pip \
         python3-opencv \
         ffmpeg \
         wget  \
         python3-dev && \
 rm -rf /var/lib/apt/lists/*
RUN pip3 install torch==1.4.0+cu100 torchvision==0.5.0+cu100 -f https://download.pytorch.org/whl/torch_stable.html setuptools tqdm
WORKDIR /opt/
RUN git clone https://github.com/smit1237/MVIMP && cd MVIMP && git checkout experiments && python3 preparation.py -f dain
WORKDIR /opt/MVIMP
RUN cd third_party/DAIN/PWCNet/correlation_package_pytorch1_0/ && python3 setup.py install

