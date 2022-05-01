#!/bin/bash

set -e


readonly CONNMARK=23
readonly TABLE_ID=233


for p in 4 6; do
    ip -$p route del local default table $TABLE_ID dev lo
    ip -$p rule del fwmark $CONNMARK table $TABLE_ID
done

for exe in iptables ip6tables; do
    $exe -t mangle -D PREROUTING -j PREROUTING_DIVERT
    $exe -t mangle -D OUTPUT -m owner --uid-owner zhr -j OUTPUT_DIVERT
    $exe -t mangle -F PREROUTING_DIVERT
    $exe -t mangle -F OUTPUT_DIVERT
    $exe -t mangle -X PREROUTING_DIVERT
    $exe -t mangle -X OUTPUT_DIVERT
done
