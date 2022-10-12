#!/bin/python

from base64 import b64decode
from ipaddress import ip_network, IPv4Network, IPv6Network, _IPv4Constants, _IPv6Constants
from requests import get
from sys import stderr
from urllib.parse import parse_qs, unquote, urlparse
from yaml import safe_dump, safe_load

SUBSCRIPTIONS = safe_load(open('/etc/clash/subscriptions.yaml', 'r'))
CLASH_CONFIG_FILE = '/etc/clash/config.yaml'
EXTERNAL_UI_PATH = '/usr/share/yacd'
API_SECRET = open('/etc/clash/api-secret.txt', 'r').read()

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


def fill(s: bytes) -> bytes:
    return s + b'=' * (4 - len(s) % 4)


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


def parse_proxy(s: str, **kwargs) -> dict:
    has_udp = kwargs.get('has_udp', True)
    r = urlparse(s)
    if r.scheme == 'ss':
        cipher, password = b64decode(fill(
            r.username.encode())).decode().split(':')
        proxy = {
            'name': unquote(r.fragment),
            'type': 'ss',
            'server': r.hostname,
            'port': r.port,
            'cipher': cipher,
            'password': password,
            'udp': has_udp
        }
        return proxy
    if r.scheme == 'trojan':
        proxy = {
            'name': unquote(r.fragment),
            'type': 'trojan',
            'server': r.hostname,
            'port': r.port,
            'password': r.username,
            'udp': has_udp,
            'skip-cert-verify': False
        }
        q = parse_qs(r.query)
        if 'sni' in q:
            proxy['sni'] = q['sni'][0]
        return proxy
    return {}


cfg = {
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
    'proxies': [],
    'proxy-groups': [{
        'name': '代理',
        'type': 'select',
        'proxies': []
    }]
}
cfg['rules'] = addresses_to_rules(CN_DNS_SERVER_ADDRESSES, '国内域名解析', True) + \
               addresses_to_rules(NON_CN_DNS_SERVER_ADDRESSES, '国外域名解析', True) + \
               ['DOMAIN-SUFFIX,%s,国外' % domain for domain in NON_CN_DOMAINS] + \
               ['DOMAIN-SUFFIX,%s,国内' % domain for domain in CN_DOMAINS] + \
               addresses_to_rules(_IPv4Constants._private_networks + _IPv6Constants._private_networks, '私网') + \
               addresses_to_rules(TELEGRAM_ADDRESSES, 'Telegram') + \
               ['GEOIP,CN,国内', 'MATCH,国外']
# Clash trys to translate it into IPv4, and this breaks everything
cfg['rules'].remove('IP-CIDR6,::ffff:0:0/96,私网')

for sub in SUBSCRIPTIONS:
    cfg['proxy-groups'][0]['proxies'].append(sub['name'])
    group = {'name': sub['name'], 'type': 'select', 'proxies': []}
    for s in b64decode(get(sub['url']).content).decode().split():
        proxy = parse_proxy(s, has_udp=sub['has_udp'])
        if not proxy:
            print(f'Ignore unknown proxy: {s}', file=stderr)
            continue
        proxy['name'] = sub['proxy_name_prefix'] + proxy['name']
        cfg['proxies'].append(proxy)
        group['proxies'].append(proxy['name'])
    cfg['proxy-groups'].append(group)

cfg['proxy-groups'] += [{
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
    safe_dump(cfg, config_file, allow_unicode=True)
