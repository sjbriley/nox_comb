import nox

@nox.session
def flake8(session):
    session.install('flake8')
    session.run(
        'flake8', 'src/nox_comb',
        '--config', 'nox.ini',
        '--output-file', 'flake8_report.txt')

@nox.session
def pylint(session):
    session.install('pylint')
    session.run(
        'pylint', 'src/nox_comb',
        '--rcfile', 'nox.ini',
        '--output', 'pylint_report')

@nox.session
def mypy(session):
    session.install('mypy')
    session.run(
        'mypy', 'src/nox_comb',
        '--config-file', 'nox.ini',)

@nox.session
def pytest(session):
    session.install('pytest', 'pytest-cov', '.')
    session.run(
        'pytest',
        '--cov-config=.coveragerc',
        '--cov-report', 'html',
        '--cov-report', 'xml',
        '--cov=nox_comb',
        '--cov-fail-under=15')
