default: build

build:
	make clean; cd misc/pip_pkg; ln -s ../../src pycloak; python setup.py sdist; mv dist/PYCLOAK-0.0.1.tar.gz ../../

clean:
	rm PYCLOAK-0.0.1.tar.gz; cd misc/pip_pkg; rm -rf pycloak dist MANIFEST

install:
	python3 setup.py install
