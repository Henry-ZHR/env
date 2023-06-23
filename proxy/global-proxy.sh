#!/bin/bash

set -e


readonly TPROXY_PORT=1082

readonly CONNMARK=23
readonly TABLE_ID=233

readonly PROTOCOLS=(tcp udp)

readonly V4_LOCAL_IPS=(0.0.0.0 127.0.0.1)
readonly V6_LOCAL_IPS=(:: ::1)


if [ "$#" -eq 2 ] && [[ "$1" == "set" ]]; then
    for exe in iptables ip6tables; do
        $exe -t mangle -A OUTPUT -m owner --uid-owner $2 -j OUTPUT_DIVERT
    done
    exit
fi


if [ "$#" -eq 2 ] && [[ "$1" == "unset" ]]; then
    for exe in iptables ip6tables; do
        $exe -t mangle -D OUTPUT -m owner --uid-owner $2 -j OUTPUT_DIVERT
    done
    exit
fi


if [ "$#" -eq 1 ] && [[ "$1" == "init" ]]; then
    for exe in iptables ip6tables; do
        $exe -t mangle -N PREROUTING_DIVERT
        for proto in ${PROTOCOLS[@]}; do
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
        for proto in ${PROTOCOLS[@]}; do
            $exe -t mangle -A OUTPUT_DIVERT -p $proto -j MARK --set-mark $CONNMARK
        done
    done

    for p in 4 6; do
        ip -$p rule add fwmark $CONNMARK table $TABLE_ID
        ip -$p route add local default table $TABLE_ID dev lo
    done

    exit
fi


if [ "$#" -eq 1 ] && [[ "$1" == "fini" ]]; then
    for p in 4 6; do
        ip -$p route del local default table $TABLE_ID dev lo
        ip -$p rule del fwmark $CONNMARK table $TABLE_ID
    done

    for exe in iptables ip6tables; do
        $exe -t mangle -D PREROUTING -j PREROUTING_DIVERT
        $exe -t mangle -F PREROUTING_DIVERT
        $exe -t mangle -F OUTPUT_DIVERT
        $exe -t mangle -X PREROUTING_DIVERT
        $exe -t mangle -X OUTPUT_DIVERT
    done

    exit
fi

echo "Usage:"
echo "  $0 { init | fini }"
echo "  $0 { set | unset } <user>"
exit 1
