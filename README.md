# meterd
Daemon for querying power meters through MBus, RTU-Modbus and TCP-Modbus

## Description
All queried values are written to a XML file periodically. This XML file is then uploaded to a FTP server of your choice every 6 hours (or less, if you want)  
You can add devices easily by adding YAML configuration files into the /etc/meterd/conf.d directory. In this config files you can specify device parameters, for example which serial device to use, as well as all Modbus registers/MBus data records to query. This configuration is also accessible through the web interface.

## Copyright notices
Meterd (c) 2019 Florian Bührle

pyMeterBus (c) 2014 Mikael Ganehag Brorsson  
lib/meterbus/LICENSE

PyYAML (c) 2017-2019 Ingy döt Net, (c) 2006-2016 Kirill Simonov  
lib/yaml/LICENSE
