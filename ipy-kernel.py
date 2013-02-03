#!/usr/bin/env python

import sys, os, subprocess, platform, time, json

config = dict(ipython_dir='~/.ipython',
              profile='default',
              name=sys.argv[1],
              force='-f' in sys.argv)

security_dir = os.path.join(config['ipython_dir'], 'profile_'+config['profile'], 'security')
def kernel_file(name):
    name, ext = os.path.splitext(name)
    return os.path.expanduser(os.path.join(security_dir, '{}.json'.format(name)))

def start_process():
    proc=subprocess.Popen('ipython kernel --profile={profile}'.format(**config), 
        shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    proc.stdout.readline()
    # should be: '[IPKernelApp] To connect another client to this kernel, use:\n'
    kernel_line = proc.stdout.readline()
    # should be something like: '[IPKernelApp] --existing kernel-65040.json\n'
    filename = kernel_line.split()[2]
    return filename, proc

def augment_kernel_file(filename):
    with open(kernel_file(filename), 'r') as f:
        kernel_info = json.load(f)
    kernel_info['hostname'] = platform.node()
    kernel_info['name'] = config['name']

    with open(kernel_file(config['name']), 'w') as f:
        json.dump(kernel_info, f)

if config['force'] or not os.path.isfile(kernel_file(config['name'])):
    filename, proc = start_process()
    time.sleep(1)
    augment_kernel_file(filename)
    try: proc.wait()
    finally:
        os.remove(kernel_file(config['name']))
        os.remove(kernel_file(filename))
