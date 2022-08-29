## nox_comb

Simple wrapper for nox in order to combine output from several different linters into one file.

## Usage

```
pip install nox_comb
nox_comb
```
Will execute nox on noxfile.py and combine outputs from all linters into lint_report.

## Args

Specify output file, defaults to lint_report -
```
nox_comb --output_file lint_report
```

Specify which linters should not report output to combined file, even if specified in noxfile.py -
```
nox_comb --disabled_output flake8,pylint
```

Specify noxfile to be ran, defaults to noxfile.py
```
nox_comb --nox_file noxfile2.py
```

Extra arguments provided to nox_comb will be passed to nox, such as -
```
comb_nox --output_file my_output --disabled_output pylint,flake8 --envdir dir -x --verbose
```
Will be ran as -
```
nox --envdir dir -x --verbose
```

## Project Structure
The top level directory should contain the noxfile.py and any configuration files, as well as a virtual environment with nox_comb installed.

## Limitations
Currently nox_comb is able to combine output from pylint, flake8, mypy, and pytest.

