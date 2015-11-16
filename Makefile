default: build

build:
	make clean && cd misc/pip_pkg; python setup.py bdist_wheel

clean:
	rm misc/pip_pkg/dist/PYCLOAK-`cat version`-py3-none-any.whl; cd misc/pip_pkg; rm -rf pycloak dist MANIFEST

install:
	pip install --upgrade misc/pip_pkg/dist/PYCLOAK-`cat version`-py3-none-any.whl

upload:
	./bash/upload_lib
