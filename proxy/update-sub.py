#!/bin/python

from base64 import decodebytes
from ipaddress import ip_network, IPv4Network, IPv6Network, _IPv4Constants, _IPv6Constants
from requests import get
from sys import stderr
from urllib.parse import parse_qs, unquote, urlparse
from yaml import safe_dump

SUB_URL = open('/home/clash/sub-url.txt', 'r').read().strip()
CLASH_CONFIG_FILE = '/home/clash/.config/clash/config.yaml'

EXTERNAL_UI_PATH = '/usr/share/clash-dashboard-git'
API_SECRET = open('/home/clash/api-secret.txt', 'r').read()

CN_DOMAINS = []
NON_CN_DOMAINS = []
CN_DNS_SERVER_ADDRESSES = ['223.5.5.5', '1.12.12.12']
NON_CN_DNS_SERVER_ADDRESSES = ['8.8.8.8', '1.1.1.1']
TELEGRAM_ADDRESSES = [
    '91.108.56.0/22', '91.108.4.0/22', '91.108.8.0/22', '91.108.16.0/22',
    '91.108.12.0/22', '149.154.160.0/20', '91.105.192.0/23', '91.108.20.0/22',
    '185.76.151.0/24', '2001:b28:f23d::/48', '2001:b28:f23f::/48',
    '2001:67c:4e8::/48', '2001:b28:f23c::/48', '2a0a:f280::/32'
]  # https://core.telegram.org/resources/cidr.txt


def fill(s: str) -> str:
    return s + '=' * (4 - len(s) % 4)


def get_raw_sub() -> bytes:
    return get(SUB_URL).content


def address_to_rule(address, target: str, no_resolve=False) -> str:
    network = ip_network(address)
    if isinstance(network, IPv4Network):
        rule = f'IP-CIDR,{network},{target}'
    elif isinstance(network, IPv6Network):
        rule = f'IP-CIDR6,{network},{target}'
    else:
        raise RuntimeError(f'Unknown address {address}')
    if no_resolve:
        rule += ',no-resolve'
    return rule


def addresses_to_rules(addresses: list,
                       target: str,
                       no_resolve=False) -> list[str]:
    return [
        address_to_rule(address, target, no_resolve) for address in addresses
    ]


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
sub['rules'] = addresses_to_rules(CN_DNS_SERVER_ADDRESSES, '国内域名解析', True) + \
               addresses_to_rules(NON_CN_DNS_SERVER_ADDRESSES, '国外域名解析', True) + \
               ['DOMAIN-SUFFIX,%s,国外' % domain for domain in NON_CN_DOMAINS] + \
               ['DOMAIN-SUFFIX,%s,国内' % domain for domain in CN_DOMAINS] + \
               addresses_to_rules(_IPv4Constants._private_networks + _IPv6Constants._private_networks, '私网') + \
               addresses_to_rules(TELEGRAM_ADDRESSES, 'Telegram') + \
               ['GEOIP,CN,国内', 'MATCH,国外']
# Clash trys to translate it into IPv4, and this breaks everything
sub['rules'].remove('IP-CIDR6,::ffff:0:0/96,私网')

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
    'name': 'Telegram',
    'type': 'select',
    'proxies': ['代理', 'DIRECT', 'REJECT']
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
    'name': '私网',
    'type': 'select',
    'proxies': ['DIRECT', '代理', 'REJECT']
}]

with open(CLASH_CONFIG_FILE, 'w') as config_file:
    safe_dump(sub, config_file, allow_unicode=True)
