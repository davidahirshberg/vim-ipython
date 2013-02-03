#!/usr/bin/env python

import sys, os, subprocess, json

config=dict(hostname='huxley', # needn't be the host of the kernel -- if the host is specified in the kernel json file (see ipk.py), that will be used instead
            name=sys.argv[1] if len(sys.argv) > 0 else "*",
            profile_dir = '~/.ipython/profile_default')

# get ports for most recently started kernel
kernel_info_json = subprocess.check_output("ssh -t {hostname} 'cd {profile_dir}/security && cat `ls -t {name}.json | tail -n1`'".format(**config), shell=True) 
kernel_info = json.loads(kernel_info_json)

# forward appropriate ports
# we may have sessions open with kernels on multiple machines, so remote ports may be used more than once
# locally, use ports defined by the session name, which is unique
all_roles = [role for role in kernel_info.keys() if role.endswith('_port')]
def local_port(role, name):
    return 30000 + 500*all_roles.index(role) + (hash(name) % 500)

ports = {role: (local_port(role, kernel_info['name']), remote_port)  
            for role, remote_port in kernel_info.items() if role.endswith('_port')}
def forward():
    return [subprocess.Popen('ssh {hostname} -f -N -L {local_port}:localhost:{remote_port}'.format(remote_port=remote_port, 
                                                                                                   local_port=local_port, 
                                                                                                   hostname=kernel_info.get('hostname',config['hostname'])), shell=True)
        for (local_port, remote_port) in ports.values()]

# write out local kernel info file
for role, (local_port,_) in ports.items():
    kernel_info[role] = local_port
kernel_info_file = os.path.join(config['profile_dir'], 'security', '{name}.json'.format(**config))
with open(os.path.expanduser(kernel_info_file), 'w') as f:
    json.dump(kernel_info, f)

try: 
    forward_processes = forward()
    os.system('IPython console --existing {}'.format(kernel_info_file))
finally:
    for proc in forward_processes:
        proc.kill()
    os.remove(os.path.expanduser(kernel_info_file))
