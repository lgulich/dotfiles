FROM ubuntu:bionic
RUN apt-get update && apt-get -y install sudo

RUN useradd -ms /bin/bash docker && adduser docker sudo
RUN echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers
USER docker
WORKDIR /home/docker/
