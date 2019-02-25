#!/usr/bin/env python3

import os
import subprocess
import pickle
import base64
import argparse

def make_kernel(args):
    if args.clean:
        subprocess.check_output(['make', 'clean'])
        return
    cmd = ['make']
    if os.path.isdir('/ccache'):
        os.environ['CCACHE_DIR'] = '/ccache'
        cmd += ['CC=ccache gcc']

    print('Start kernel compilation in silent mode')
    subprocess.check_output(cmd + ['-j%d' %(args.num_jobs), '-s'])

def make_iproute2(args):
    if args.clean:
        subprocess.check_output(['make', 'distclean'])
        return
    subprocess.check_output(['make', '-j%d' %(args.num_jobs)])

def make_rdma_core(args):
    if args.clean:
        subprocess.check_output(['rm', '-rf', 'build'])
        return
    subprocess.check_output(['./build.sh'])

def switch_to_user(args):
    with open("/etc/passwd","a") as F:
        F.write(args.passwd + "\n");
    with open("/etc/group","a") as F:
        F.write(args.group + "\n");
    os.setgid(args.gid);
    os.setuid(args.uid);
    os.environ['HOME'] = args.home

def setup_from_pickle(args, pickle_params):
    """The script that invokes docker passes in some more detailed parameters
    about the environment in a pickle and we adjust the configuration
    accordingly"""
    p = pickle.loads(base64.b64decode(pickle_params))
    args.src = p.get("src", None)
    args.project = p.get("project", None)
    args.passwd = p.get("passwd", None)
    args.group = p.get("group", None)
    args.uid = p.get("uid", None)
    args.gid = p.get("gid", None)
    args.clean = p.get("clean", False)
    args.shell = p.get("shell", False)
    args.home = p.get('home', None)
    args.build_recipe = p.get('build_recipe', None)

parser = argparse.ArgumentParser(description='CI container')
args = parser.parse_args()

args.num_jobs = len(os.sched_getaffinity(0)) * 2
pickle_data = os.environ.get("BUILD_PICKLE")
setup_from_pickle(args, pickle_data)

switch_to_user(args)
if args.shell:
    os.execvp('/bin/bash', ['/bin/bash'])

if args.build_recipe:
    os.execvp('/bin/bash', ['/bin/bash', args.build_recipe])

if args.project == "kernel":
    make_kernel(args)
if args.project == "iproute2":
    make_iproute2(args)
if args.project == "rdma-core":
    make_rdma_core(args)
