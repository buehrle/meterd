#!/usr/bin/env bash

if [[ "$EUID" -ne 0 ]]
  then echo "Please use a fakeroot environment."
  exit
fi

V_MAJOR=1
V_MINOR=2
V_REV=5

PACKAGE_NAME="meterd_$V_MAJOR.$V_MINOR-$V_REV"

mkdir -p ${PACKAGE_NAME}

mkdir -p ${PACKAGE_NAME}/usr/bin
mkdir -p ${PACKAGE_NAME}/usr/local/meterd/lib/meterbus
mkdir -p ${PACKAGE_NAME}/usr/local/meterd/lib/yaml
mkdir -p ${PACKAGE_NAME}/usr/local/meterd/venv
mkdir -p ${PACKAGE_NAME}/etc/systemd/system
mkdir -p ${PACKAGE_NAME}/etc/meterd/conf.d
mkdir -p ${PACKAGE_NAME}/usr/local/lib/meterd-install/pip

mkdir -p ${PACKAGE_NAME}/var/www/meterd/css
mkdir -p ${PACKAGE_NAME}/var/www/meterd/img
mkdir -p ${PACKAGE_NAME}/var/www/meterd/templates

mkdir -p ${PACKAGE_NAME}/etc/nginx/sites-available
mkdir -p ${PACKAGE_NAME}/etc/nginx/sites-enabled

mkdir -p ${PACKAGE_NAME}/DEBIAN

cp meterd/data.py ${PACKAGE_NAME}/usr/local/meterd
cp meterd/handlers.py ${PACKAGE_NAME}/usr/local/meterd
cp meterd/meterd.py ${PACKAGE_NAME}/usr/local/meterd
cp meterd/meterd-ftpd.py ${PACKAGE_NAME}/usr/local/meterd
cp meterd/monitoring.py ${PACKAGE_NAME}/usr/local/meterd
cp meterd/query.py ${PACKAGE_NAME}/usr/local/meterd

cp lib/meterbus/* ${PACKAGE_NAME}/usr/local/meterd/lib/meterbus
cp lib/yaml/* ${PACKAGE_NAME}/usr/local/meterd/lib/yaml
cp -R pip/* ${PACKAGE_NAME}/usr/local/lib/meterd-install/pip

cp meterd-query/meterd-query.py ${PACKAGE_NAME}/usr/local/meterd

cp units/meterd.service ${PACKAGE_NAME}/etc/systemd/system
cp units/meterd-ftpd.service ${PACKAGE_NAME}/etc/systemd/system
cp units/meterd-ftpd.timer ${PACKAGE_NAME}/etc/systemd/system

cp conf/example-main.yaml ${PACKAGE_NAME}/etc/meterd
cp conf/example-mbus.yaml ${PACKAGE_NAME}/etc/meterd
cp conf/example-modbus_rtu.yaml ${PACKAGE_NAME}/etc/meterd
cp conf/example-modbus_tcp.yaml ${PACKAGE_NAME}/etc/meterd

cp webif/index.php ${PACKAGE_NAME}/var/www/meterd
cp webif/main.js ${PACKAGE_NAME}/var/www/meterd
cp webif/css/* ${PACKAGE_NAME}/var/www/meterd/css
cp webif/img/* ${PACKAGE_NAME}/var/www/meterd/img
cp webif/templates/* ${PACKAGE_NAME}/var/www/meterd/templates

cp webif/nginx/sites-available/meterd ${PACKAGE_NAME}/etc/nginx/sites-available
cp webif/nginx/php-fpm/meterd.conf ${PACKAGE_NAME}/usr/local/lib/meterd-install/meterd.conf

cp build/control ${PACKAGE_NAME}/DEBIAN/
cp build/postinst ${PACKAGE_NAME}/DEBIAN/
cp build/postrm ${PACKAGE_NAME}/DEBIAN/
cp build/prerm ${PACKAGE_NAME}/DEBIAN/

chown -R root:root ${PACKAGE_NAME}/*

ln -s /usr/local/meterd/meterd-query.py ${PACKAGE_NAME}/usr/bin/meterd-query
ln -s /etc/nginx/sites-available/meterd ${PACKAGE_NAME}/etc/nginx/sites-enabled/meterd

chmod 755 ${PACKAGE_NAME}/usr/local/meterd/meterd-ftpd.py
chmod 755 ${PACKAGE_NAME}/usr/local/meterd/meterd.py
chmod 755 ${PACKAGE_NAME}/usr/local/meterd/meterd-query.py

chmod 755 ${PACKAGE_NAME}/var/www/meterd/index.php

chmod 755 ${PACKAGE_NAME}/DEBIAN/postinst
chmod 755 ${PACKAGE_NAME}/DEBIAN/postrm
chmod 755 ${PACKAGE_NAME}/DEBIAN/prerm

dpkg-deb --build ${PACKAGE_NAME}

rm -rf ${PACKAGE_NAME}