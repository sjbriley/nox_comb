"""Unit tests"""
import argparse
import sys
from unittest.mock import patch
from nox_comb.main import Linter

def test_generate_temp_nox():
    pass

def test_run_nox():
    pass

def test_combine_output():
    pass

def test_find_output():
    pass

def test_arg_parse():
    """Verify command line parser works correctly"""
    output_file = 'output'
    nox_file = 'noxfile'
    disabled_output = '--disabled_output pylint,pytest'.split(' ')
    enabled_output = '--enabled_output pylint'.split(' ')
    rem_args = '-v --test_args -flag'.split(' ')
    args = ['lint', '--output_file', output_file, '--nox_file', nox_file] + \
        enabled_output + disabled_output + rem_args
    linter = Linter()
    with patch.object(sys, 'argv', args):
        linter._parse_args()
    args = linter._args
    assert args.output_file == output_file
    assert args.nox_file == nox_file
    assert args.rem == rem_args
    # enabled overrides disabled, so only pylint should run
    for pkg in ('pytest', 'mypy', 'flake8'):
        assert pkg in args.disabled_output
