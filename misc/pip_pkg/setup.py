#from distutils.core import setup
from setuptools import setup, find_packages
import subprocess

p = subprocess.Popen(['git', 'rev-list', 'HEAD', '--count'], stdout=subprocess.PIPE)
out, err = p.communicate()
code = p.wait()

commit_count = "UNKNOWN"
if code == 0:
   commit_count = str(out, "ascii")

VERSION="0.1." + commit_count

with open("../../version", "w") as fh:
   fh.write(VERSION)
   fh.flush()

setup (
   name="PYCLOAK",
   version=VERSION,
   author="Kostyantyn Kovalskyy",
   author_email="konstantin@icloak.org",
   #packages=["pycloak", "pycloak.test"],
   packages=["pycloak", "pycloak.IPC", "pycloak.mac", "pycloak.win"],
   package_dir={"pycloak": "../../src"},
   #binary files go here
   #scripts=['bin/ifs-mount', 'bin/ifs-test'],
   #url='http://pypi.python.org/pypi/ICLOAKFS/',
   url='http://pypi.python.org/pypi/PYCLOAK/',
   #license='LICENSE.txt',

   description="ICLOAK helper library with miscellaneous tools." #,
   #long_description=open("README.md").read(),

   #install_requires=['fs', 'pyfuse', 'cstruct >= 1.0', 'pbkdf2']
)
