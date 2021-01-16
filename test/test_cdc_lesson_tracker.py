# To be run like this:
#   python3 -m pytest -v test/test_rpi_ac_control.py
#   python3 -m pytest -k 'test_run_shell_cmd' -v test/test_rpi_ac_control.py

import pytest
import os
import re
from test_utils.io import *
from test_utils.systemd import *
from test_utils.shell import *

systemd_service = "cdc-lesson-tracker.service"


def test_systemd_service_enabled_running():
    assert is_service_enabled(systemd_service)
    assert is_service_running(systemd_service)

