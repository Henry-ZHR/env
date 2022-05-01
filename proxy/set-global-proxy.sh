#!/bin/bash

set -e


readonly TPROXY_PORT=7893

readonly CONNMARK=23
readonly TABLE_ID=233

readonly V4_LOCAL_IPS=(0.0.0.0/8 10.0.0.0/8 100.64.0.0/10 127.0.0.0/8 169.254.0.0/16 172.16.0.0/12 192.0.0.0/24 192.168.0.0/16 198.18.0.0/15 255.255.255.255/32)
readonly V6_LOCAL_IPS=(::/128 ::1/128 64:ff9b:1::/48 100::/64 fc00::/7 fe80::/10)


for exe in iptables ip6tables; do
    $exe -t mangle -N PREROUTING_DIVERT
    for proto in tcp udp; do
        $exe -t mangle -A PREROUTING_DIVERT -i lo -p $proto -m mark --mark $CONNMARK -j TPROXY --on-port $TPROXY_PORT
    done
done
for exe in iptables ip6tables; do
    $exe -t mangle -A PREROUTING -j PREROUTING_DIVERT
done

for exe in iptables ip6tables; do
    $exe -t mangle -N OUTPUT_DIVERT
done
for ip in ${V4_LOCAL_IPS[@]}; do
    iptables -t mangle -A OUTPUT_DIVERT -d $ip -j RETURN
done
for ip in ${V6_LOCAL_IPS[@]}; do
    ip6tables -t mangle -A OUTPUT_DIVERT -d $ip -j RETURN
done
for exe in iptables ip6tables; do
    for proto in tcp udp; do
        $exe -t mangle -A OUTPUT_DIVERT -p $proto -j MARK --set-mark $CONNMARK
    done
done
for exe in iptables ip6tables; do
    $exe -t mangle -A OUTPUT -m owner --uid-owner zhr -j OUTPUT_DIVERT
done

for p in 4 6; do
    ip -$p rule add fwmark $CONNMARK table $TABLE_ID
    ip -$p route add local default table $TABLE_ID dev lo
done
