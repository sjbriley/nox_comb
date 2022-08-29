"""Command line wrapper for nox to combine linter output
"""

import argparse
import pathlib
import subprocess
import re
import logging
import string
import random
import os
from collections import defaultdict
from typing import Tuple
import sys


class Linter:
    """Wrapper for nox to combine linter output
    """
    PYLINT_PAT = r"""['"]pylint['"],[^)]*['"]--output['"],\s{0,3}['"](\S*)['"]"""
    FLAKE8_PAT = r"""['"]flake8['"],[^)]*['"]--output-file['"],\s{0,3}['"](\S*)['"]"""
    ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', re.VERBOSE)
    ALL_PARSERS = ['pylint', 'flake8', 'pytest', 'mypy']

    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self._temp_files = defaultdict(list)
        self._logger.setLevel(logging.DEBUG)
        self._args: argparse.Namespace
        self._parse_args()

    def run_nox(self) -> None:
        """Executes nox with modified file output, and compiles
        all output from linters into one file.

        Raises:
            FileNotFoundError: If nox file cannot be found
        """

        nox_file = pathlib.Path(self._args.nox_file)
        if not nox_file.exists():
            raise FileNotFoundError(f"Nox file does not exist at {str(nox_file)}")
        with open(nox_file, 'r') as open_file:
            contents = open_file.read()
        temp_nox = self._generate_temp_nox(contents)
        self._logger.debug('Generated temp nox file at %s', str(temp_nox))
        try:
            pytest_output, mypy_output = self._run_nox(temp_nox)
            self._combine_output(pytest_output, mypy_output)
        finally:
            temp_nox.unlink()
            for file in self._temp_files:
                for temp_file in self._temp_files[file]:
                    try:
                        temp_file[1].unlink()
                    except:
                        continue

    def _parse_args(self) -> None:
        """Parses all user arguments into self._args
        """
        parser = argparse.ArgumentParser()
        parser.add_argument(
            '--nox_file', type=str, default='noxfile.py', dest='nox_file',
            help='location of nox file')
        parser.add_argument(
            '--output_file', type=str, default='lint_report', dest='output_file',
            help='Output file to write report to')
        parser.add_argument(
            '--disabled_output', default='', type=str, dest='disabled_output',
            help='Ignore reporting for specific packages')
        parser.add_argument(
            '--enabled_output', default='', type=str, dest='enabled_output',
            help='Enable reporting for specific packages, overrides disabled_output')
        parser.add_argument('args', nargs='*')
        self._args, self._args.rem = parser.parse_known_args()
        self._args.disabled_output = [
            linter.lower() for linter in self._args.disabled_output.split(',')]
        self._args.enabled_output = [
            linter.lower() for linter in self._args.enabled_output.split(',')]
        if '' in self._args.enabled_output:
            self._args.enabled_output.remove('')
        if self._args.enabled_output != []:
            self._args.disabled_output = self.ALL_PARSERS
            for opt in self._args.enabled_output:
                if opt in self._args.disabled_output:
                    self._args.disabled_output.remove(opt)
        self._logger.debug('Args are %s', str(self._args))

    def _generate_temp_nox(self, contents: str) -> pathlib.Path:
        """Generates a temporary nox file with modified output contents.

        Args:
            contents (str): Contents of original nox file

        Returns:
            pathlib.Path: path to temporary nox file
        """
        if 'pylint' in contents.lower():
            if 'pylint' in self._args.disabled_output:
                self._logger.debug('Not including pylint into combined output, skipping...')
            else:
                contents = self._find_output(contents, self.PYLINT_PAT, 'pylint')
        if 'flake8' in contents.lower():
            if 'flake8' in self._args.disabled_output:
                self._logger.debug('Not including flake8 into combined output, skipping...')
            else:
                contents = self._find_output(contents, self.FLAKE8_PAT, 'flake8')

        temp_nox = pathlib.Path('.temp_nox.py')
        with open(temp_nox, 'w') as write_file:
            write_file.write(contents)
        return temp_nox

    def _run_nox(self, temp_nox: pathlib.Path) -> Tuple[bytes, bytes]:
        """Executes nox with subprocess.Popen

        Args:
            temp_nox (pathlib.Path): path to temporary nox file to be executed

        Returns:
            Tuple(bytes, bytes): contents of pytest output and mypy output
        """
        rem = ' '.join(self._args.rem)
        cmd = f'nox -f {temp_nox} --forcecolor {rem}'.split(' ')
        if '' in cmd:
            cmd.remove('')
        self._logger.debug('Executing cmd %s', str(cmd))
        with subprocess.Popen(
                cmd,
                executable=sys.executable.replace('python.exe', 'nox.exe'),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                cwd=os.getcwd()) as process:
            try:
                pytest_output = b''
                mypy_output = b''
                pytest = False
                mypy = False
                while True:
                    line = process.stdout.readline()  # type: ignore
                    if 'pytest' not in self._args.disabled_output:
                        pytest_output, pytest = self._process_pytest(line, pytest_output, pytest)
                    if 'mypy' not in self._args.disabled_output:
                        mypy_output, mypy = self._process_mypy(line, mypy_output, mypy)
                    if not line:
                        break
                    print(line.decode('utf-8').replace('\n',''))
                stdout, stderr = process.communicate()
                self._logger.debug(stdout)
                self._logger.debug(stderr)
            except:
                self._logger.debug('Exception occured during subprocess', exc_info=True)
                raise
        return pytest_output, mypy_output

    def _combine_output(self, pytest_output: bytes, mypy_output: bytes) -> None:
        """Combines output from all linters into user specified output file

        Args:
            pytest_output (bytes): contents from pytest
            mypy_output (bytes): contents from mypy
        """
        contents: bytes = b''
        for text in (['pytest', pytest_output], ['mypy', mypy_output]):
            if text[1] != b'':
                # get rid of color
                text[1] = self.ANSI_ESCAPE.sub('', text[1].decode('utf-8'))  # type: ignore
                contents += f'{"#"*30} {text[0]}\n\n'.encode('utf-8')
                contents += f'{text[1]}'.encode('utf-8')
                contents += b'\n\n'
        for key in self._temp_files:
            for temp_file in self._temp_files[key]:
                try:
                    with open(temp_file[1], 'rb') as read_file:
                        contents += f'{"#"*30} {temp_file[0]}\n\n'.encode('utf-8')
                        contents += read_file.read()
                except:
                    self._logger.debug(
                        'Could not write contents from file %s', str(temp_file[1]),
                        exc_info=True)
        with open(self._args.output_file, 'wb') as write_file:
            write_file.write(contents)
        self._logger.info('Wrote contents to %s', self._args.output_file)

    def _find_output(self, contents: str, pattern: str, name: str) -> str:
        """Searches contents of nox file for output file for all linters

        Args:
            contents (str): of nox file
            pattern (str): pattern specific to linters for output file specification
            name (str): name of linter

        Returns:
            str: modified contents with temporary output file specified
        """
        result = re.search(pattern, contents)
        if result is None or len(contents) < 2:
            self._logger.debug('Could not find output file for %s', name)
            return contents
        out_file = result[1]
        self._logger.debug('Found output file %s for %s', out_file, name)
        ran_str = ''.join(random.choices(string.ascii_letters, k=10))
        temp_file = pathlib.Path('.nox')
        temp_file.mkdir(exist_ok=True)
        temp_file = temp_file / f'{out_file}_temp_{ran_str}'
        self._logger.debug('Generated temp file %s for %s', str(temp_file), name)
        self._temp_files[out_file].append((name, temp_file))
        contents = contents.replace(result[1], str(temp_file).replace('\\', '/'))
        return contents

    def _process_pytest(
            self, line: bytes, pytest_output: bytes, pytest: bool) -> Tuple[bytes, bool]:
        """Processes stdout lines for pytest output

        Args:
            line (bytes): stdout bytes
            pytest_output (bytes): pytest recorded output
            pytest (bool): True if recording pytest outout

        Returns:
            Tuple[bytes, bool]: pytest_output, pytest
        """
        if 'pytest' in line.decode('utf-8') and pytest_output == b'':
            pytest = True
        if pytest is True:
            out = self.ANSI_ESCAPE.sub('', line.decode('utf-8').lower())
            if 'nox > command pytest' in out:
                pytest = False
            pytest_output += line
        return pytest_output, pytest

    def _process_mypy(self, line: bytes, mypy_output: bytes, mypy: bool) -> Tuple[bytes, bool]:
        """Processes stdout lines for mypy output

        Args:
            line (bytes): stdout bytes
            mypy_output (bytes): mypy recorded output
            mypy (bool): True if recording mypy outout

        Returns:
            Tuple[bytes, bool]: mypy_output, mypy
        """
        if 'mypy' in line.decode('utf-8') and mypy_output == b'':
            mypy = True
        if mypy is True:
            out = self.ANSI_ESCAPE.sub('', line.decode('utf-8').lower())
            if 'nox > command mypy' in out:
                mypy = False
            mypy_output += line
        return mypy_output, mypy


def main():
    """main"""
    Linter().run_nox()


if __name__ == "__main__":
    main()
