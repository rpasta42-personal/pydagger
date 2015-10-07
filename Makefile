default: build

build:
	make clean && cd misc/pip_pkg; python setup.py bdist_wheel && cp dist/*.whl ../../ && echo $(git rev-list HEAD --count) >> version

clean:
	rm PYCLOAK-0.0.1.tar.gz; cd misc/pip_pkg; rm -rf pycloak dist MANIFEST

install:
	pip install --upgrade PYCLOAK-0.0.1-py3-none-any.whl

upload:
	./upload_lib
