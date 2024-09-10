import json
import os
import pwd
import subprocess

from pathlib import Path
from tempfile import TemporaryDirectory

CONFIG_DIR = Path('/etc/sing-box')
CONFIG_FILE = CONFIG_DIR / 'config.json'
RULE_SETS_DIR = CONFIG_DIR / 'rule-sets'


def ensure_permission(path: str, user: str, mode: int):
    passwd = pwd.getpwnam(user)
    os.chown(path, passwd.pw_uid, passwd.pw_gid)
    os.chmod(path, mode)


def update_main_config():
    serenity_workdir = TemporaryDirectory()
    ensure_permission(serenity_workdir.name, 'serenity', 0o700)
    subprocess.check_call(['global-proxy', 'enable', 'serenity'])
    serenity_output = subprocess.check_output([
        'sudo', '-u', 'serenity', 'serenity', 'export', 'default', '-C',
        '/etc/serenity', '-D', serenity_workdir.name
    ])
    subprocess.check_call(['global-proxy', 'disable', 'serenity'])
    del serenity_workdir

    outbounds = json.loads(serenity_output)['outbounds'][3:]
    assert outbounds[0]['tag'] == 'default'

    script_dir = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(script_dir, 'basic-config.json'), 'r') as f:
        config_content = json.loads(f.read())
    assert config_content['outbounds'][0]['tag'] == 'proxy'
    config_content['outbounds'][0]['outbounds'] = outbounds[0]['outbounds']
    config_content['outbounds'] += outbounds[1:]
    with (CONFIG_DIR / 'clash-api-secret.txt').open('r') as f:
        config_content['experimental']['clash_api']['secret'] = f.read()

    CONFIG_FILE.replace(CONFIG_DIR / 'config.json.bak')
    with CONFIG_FILE.open('w') as f:
        json.dump(config_content, f, ensure_ascii=False, indent=4)
    ensure_permission(CONFIG_FILE.absolute(), 'sing-box', 0o600)


def generate_rule_set():
    RULE_SETS_DIR.mkdir(exist_ok=True)
    RULE_SETS_DIR.chmod(0o755)
    tmp_dir = TemporaryDirectory()

    subprocess.check_call([
        'v2dat', 'unpack', 'geoip', '-o', tmp_dir.name, '-f', 'cn',
        '/usr/share/v2ray/geoip.dat'
    ])
    with open(os.path.join(tmp_dir.name, 'geoip_cn.txt'), 'r') as f:
        cn_ips = f.read().split()
    with (RULE_SETS_DIR / 'geoip-cn.json').open('w') as f:
        json.dump({'version': 1, 'rules': [{"ip_cidr": cn_ips}]}, f)

    geosite_cn_rules = {
        'domain': [],
        'domain_suffix': [],
        'domain_keyword': [],
        'domain_regex': []
    }
    for tag in ['cn', 'google@cn', 'apple@cn']:
        subprocess.check_call([
            'v2dat', 'unpack', 'geosite', '-o', tmp_dir.name, '-f', tag,
            '/usr/share/v2ray/geosite.dat'
        ])
        with open(os.path.join(tmp_dir.name, f'geosite_{tag}.txt'), 'r') as f:
            for line in f.read().split():
                if line.startswith('keyword:'):
                    geosite_cn_rules['domain_keyword'] += [line[8:]]
                elif line.startswith('regexp:'):
                    geosite_cn_rules['domain_regex'] += [line[7:]]
                elif line.startswith('full:'):
                    geosite_cn_rules['domain'] += [line[5:]]
                else:
                    assert ':' not in line
                    geosite_cn_rules['domain_suffix'] += [line]
    with (RULE_SETS_DIR / 'geosite-cn.json').open('w') as f:
        json.dump({'version': 1, 'rules': [geosite_cn_rules]}, f)


if __name__ == '__main__':
    update_main_config()
    generate_rule_set()
    subprocess.check_call([
        'sudo', '-u', 'sing-box', 'sing-box', 'check', '-C',
        CONFIG_DIR.absolute()
    ])
