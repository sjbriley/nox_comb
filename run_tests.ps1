# pass with "./run_tests.ps1 -build"
param(
    [switch]$build = $null
)

# exit on failure
$ErrorActionPreference = "Stop"

# print lines
Set-PSDebug -Trace 1

if (-Not (Test-Path -Path virtualenv)) {
    python -m venv virtualenv
    ./virtualenv/scripts/python -m pip install --upgrade pip
}

./virtualenv/scripts/activate

pip install nox
nox --verbose
if ($LASTEXITCODE -ne 0){
    exit $LASTEXITCODE
}

if ($build) {
    python setup.py sdist
    $dist = ls dist/
    foreach ($file in $dist){
        pip install ./dist/$file
    }
}
