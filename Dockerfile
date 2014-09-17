# Docker container for ubuntu developer tools center
# this install a full ubuntu desktop environment in an
# unpriviledge container, add a passwordless sudo user.

# This is to enable running medium tests of udtc.

FROM	ubuntu:14.04
MAINTAINER	Didier Roche <didrocks@ubuntu.com>

# Set the env variable DEBIAN_FRONTEND to noninteractive
ENV DEBIAN_FRONTEND noninteractive

# remove proposed (but used in the base system, so needed if apt has an update and so on…)
# and be up to date.
RUN rm /etc/apt/sources.list.d/proposed.list
RUN apt-get update
RUN apt-get dist-upgrade -y

# install add-apt-respository and tools to create build-deps
RUN apt-get install -y software-properties-common devscripts equivs dpkg-dev

# add didrocks ppa to ensure we have the correct fuse version (postinst)
RUN add-apt-repository -y ppa:didrocks/ubuntu-developer-tools-center
RUN apt-get update

# install system udtc (from latest released version)
#RUN apt-get install -y ubuntu-developer-tools-center

# install udtc build-deps
ADD debian/control /tmp/
RUN mk-build-deps /tmp/control -i --tool 'apt-get --yes'

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

# finally remove all ppas and add local repository
RUN rm /etc/apt/sources.list.d/*
ADD docker/create_packages.sh /tmp/
RUN /tmp/create_packages.sh /apt-fake-repo

