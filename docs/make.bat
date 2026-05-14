@ECHO OFF
pushd %~dp0

REM Minimal Sphinx make.bat for Windows
if "%SPHINXBUILD%" == "" (
    set SPHINXBUILD=sphinx-build
)
set SOURCEDIR=.
set BUILDDIR=_build

if "%1" == "" goto help

%SPHINXBUILD% >NUL 2>NUL
if errorlevel 9009 (
    echo.sphinx-build was not found. Install Sphinx from requirements-dev.txt.
    exit /b 1
)

if "%1" == "html" (
    %SPHINXBUILD% -b html %SOURCEDIR% %BUILDDIR%\html %SPHINXOPTS%
    goto end
)
if "%1" == "markdown" (
    %SPHINXBUILD% -b markdown %SOURCEDIR% %BUILDDIR%\markdown %SPHINXOPTS%
    goto end
)
if "%1" == "clean" (
    if exist %BUILDDIR% rmdir /s /q %BUILDDIR%
    goto end
)

:help
%SPHINXBUILD% -M help %SOURCEDIR% %BUILDDIR% %SPHINXOPTS%

:end
popd
