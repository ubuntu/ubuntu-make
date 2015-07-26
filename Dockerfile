# Docker container for Ubuntu Make
# this installs a full ubuntu desktop environment in an
# unprivileged container, and adds a passwordless sudo user.

# This enables running medium tests of umake.

FROM	ubuntu:14.04
MAINTAINER	Didier Roche <didrocks@ubuntu.com>

# Set the env variable DEBIAN_FRONTEND to noninteractive
ENV DEBIAN_FRONTEND noninteractive

ADD debian/control /tmp/
ADD tests/data/developer.android.com.crt /usr/local/share/ca-certificates/
ADD tests/data/www.eclipse.org.crt /usr/local/share/ca-certificates/
ADD tests/data/www.jetbrains.com.crt /usr/local/share/ca-certificates/
ADD tests/data/golang.org.crt /usr/local/share/ca-certificates/
ADD tests/data/www.dartlang.org.crt /usr/local/share/ca-certificates/
ADD tests/data/www.mozilla.org.crt /usr/local/share/ca-certificates/
ADD tests/data/code.visualstudio.com.crt /usr/local/share/ca-certificates/
ADD docker/create_packages.sh /tmp/

# Refresh the image
RUN \
  apt-get update && \
  apt-get dist-upgrade -y && \

# install add-apt-repository and tools to create build-deps
  apt-get install -y software-properties-common devscripts equivs dpkg-dev && \

# add umake ppa
  add-apt-repository -y ppa:ubuntu-desktop/ubuntu-make && \
  apt-get update && \

# install system umake (from latest released version)
#RUN apt-get install -y ubuntu-make

# install umake build-deps
  mk-build-deps /tmp/control -i --tool 'apt-get --yes' && \

# for running it as a daemon (and ssh requires the sshd directory)
  apt-get install openssh-server -y && \
  mkdir /var/run/sshd && \
# disable DNS to not wait on host name resolution (delay when working offline)
  echo "UseDNS no" >> /etc/ssh/sshd_config && \

  echo 'EXTRA_GROUPS="adm cdrom sudo dip plugdev fuse"' >> /etc/adduser.conf && \
  echo 'ADD_EXTRA_GROUPS=1' >> /etc/adduser.conf && \
  echo "user ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/bar && \
  adduser --disabled-password --gecos "" user && \
  echo user:user | chpasswd && \

# Twisted for a mock FTP server.
  apt-get install python-twisted-core -y && \

# add certificates
  update-ca-certificates && \

# finally remove all ppas and add local repository
  rm /etc/apt/sources.list.d/* && \
  /tmp/create_packages.sh /apt-fake-repo && \

# clean up stuff
  apt-get clean -y && \
  apt-get remove --purge -y software-properties-common devscripts equivs && \
  apt-get autoremove -y

