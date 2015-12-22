@ECHO OFF
SETLOCAL ENABLEDELAYEDEXPANSION

FOR /F "tokens=* USEBACKQ" %%F in (`type version`) do (
	SET version=%%F

)

echo "CURRENT VERSION %version%

set SDKPATH="C:\Program Files\Microsoft SDKs\Windows\v7.1\Bin"


IF "%1"=="" GOTO :build
GOTO :%1
GOTO :error_case

:dev
	%SDKPATH%/setenv /x64 /release
	set MSSDK=1
	set DISTUTILS_USE_SDK=1
	REM Just in case we have virtualenv running and installed
	deactivate
	pip install virtualenvwrapper-win
	mkvirtualenv pycloak
	workon pycloak
	pip install --upgrade setuptools
	pip install --upgrade pip
	GOTO end_case

:build
	ECHO BUILDING
	cd misc\pip_pkg
        python setup.py bdist_wheel
	GOTO end_case
:clean
	ECHO CLEANING
	del misc/pip_pkg/dist/PYCLOAK*
        cd misc/pip_pkg
        del pycloak dist MANIFEST
	GOTO end_case

:install
	pip install --upgrade misc/pip_pkg/dist/PYCLOAK-%version%-py3-none-any.whl
	GOTO end_case

:lazy_install
	echo INSTALLING LAZILLY ON VIRTENV FOR UPDATER BUILDER. DELETE ME LATER
	workon icloak-updater
	make
	make install
	workon icloak-updater-starter
	make
	make install
	deactivate
	GOTO end_case

:error_case
	ECHO Invalid Option "%1"
	GOTO end_case

:end_case
	ECHO Done...
	GOTO :EOF
