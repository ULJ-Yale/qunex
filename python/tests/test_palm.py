import getpass
import os
import shutil
import tempfile
from datetime import datetime

import pytest

from qx_utilities.general.palm import run_palm

from .utils import get_test_data_path

# run_palm shells out to palm and wb_command and reads the HCP templates under
# QUNEXPATH, none of which exist outside a QuNex install, so skip rather than
# fail there (this is what keeps the test out of the way on a CI runner)
_missing = [
    name
    for name in ("palm", "wb_command")
    if shutil.which(name) is None
]
if "QUNEXPATH" not in os.environ:
    _missing.append("QUNEXPATH")

requires_palm = pytest.mark.skipif(
    bool(_missing),
    reason=f"run_palm needs {', '.join(_missing)}",
)


@requires_palm
def test_run_palm():
    """Test run_palm"""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    temp_dir = os.path.join(tempfile.gettempdir(), f'fc_tests_{getpass.getuser()}', timestamp)

    run_palm(
        image=get_test_data_path("gbc_diff.dscalar.nii"),
        design="name:zero",
        palm_args="n:5|C:3.1|zstat",
        root=f"{temp_dir}/C/gbc_diff",
        cleanup="No"
    )

    assert os.path.exists(os.path.join(temp_dir, "C", "gbc_diff_R_elapsed.csv"))
    assert os.path.exists(os.path.join(temp_dir, "C", "gbc_diff_volume_elapsed.csv"))
    assert os.path.exists(os.path.join(temp_dir, "C", "gbc_diff_L_elapsed.csv"))

    run_palm(
        image=get_test_data_path("gbc_diff.dscalar.nii"),
        design="name:zero",
        palm_args="n:5|zstat",
        root=f"{temp_dir}/gbc_diff",
        cleanup="No"
    )

    assert os.path.exists(os.path.join(temp_dir, "gbc_diff_elapsed.csv"))