# Docker container for ubuntu developer tools center
# this install a full ubuntu desktop environment in an
# unpriviledge container, add a passwordless sudo user.

# This is to enable running medium tests of udtc.

FROM	ubuntu:14.04
MAINTAINER	Didier Roche <didrocks@ubuntu.com>

# Set the env variable DEBIAN_FRONTEND to noninteractive
ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update
RUN apt-get install -y software-properties-common

# Installing fuse package is trying to create a fuse device without success
# due the container permissions. Remove postinst
RUN apt-get -y install fuse  || :
RUN rm -rf /var/lib/dpkg/info/fuse.postinst
RUN apt-get -y install fuse

# add didrocks ppa to ensure we have the correct fuse version (postinst)a
RUN add-apt-repository -y ppa:didrocks/docker-ppa-udtc
RUN add-apt-repository -y ppa:fkrull/deadsnakes
RUN apt-get update
RUN apt-get dist-upgrade -y
RUN apt-get install ubuntu-desktop -y

# udtc requirements
RUN apt-get install python3.4 apt apt-utils libapt-pkg-dev gir1.2-glib-2.0 python3-gi python3-progressbar -y

# for running it as a daemon (and ssh requires the sshd directory)
RUN apt-get install openssh-server -y
RUN mkdir /var/run/sshd
# disable DNS to not wait on host name resolution (delay when working offline)
RUN echo "UseDNS no" >> /etc/ssh/sshd_config

RUN echo 'EXTRA_GROUPS="adm cdrom sudo dip plugdev fuse"' >> /etc/adduser.conf
RUN echo 'ADD_EXTRA_GROUPS=1' >> /etc/adduser.conf
RUN echo "user ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/bar
RUN adduser --disabled-password --gecos "" user
RUN echo user:user | chpasswd

# add certificates
ADD tests/data/developer.android.com.crt /usr/local/share/ca-certificates/
RUN update-ca-certificates
