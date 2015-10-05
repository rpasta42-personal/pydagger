default: build

build:
	make clean; cd misc/pip_pkg; python setup.py sdist; cp dist/PYCLOAK-0.0.1.tar.gz ../../

clean:
	rm PYCLOAK-0.0.1.tar.gz; cd misc/pip_pkg; rm -rf pycloak dist MANIFEST

install:
	cd misc/pip_pkg; python3 setup.py install
