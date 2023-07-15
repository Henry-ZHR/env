#!/bin/bash

cd "$(dirname ${0})"

sudo cp config.yaml /etc/mosdns

pushd v2dat
mkdir out
go run ./ unpack geosite -o out -f cn -f google@cn -f apple@cn -f geolocation-!cn /usr/share/v2ray/geosite.dat
sudo cp out/* /etc/mosdns
rm -rf out
popd

sudo chown -R root:root /etc/mosdns
