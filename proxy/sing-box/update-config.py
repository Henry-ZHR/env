import json
import os
import pwd
import subprocess

from subprocess import PIPE, Popen
from tempfile import TemporaryDirectory


def ensure_permission(path: str, user: str, mode: int):
    passwd = pwd.getpwnam(user)
    os.chown(path, passwd.pw_uid, passwd.pw_gid)
    os.chmod(path, mode)


serenity_workdir = TemporaryDirectory()
ensure_permission(serenity_workdir.name, 'serenity', 0o700)
subprocess.check_call(['global-proxy', 'enable', 'serenity'])
serenity = Popen([
    'sudo', '-u', 'serenity', 'serenity', 'export', 'default', '-C',
    '/etc/serenity', '-D', serenity_workdir.name
],
                 stdout=PIPE,
                 stderr=PIPE)
serenity_output, serenity_err = serenity.communicate()
subprocess.check_call(['global-proxy', 'disable', 'serenity'])
print('Serenity log:')
print(serenity_err.decode())
if serenity.returncode != 0:
    print('Serenity return code:', serenity.returncode)
    exit(1)

s_result = json.loads(serenity_output)
outbounds = s_result['outbounds'][3:]
assert outbounds[0]['tag'] == 'default'

script_dir = os.path.dirname(os.path.realpath(__file__))
with open(os.path.join(script_dir, 'basic-config.json'), 'r') as f:
    config_content = json.loads(f.read())
assert config_content['outbounds'][0]['tag'] == 'proxy'
config_content['outbounds'][0]['outbounds'] = outbounds[0]['outbounds']
config_content['outbounds'] += outbounds[1:]
with open('/etc/sing-box/clash-api-secret.txt', 'r') as f:
    config_content['experimental']['clash_api']['secret'] = f.read()

os.remove('/etc/sing-box/config.json.bak')
os.rename('/etc/sing-box/config.json', '/etc/sing-box/config.json.bak')
with open('/etc/sing-box/config.json', 'w') as config_file:
    json.dump(config_content, config_file, ensure_ascii=False, indent=4)
ensure_permission('/etc/sing-box/config.json', 'sing-box', 0o600)
subprocess.check_call(
    ['sudo', '-u', 'sing-box', 'sing-box', 'check', '-C', '/etc/sing-box'])
