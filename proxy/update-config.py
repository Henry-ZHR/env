import base64
import json
import os
import pwd
import re
import requests
import subprocess
import sys

from pathlib import Path
from tempfile import TemporaryDirectory

SCRIPT_DIR = Path(__file__).parent

SB_CONFIG_DIR = Path('/etc/sing-box')
SB_CONFIG_FILE = SB_CONFIG_DIR / 'config.json'
SB_RULE_SETS_DIR = SB_CONFIG_DIR / 'rule-sets'

MOSDNS_CONFIG_DIR = Path('/etc/mosdns')

REQUESTS_PROXIES = {'https': 'http://127.0.0.1:1080'}
GEOSITE_TAGS = ['cn', 'apple@cn', 'google@cn', 'microsoft@cn']
GFWLIST_URL = 'https://raw.githubusercontent.com/gfwlist/gfwlist/refs/heads/master/gfwlist.txt'
DOMAIN_VALIDATE_RE = re.compile(
    "^(((?!-))(xn--|_)?[a-z0-9-]{0,61}[a-z0-9]{1,1}\\.)*(xn--)?([a-z0-9][a-z0-9\\-]{0,60}|[a-z0-9-]{1,30}\\.[a-z]{2,})$"
)


def ensure_permission(path: str, user: str, mode: int):
    passwd = pwd.getpwnam(user)
    os.chown(path, passwd.pw_uid, passwd.pw_gid)
    os.chmod(path, mode)


def check_root():
    assert os.getuid() == 0


# Returns: (geoip_content, geosite_content)
def unpack_geo() -> tuple[str, str]:
    _tmp_dir = TemporaryDirectory()
    tmp_dir = Path(_tmp_dir.name)

    subprocess.check_call([
        'v2dat', 'unpack', 'geoip', '-o',
        tmp_dir.absolute(), '-f', 'cn', '/usr/share/v2ray/geoip.dat'
    ])
    with (tmp_dir / "geoip_cn.txt").open('r') as f:
        geoip_content = f.read()
    geosite_content = ''
    for tag in GEOSITE_TAGS:
        subprocess.check_call([
            'v2dat', 'unpack', 'geosite', '-o',
            tmp_dir.absolute(), '-f', tag, '/usr/share/v2ray/geosite.dat'
        ])
        with (tmp_dir / f'geosite_{tag}.txt').open('r') as f:
            geosite_content += f.read()
    return geoip_content, geosite_content


# Returns: (blacklist, whitelist)
# Format: same as geosite_xxx.txt
def get_gfwlist() -> tuple[str, str]:

    r = requests.get(GFWLIST_URL, proxies=REQUESTS_PROXIES)
    assert r.status_code == 200
    blacklist, whitelist, ignore_cnt = [], [], 0

    def add_if_valid(l: list[str], domain: str, prefix: str = None):
        if DOMAIN_VALIDATE_RE.fullmatch(domain):
            l += [(f'{prefix}:' if prefix else '') + domain]
        else:
            nonlocal ignore_cnt
            ignore_cnt += 1

    for line in base64.b64decode(r.content).decode().splitlines():
        if line.startswith('!'):
            continue
        if line.startswith('@@'):
            l = whitelist
            line = line[2:]
        else:
            l = blacklist

        if line.startswith('||'):
            add_if_valid(l, line[2:])
        elif line.startswith('|http://'):
            add_if_valid(l, line[8:], 'full')
        elif line.startswith('.'):
            add_if_valid(l, line[1:])
        elif DOMAIN_VALIDATE_RE.fullmatch(line):
            l += [line]
        else:
            ignore_cnt += 1
    if ignore_cnt > 0:
        print(f'Ignored {ignore_cnt} rule(s) from gfwlist', file=sys.stderr)
    blacklist = '\n'.join(dict.fromkeys(blacklist)) + '\n'
    whitelist = '\n'.join(dict.fromkeys(whitelist)) + '\n'
    return blacklist, whitelist


def update_sb_config():

    def run_serenity() -> str:
        serenity_workdir = TemporaryDirectory()
        ensure_permission(serenity_workdir.name, 'serenity', 0o700)
        subprocess.check_call(['global-proxy', 'enable', 'serenity'])
        output = subprocess.check_output([
            'sudo', '-u', 'serenity', 'serenity', 'export', 'default', '-C',
            '/etc/serenity', '-D', serenity_workdir.name
        ])
        subprocess.check_call(['global-proxy', 'disable', 'serenity'])
        return output

    serenity_output = run_serenity()
    outbounds = json.loads(serenity_output)['outbounds'][3:]
    assert outbounds[0]['tag'] == 'default'

    with (SCRIPT_DIR / 'sing-box' / 'basic-config.json').open('r') as f:
        config_content = json.loads(f.read())
    assert config_content['outbounds'][0]['tag'] == 'proxy'
    config_content['outbounds'][0]['outbounds'] = outbounds[0]['outbounds']
    config_content['outbounds'] += outbounds[1:]
    with (SB_CONFIG_DIR / 'clash-api-secret.txt').open('r') as f:
        config_content['experimental']['clash_api']['secret'] = f.read()

    SB_CONFIG_FILE.replace(SB_CONFIG_DIR / 'config.json.bak')
    with SB_CONFIG_FILE.open('w') as f:
        json.dump(config_content, f, ensure_ascii=False, indent=4)
    ensure_permission(SB_CONFIG_FILE.absolute(), 'sing-box', 0o600)


def update_sb_rule_sets(geoip_content: str, geosite_content: str,
                        gfwlist_whitelist: list[str]):

    def gen_rules(rule: dict) -> dict:
        return {'version': 1, 'rules': [rule]}

    with (SB_RULE_SETS_DIR / 'geoip-cn.json').open('w') as f:
        json.dump(gen_rules({'ip_cidr': geoip_content.split()}), f, indent=4)

    def txt_to_rule(txt: str) -> dict:
        rule = {
            'domain': [],
            'domain_suffix': [],
            'domain_keyword': [],
            'domain_regex': []
        }
        for line in txt.splitlines():
            if line.startswith('keyword:'):
                rule['domain_keyword'] += [line[8:]]
            elif line.startswith('regexp:'):
                rule['domain_regex'] += [line[7:]]
            elif line.startswith('full:'):
                rule['domain'] += [line[5:]]
            else:
                assert ':' not in line
                rule['domain_suffix'] += [line]
        return rule

    with (SB_RULE_SETS_DIR / 'geosite-cn.json').open('w') as f:
        json.dump(gen_rules(txt_to_rule(geosite_content)), f, indent=4)
    with (SB_RULE_SETS_DIR / 'gfwlist-whitelist.json').open('w') as f:
        json.dump(gen_rules(txt_to_rule(gfwlist_whitelist)), f, indent=4)


def update_mosdns_config(geosite_content: str, gfwlist: str,
                         gfwlist_whitelist: str):
    with (SCRIPT_DIR / 'mosdns' / 'config.yaml').open('r') as f:
        config_content = f.read()
    with (MOSDNS_CONFIG_DIR / 'config.yaml').open('w') as f:
        f.write(config_content)
    with (MOSDNS_CONFIG_DIR / 'geosite-cn.txt').open('w') as f:
        f.write(geosite_content)
    with (MOSDNS_CONFIG_DIR / 'gfwlist.txt').open('w') as f:
        f.write(gfwlist)
    with (MOSDNS_CONFIG_DIR / 'gfwlist-whitelist.txt').open('w') as f:
        f.write(gfwlist_whitelist)
    pass


if __name__ == '__main__':
    check_root()

    # sing-box
    update_sb_config()
    geoip_content, geosite_content = unpack_geo()
    gfwlist, gfwlist_whitelist = get_gfwlist()
    update_sb_rule_sets(geoip_content, geosite_content, gfwlist_whitelist)
    subprocess.check_call([
        'sudo', '-u', 'sing-box', 'sing-box', 'check', '-C',
        SB_CONFIG_DIR.absolute()
    ])

    # mosdns
    update_mosdns_config(geosite_content, gfwlist, gfwlist_whitelist)
