#!/bin/python

from base64 import decodebytes
from requests import get
from sys import stderr
from urllib.parse import unquote
from yaml import safe_dump

SUB_URL_FILE = '/home/clash/sub-url.txt'
CLASH_CONFIG_FILE = '/home/clash/.config/clash/config.yaml'

YACD_PATH = '/home/clash/yacd'
API_SECRET = open('/home/clash/api-secret.txt').read()

RESERVED_V4_IPS = [
    '0.0.0.0/8', '10.0.0.0/8', '100.64.0.0/10', '127.0.0.0/8',
    '169.254.0.0/16', '172.16.0.0/12', '192.0.0.0/24', '192.168.0.0/16',
    '198.18.0.0/15', '255.255.255.255/32'
]
RESERVED_V6_IPS = [
    '::/128', '::1/128', '64:ff9b:1::/48', '100::/64', 'fc00::/7', 'fe80::/10'
]
CN_DOMAINS = [
    'baidu.com', 'gov.cn', 'bilibili.com', 'hdslb.com', 'kugou.com',
    'richup.io'
]
NON_CN_DOMAINS = ['www.google.com', 'www.google.com.hk']


def fill(s: str) -> str:
    return s + '=' * (4 - len(s) % 4)


def get_raw_sub() -> bytes:
    return get(open(SUB_URL_FILE).read()).content


sub = {
    'port': 7890,
    'socks-port': 7891,
    'tproxy-port': 7893,
    'allow-lan': False,
    'mode': 'rule',
    'log-level': 'debug',
    'ipv6': True,
    'external-controller': '127.0.0.1:9090',
    'external-ui': YACD_PATH,
    'secret': API_SECRET,
    'profile': {
        'store-selected': True,
        'store-fake-ip': False
    },
    'proxies': []
}
sub['rules'] = ['DOMAIN-SUFFIX,%s,国外' % domain for domain in NON_CN_DOMAINS]+ \
               ['DOMAIN-SUFFIX,%s,国内' % domain for domain in CN_DOMAINS] + \
               ['IP-CIDR,%s,本地' % ip for ip in RESERVED_V4_IPS] + \
               ['IP-CIDR6,%s,本地' % ip for ip in RESERVED_V6_IPS] + \
               ['GEOIP,CN,国内', 'MATCH,国外']

proxy_names = []

for s in decodebytes(get_raw_sub()).decode().split():
    if s.startswith('vmess://'):
        print('Ignoring vmess server', file=stderr)
        continue
    assert s[:5] == 'ss://'
    proxy = {'type': 'ss', 'udp': True}
    proxy['cipher'], proxy['password'] = decodebytes(
        fill(s[5:s.find('@')]).encode()).decode().split(':')
    proxy['server'] = s[s.find('@') + 1:s.find(':', 5)]
    proxy['port'] = s[s.find(':', 5) + 1:s.find('#')]
    proxy['name'] = unquote(s[s.find('#') + 1:])
    sub['proxies'].append(proxy)
    proxy_names.append(proxy['name'])

sub['proxy-groups'] = [{
    'name': '国外',
    'type': 'select',
    'proxies': proxy_names + ['DIRECT']
}, {
    'name': '国内',
    'type': 'select',
    'proxies': ['DIRECT'] + proxy_names
}, {
    'name': '本地',
    'type': 'select',
    'proxies': ['DIRECT'] + proxy_names
}]

with open(CLASH_CONFIG_FILE, 'w') as config_file:
    safe_dump(sub, config_file)
