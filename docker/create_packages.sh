#!/bin/bash
repo_root_dir=$1

generate_package (){
temp_dir="/tmp/package"

package_name=$1
version=$2
arch=$3
multiarch=true
if [ -z "$arch" ]; then
    arch=$(dpkg --print-architecture)
    multiarch=false
fi

mkdir -p $temp_dir/DEBIAN
control_file=$temp_dir/DEBIAN/control

echo "Package: $package_name
Source: testpackage
Version: $version
Architecture: $arch
Maintainer: Didier Roche <didrocks@ubuntu.com>
Installed-Size: 26
Section: misc
Priority: extra" > $control_file
[[ $multiarch == true ]] && echo "Multi-Arch: same" >> $control_file
echo "Description: Dummy package for testing
 Package used for testing debs installation" >> $control_file
dpkg-deb -b $temp_dir ${package_name}_${version,}_${arch}.deb
rm -rf $temp_dir
}

extract_version() {
version=$(apt-cache policy $1 | grep Candidate | awk '{print $2}')
[ -z "$version" ] && version=1.0
echo $version
}

create_package() {
package_name=$1
arch=$2
version=$(extract_version $package_name)
generate_package $package_name $version $arch
}

# android studio and adt deps
mkdir -p $repo_root_dir/android
cd $repo_root_dir/android
create_package clang
create_package openjdk-7-jdk
create_package openjdk-8-jdk
create_package jayatana
create_package libncurses5 i386
create_package libstdc++6 i386
create_package zlib1g i386
dpkg-scanpackages . /dev/null | gzip -9c > Packages.gz

# android-platform-tools dep
mkdir -p $repo_root_dir/android-platform-tools
cd $repo_root_dir/android-platform-tools
create_package android-sdk-platform-tools-common
dpkg-scanpackages . /dev/null | gzip -9c > Packages.gz

# rubymine deps
mkdir -p $repo_root_dir/rider
cd $repo_root_dir/rider
create_package mono-devel
dpkg-scanpackages . /dev/null | gzip -9c > Packages.gz

# rubymine deps
mkdir -p $repo_root_dir/rubymine
cd $repo_root_dir/rubymine
create_package ruby
dpkg-scanpackages . /dev/null | gzip -9c > Packages.gz

# stencyl deps
mkdir -p $repo_root_dir/stencyl
cd $repo_root_dir/stencyl
create_package libxtst6 i386
create_package libxext6 i386
create_package libxi6 i386
create_package libncurses5 i386
create_package libxt6 i386
create_package libxpm4 i386
create_package libxmu6 i386
create_package libxp6 i386
create_package libgtk2.0-0 i386
create_package libatk1.0-0 i386
create_package libc6 i386
create_package libcairo2 i386
create_package libexpat1 i386
create_package libfontconfig1 i386
create_package libfreetype6 i386
create_package libglib2.0-0 i386
create_package libice6 i386
create_package libpango1.0-0 i386
create_package libpng12-0 i386
create_package libsm6 i386
create_package libxau6 i386
create_package libxcursor1 i386
create_package libxdmcp6 i386
create_package libxfixes3 i386
create_package libx11-6 i386
create_package libxinerama1 i386
create_package libxrandr2 i386
create_package libxrender1 i386
create_package zlib1g i386
create_package libnss3-1d i386
create_package libnspr4-0d i386
create_package libcurl3 i386
create_package libasound2 i386
dpkg-scanpackages . /dev/null | gzip -9c > Packages.gz

# visual studio code deps
mkdir -p $repo_root_dir/vscode
cd $repo_root_dir/vscode
create_package libgtk2.0-0
create_package libgconf-2-4
dpkg-scanpackages . /dev/null | gzip -9c > Packages.gz

# atom deps
mkdir -p $repo_root_dir/atom
cd $repo_root_dir/atom
create_package libgconf-2-4
dpkg-scanpackages . /dev/null | gzip -9c > Packages.gz

# arduino deps
mkdir -p $repo_root_dir/arduino
cd $repo_root_dir/arduino
create_package gcc-avr
create_package avr-libc
dpkg-scanpackages . /dev/null | gzip -9c > Packages.gz

# scala deps
mkdir -p $repo_root_dir/scala
cd $repo_root_dir/scala
create_package openjdk-7-jre
create_package openjdk-8-jre
dpkg-scanpackages . /dev/null | gzip -9c > Packages.gz

# kotlin deps
mkdir -p $repo_root_dir/kotlin
cd $repo_root_dir/kotlin
create_package openjdk-7-jre
create_package openjdk-8-jre
dpkg-scanpackages . /dev/null | gzip -9c > Packages.gz

# swift deps
mkdir -p $repo_root_dir/swift
cd $repo_root_dir/swift
create_package clang
create_package libicu-dev
create_package libicu55
dpkg-scanpackages . /dev/null | gzip -9c > Packages.gz

# unity3d deps
mkdir -p $repo_root_dir/unity3d
cd $repo_root_dir/unity3d
create_package gconf-service
create_package lib32gcc1
create_package lib32stdc++6
create_package libasound2
create_package libcairo2
create_package libcap2
create_package libcups2
create_package libfontconfig1
create_package libfreetype6
create_package libgconf-2-4
create_package libgdk-pixbuf2.0-0
create_package libgl1-mesa-glx
create_package libglu1-mesa
create_package libgtk2.0-0
create_package libnspr4
create_package libnss3
create_package libpango1.0-0
create_package libpq5
create_package libxcomposite1
create_package libxcursor1
create_package libxdamage1
create_package libxext6
create_package libxfixes3
create_package libxi6
create_package libxrandr2
create_package libxrender1
create_package libxtst6
create_package monodevelop
dpkg-scanpackages . /dev/null | gzip -9c > Packages.gz

# crystal deps
mkdir -p $repo_root_dir/crystal
cd $repo_root_dir/crystal
create_package libbsd-dev
create_package libedit-dev
create_package libevent-core-2.0-5
create_package libevent-dev
create_package libevent-extra-2.0-5
create_package libevent-openssl-2.0-5
create_package libevent-pthreads-2.0-5
create_package libgc-dev
create_package libgmp-dev
create_package libgmpxx4ldbl
create_package libssl-dev
create_package libxml2-dev
create_package libyaml-dev
create_package libreadline-dev
create_package automake
create_package libtool
create_package git
create_package llvm
create_package libpcre3-dev
create_package build-essential
dpkg-scanpackages . /dev/null | gzip -9c > Packages.gz

# DBeaver deps
mkdir -p $repo_root_dir/dbeaver
cd $repo_root_dir/dbeaver
create_package openjdk-8-jre-headless
dpkg-scanpackages . /dev/null | gzip -9c > Packages.gz

# liteide deps
mkdir -p $repo_root_dir/liteide
cd $repo_root_dir/liteide
create_package libqt5core5a
dpkg-scanpackages . /dev/null | gzip -9c > Packages.gz
