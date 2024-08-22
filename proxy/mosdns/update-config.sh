#!/bin/bash

set -o errexit

cd "$(dirname "${0}")"

cp config.yaml /etc/mosdns
v2dat unpack geosite -o /etc/mosdns -f cn -f google@cn -f apple@cn -f geolocation-!cn /usr/share/v2ray/geosite.dat

chown -R root:root /etc/mosdns
