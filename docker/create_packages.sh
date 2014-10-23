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
echo $(apt-cache policy $1 | grep Candidate | awk '{print $2}')
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
create_package openjdk-7-jdk
create_package libncurses5 i386
create_package libstdc++6 i386
create_package zlib1g i386
dpkg-scanpackages . /dev/null | gzip -9c > Packages.gz

# eclipse deps
mkdir -p $repo_root_dir/eclipse
cd $repo_root_dir/eclipse
create_package openjdk-7-jdk
dpkg-scanpackages . /dev/null | gzip -9c > Packages.gz

