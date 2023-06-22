import os
import pwd
import requests
import subprocess
import time

subprocess.check_call(['global-proxy', 'set', 'serenity'])
serenity = subprocess.Popen([
    'sudo', '-u', 'serenity', 'serenity', 'run', '-c',
    '/etc/serenity/config.json'
])
try:
    time.sleep(5)
    config_content = requests.get('http://127.0.0.1:1070/').content
    with open('/etc/sing-box/config.json', 'w') as config_file:
        config_file.write(config_content.decode())
    passwd = pwd.getpwnam('sing-box')
    os.chown('/etc/sing-box/config.json', passwd.pw_uid, passwd.pw_gid)
    os.chmod('/etc/sing-box/config.json', 0o600)
except:
    raise
finally:
    serenity.terminate()
    subprocess.check_call(['global-proxy', 'unset', 'serenity'])
