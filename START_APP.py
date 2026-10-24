"""Open in Spyder, VS Code, PyCharm, IDLE, or run: python START_APP.py.

Reuses the interpreter that executes this script. Never downloads or installs Python.
Creates an isolated app environment and installs only the project's packages.
"""
from pathlib import Path
import subprocess
import sys
import venv

ROOT = Path(__file__).resolve().parent
RUNTIME = ROOT / '.runtime'
CODE = ROOT / 'Python_Code'
DEPENDENCIES = CODE / 'requirements.txt'


def main():
    print('=' * 64)
    print('Ga2O3 TRANSIENT THERMAL LAB  |  RafaelDaSquidman')
    print('Existing Python detected:', sys.executable)
    print('=' * 64)
    if sys.version_info < (3, 11):
        print('Python 3.11 or later is required. Change your IDE interpreter.')
        return 2

    dest = RUNTIME / ('Scripts/python.exe' if sys.platform == 'win32' else 'bin/python')
    if not dest.exists():
        print('Creating isolated environment using this existing Python interpreter...')
        try:
            venv.create(RUNTIME, system_site_packages=True, with_pip=True)
        except Exception as exc:
            print('Could not create private environment:', exc)
            print('If Spyder already has all required libraries, the app can instead be run from its terminal:')
            print(f'"{sys.executable}" -m streamlit run "{CODE / "app.py"}"')
            return 3
    if not dest.exists():
        print('The virtual environment did not create a Python executable.')
        return 3

    # Only use pip when a needed import is missing from the private/system site-packages.
    libraries = 'import numpy, scipy, pandas, plotly, streamlit'
    probe = subprocess.run([str(dest), '-c',libraries], cwd=ROOT,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,check=False)
    if probe.returncode:
        print('Installing missing project libraries (internet access may be needed)...')
        result = subprocess.run([str(dest), '-m','pip','install','-r',str(DEPENDENCIES)],cwd=ROOT,check=False)
        if result.returncode:
            print('\nDependency installation failed. Check internet access and available disk space.')
            print('No Python interpreter was installed or modified by this launcher.')
            return result.returncode
    print('\nOpening the Streamlit application at http://127.0.0.1:8501')
    print('Leave this process running; Ctrl+C stops the app.')
    try:
        return subprocess.call([str(dest),'-m','streamlit','run',str(CODE/'app.py'),
                                '--server.address','127.0.0.1'],cwd=ROOT)
    except KeyboardInterrupt:
        return 0

if __name__ == '__main__':
    raise SystemExit(main())
