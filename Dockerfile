# Docker container for Ubuntu Make
# this installs a full ubuntu desktop environment in an
# unprivileged container, and adds a passwordless sudo user.

# This enables running medium tests of umake.

FROM	ubuntu:18.04
LABEL maintainer	Galileo Sartor <galileo.sartor@gmail.com>

# Set the env variable DEBIAN_FRONTEND to noninteractive
ENV DEBIAN_FRONTEND noninteractive

ENV LANG C.UTF-8

COPY debian/control /tmp/
COPY docker/umake_docker.pub /tmp/
COPY tests/data/*.crt /usr/local/share/ca-certificates/
COPY docker/create_packages.sh /tmp/

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Refresh the image
RUN \
  apt-get update && \
# install add-apt-repository and tools to create build-deps
# Twisted for a mock FTP server and locales
  apt-get install --no-install-recommends -y software-properties-common devscripts equivs dpkg-dev openssh-server sudo python3-twisted locales && \
# Set default locale
  locale-gen en_US.UTF-8 && \
# install umake build-deps
  mk-build-deps /tmp/control -i --tool 'apt-get --yes' && \
# for running it as a daemon (and ssh requires the sshd directory)
  mkdir /var/run/sshd && \
# disable DNS to not wait on host name resolution (delay when working offline)
  echo "UseDNS no" >> /etc/ssh/sshd_config && \
  echo 'EXTRA_GROUPS="adm cdrom sudo dip plugdev fuse"' >> /etc/adduser.conf && \
  echo 'ADD_EXTRA_GROUPS=1' >> /etc/adduser.conf && \
  echo "user ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/bar && \
  adduser --disabled-password --gecos "" user && \
  echo user:user | chpasswd && \
# add the ubuntu make ssh key to the list of authorized ones
  mkdir -p /home/user/.ssh && \
  cat /tmp/umake_docker.pub >> /home/user/.ssh/authorized_keys && \
  chown -R user:user /home/user/ && \
# add certificates
  update-ca-certificates && \
# finally remove all ppas and add local repository
  /tmp/create_packages.sh /apt-fake-repo && \
# clean up stuff
  apt-get clean -y && \
  apt-get remove --purge -y software-properties-common devscripts equivs
