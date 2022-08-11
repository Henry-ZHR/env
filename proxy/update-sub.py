#!/bin/python

from base64 import decodebytes
from ipaddress import _IPv4Constants, _IPv6Constants
from requests import get
from sys import stderr
from urllib.parse import parse_qs, unquote, urlparse
from yaml import safe_dump

SUB_URL_FILE = '/home/clash/sub-url.txt'
CLASH_CONFIG_FILE = '/home/clash/.config/clash/config.yaml'

EXTERNAL_UI_PATH = '/home/clash/clash-dashboard/dist'
API_SECRET = open('/home/clash/api-secret.txt').read()

CN_DOMAINS = []
NON_CN_DOMAINS = []
CN_DNS_SERVER_IPS = ['223.5.5.5/32', '1.12.12.12/32']
NON_CN_DNS_SERVER_IPS = ['8.8.8.8/32', '1.1.1.1/32']


def fill(s: str) -> str:
    return s + '=' * (4 - len(s) % 4)


def get_raw_sub() -> bytes:
    return get(open(SUB_URL_FILE, 'r').read().strip()).content


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
               [f'IP-CIDR,{ip},私有' for ip in _IPv4Constants._private_networks] + \
               [f'IP-CIDR6,{ip},私有' for ip in _IPv6Constants._private_networks] + \
               ['GEOIP,CN,国内', 'MATCH,国外']
# Clash is trying to translate it into IPv4, and this breaks everything
sub['rules'].remove('IP-CIDR6,::ffff:0:0/96,私有')

proxy_names = []

for s in decodebytes(get_raw_sub()).decode().split():
    r = urlparse(s)
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
    if r.scheme == 'trojan':
        proxy = {
            'name': unquote(r.fragment),
            'type': 'trojan',
            'server': r.hostname,
            'port': r.port,
            'password': r.username,
            'udp': True,
            'skip-cert-verify': False
        }
        t = parse_qs(r.query)
        if 'sni' in t:
            proxy['sni'] = t['sni'][0]
        sub['proxies'].append(proxy)
        proxy_names.append(proxy['name'])
        continue
    print('Ignore unknown server', file=stderr)

sub['proxy-groups'] = [{
    'name': '代理',
    'type': 'select',
    'proxies': proxy_names
}, {
    'name': '国外',
    'type': 'select',
    'proxies': ['代理', 'DIRECT', 'REJECT']
}, {
    'name': '国内',
    'type': 'select',
    'proxies': ['DIRECT', '代理', 'REJECT']
}, {
    'name': '国外域名解析',
    'type': 'select',
    'proxies': ['代理', 'DIRECT', 'REJECT']
}, {
    'name': '国内域名解析',
    'type': 'select',
    'proxies': ['DIRECT', '代理', 'REJECT']
}, {
    'name': '私有',
    'type': 'select',
    'proxies': ['DIRECT', '代理', 'REJECT']
}]

with open(CLASH_CONFIG_FILE, 'w') as config_file:
    safe_dump(sub, config_file, allow_unicode=True)
