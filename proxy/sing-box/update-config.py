import json
import os
import pwd
import requests
import subprocess
import tempfile

import pwn


def ensure_permission(path: str, user: str, mode: int):
    passwd = pwd.getpwnam(user)
    os.chown(path, passwd.pw_uid, passwd.pw_gid)
    os.chmod(path, mode)


serenity_workdir = tempfile.TemporaryDirectory()
ensure_permission(serenity_workdir.name, 'serenity', 0o700)
subprocess.check_call(['global-proxy', 'enable', 'serenity'])
serenity = pwn.process([
    'sudo', '-u', 'serenity', 'serenity', 'run', '-C', '/etc/serenity', '-D',
    serenity_workdir.name
])
serenity_output = b''
try:
    serenity_output += serenity.recvuntil(b'serenity started')
    s_result = json.loads(requests.get('http://127.0.0.1:1070/').content)
    outbounds = s_result['outbounds'][3:]
    assert outbounds[0]['tag'] == 'Default'

    script_dir = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(script_dir, 'basic-config.json'),
              'r') as basic_config_file:
        config_content = json.loads(basic_config_file.read())
    assert config_content['outbounds'][0]['tag'] == 'proxy'
    config_content['outbounds'][0]['outbounds'] = outbounds[0]['outbounds']
    config_content['outbounds'] += outbounds[1:]
    with open('/etc/sing-box/clash-api-secret.txt', 'r') as secret_file:
        secret = secret_file.read()
        config_content['experimental']['clash_api']['secret'] = secret

    os.remove('/etc/sing-box/config.json.bak')
    os.rename('/etc/sing-box/config.json', '/etc/sing-box/config.json.bak')
    with open('/etc/sing-box/config.json', 'w') as config_file:
        json.dump(config_content, config_file, ensure_ascii=False, indent=4)
    ensure_permission('/etc/sing-box/config.json', 'sing-box', 0o600)
    subprocess.check_call(
        ['sudo', '-u', 'sing-box', 'sing-box', 'check', '-C', '/etc/sing-box'])
except:
    raise
finally:
    serenity.terminate()
    serenity_output += serenity.recvall()
    print('Serenity log:')
    print(serenity_output.decode())
    subprocess.check_call(['global-proxy', 'disable', 'serenity'])
