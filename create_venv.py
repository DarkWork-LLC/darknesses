#!/usr/bin/env python3
import os, subprocess, shutil

venv_path = '/home/bimo/workspace/darknesses/.venv'

# Remove existing venv
if os.path.exists(venv_path):
    shutil.rmtree(venv_path)

# Create directory structure
os.makedirs(os.path.join(venv_path, 'bin'), exist_ok=True)
os.makedirs(os.path.join(venv_path, 'lib'), exist_ok=True)
os.makedirs(os.path.join(venv_path, 'include'), exist_ok=True)
os.makedirs(os.path.join(venv_path, 'lib64'), exist_ok=True)

# Create symlinks
python3_path = '/usr/bin/python3'
os.symlink(python3_path, os.path.join(venv_path, 'bin', 'python'))
os.symlink(python3_path, os.path.join(venv_path, 'bin', 'python3'))

# Install pip using get-pip.py
import subprocess
subprocess.run(['curl', '-sS', 'https://bootstrap.pypa.io/get-pip.py', '-o', '/tmp/get-pip.py'])
subprocess.run([os.path.join(venv_path, 'bin', 'python'), '/tmp/get-pip.py'])

# Install requirements
subprocess.run([os.path.join(venv_path, 'bin', 'python'), '-m', 'pip', 'install', '-r', '/home/bimo/workspace/darknesses/requirements/dev.txt'])

print('Venv created with pip and requirements installed')
