#!/bin/python

from base64 import decodebytes
from requests import get
from sys import stderr
from urllib.parse import parse_qs, unquote, urlparse
from yaml import safe_dump

SUB_URL_FILE = '/home/clash/sub-url.txt'
CLASH_CONFIG_FILE = '/home/clash/.config/clash/config.yaml'

EXTERNAL_UI_PATH = '/home/clash/clash-dashboard/dist'
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
NON_CN_DOMAINS = []
CN_DNS_SERVER_IPS = [
    '223.5.5.5/32', '1.12.12.12/32', '101.6.6.6/32', '9.9.9.9/32',
    '45.11.45.11/32'
]
NON_CN_DNS_SERVER_IPS = ['8.8.8.8/32', '1.1.1.1/32']


def fill(s: str) -> str:
    return s + '=' * (4 - len(s) % 4)


def get_raw_sub() -> bytes:
    return get(open(SUB_URL_FILE).read()).content


sub = {
    'port': 7890,
    'socks-port': 7891,
    'allow-lan': False,
    'mode': 'rule',
    'log-level': 'debug',
    'ipv6': True,
    'external-controller': '127.0.0.1:9090',
    'external-ui': EXTERNAL_UI_PATH,
    'secret': API_SECRET,
    'profile': {
        'store-selected': True
    },
    'proxies': []
}
sub['rules'] = ['IP-CIDR,%s,国内域名解析,no-resolve' % ip for ip in CN_DNS_SERVER_IPS] + \
               ['IP-CIDR,%s,国外域名解析,no-resolve' % ip for ip in NON_CN_DNS_SERVER_IPS] + \
               ['DOMAIN-SUFFIX,%s,国外' % domain for domain in NON_CN_DOMAINS] + \
               ['DOMAIN-SUFFIX,%s,国内' % domain for domain in CN_DOMAINS] + \
               ['IP-CIDR,%s,本地' % ip for ip in RESERVED_V4_IPS] + \
               ['IP-CIDR6,%s,本地' % ip for ip in RESERVED_V6_IPS] + \
               ['GEOIP,CN,国内', 'MATCH,国外']

proxy_names = []

for s in decodebytes(get_raw_sub()).decode().split():
    if s.startswith('ss://'):
        proxy = {'type': 'ss', 'udp': True}
        proxy['cipher'], proxy['password'] = decodebytes(
            fill(s[5:s.find('@')]).encode()).decode().split(':')
        proxy['server'] = s[s.find('@') + 1:s.find(':', 5)]
        proxy['port'] = s[s.find(':', 5) + 1:s.find('#')]
        proxy['name'] = unquote(s[s.find('#') + 1:])
        sub['proxies'].append(proxy)
        proxy_names.append(proxy['name'])
        continue
    if s.startswith('trojan://'):
        r = urlparse(s)
        t = parse_qs(r.query)
        assert r.scheme == 'trojan'
        if 'sni' not in t:
            print('SNI not present, ignored', file=stderr)
            continue
        sub['proxies'].append({
            'name': unquote(r.fragment),
            'type': 'trojan',
            'server': r.hostname,
            'port': r.port,
            'password': r.username,
            'udp': True,
            'sni': t['sni'][0],
            'skip-cert-verify': False
        })
        proxy_names.append(unquote(r.fragment))
        continue
    print('Ignore unknown server', file=stderr)

sub['proxy-groups'] = [{
    'name': '代理',
    'type': 'select',
    'proxies': proxy_names
}, {
    'name': '国外',
    'type': 'select',
    'proxies': ['代理', 'DIRECT']
}, {
    'name': '国内',
    'type': 'select',
    'proxies': ['DIRECT', '代理']
}, {
    'name': '国外域名解析',
    'type': 'select',
    'proxies': ['代理', 'DIRECT']
}, {
    'name': '国内域名解析',
    'type': 'select',
    'proxies': ['DIRECT', '代理']
}, {
    'name': '本地',
    'type': 'select',
    'proxies': ['DIRECT', '代理']
}]

with open(CLASH_CONFIG_FILE, 'w') as config_file:
    safe_dump(sub, config_file)
