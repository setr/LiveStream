#!/bin/bash
sudo apt-get -y install build-essential libpcre3 libpcre3-dev libssl-dev

wget http://nginx.org/download/nginx-1.13.6.tar.gz 
wget https://github.com/arut/nginx-rtmp-module/archive/v1.2.0.tar.gz
tar -zxvf nginx-1.13.6.tar.gz
tar -zxvf v1.2.0.tar.gz 

cd nginx-1.13.6/
sudo ./configure --with-http_ssl_module --add-module=../nginx-rtmp-module-1.2.0
# we need to edit objs/Makefile to remove the -Werror flag; gcc6 is fine but gcc7 adds a new warning that causes rtmp to fail compilation
sed -i '3c CFLAGS =  -pipe  -O -W -Wall -Wpointer-arith -Wno-unused-parameter -g' objs/Makefile
make
make install



# accepts any rtmp stream and multiplex-forwards it on the url rtmp://IP_ADDR/live
sudo echo ' 
rtmp {
        server {
                listen 1935;
                chunk_size 4096;

                application live {
                        live on;
                        record off;
                }
        }
}' >> /usr/local/nginx/conf/nginx.conf

# run nginx
sudo /usr/local/nginx/sbin/nginx
