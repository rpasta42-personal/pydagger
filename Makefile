SHELL := /bin/bash
default: build

virtenvinstall:
	pip install virtualenv virtualenvwrapper

setup: virtenvinstall
	source `which virtualenvwrapper.sh` && mkvirtualenv pycloak --python=`which python3` && workon pycloak && pip install --upgrade setuptools pip wheel && pip install -r misc/freeze.txt; deactivate

build:
	workon pycloak; make clean && cd misc/pip_pkg; python setup.py bdist_wheel

clean:
	rm misc/pip_pkg/dist/PYCLOAK-`cat version`-py3-none-any.whl; cd misc/pip_pkg; rm -rf pycloak dist MANIFEST

install: build
	pip install --upgrade misc/pip_pkg/dist/PYCLOAK-`cat version`-py3-none-any.whl
upload:
	./misc/bash/upload_lib
lazy_install:
	source `which virtualenvwrapper.sh` && workon pycloak && make && make install && deactivate && workon icloak-updater && make && make install && workon icloak-updater-starter && make && make install
