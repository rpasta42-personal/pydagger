from distutils.core import setup

setup (
   name="PYCLOAK",
   version="0.0.1",
   author="Kostyantyn Kovalskyy",
   author_email="konstantin@icloak.org",
   #packages=["pycloak", "pycloak.test"],
   packages=["pycloak", "pycloak.IPC"],
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
