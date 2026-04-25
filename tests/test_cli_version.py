import subprocess
import sys

from omniglyph import __version__


def test_cli_version_outputs_package_version():
    result = subprocess.run(
        [sys.executable, "-m", "omniglyph.cli", "--version"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert result.stdout.strip() == f"omniglyph {__version__}"
