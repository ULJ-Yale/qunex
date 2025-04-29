import os
import tempfile
from datetime import datetime

from general.palm import run_palm

from .utils import get_test_data_path


def test_run_palm():
    """Test run_palm"""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    temp_dir = os.path.join(tempfile.gettempdir(), 'fc_tests', timestamp)

    run_palm(
        image=get_test_data_path("gbc_diff.dscalar.nii"),
        design="name:zero",
        palm_args="n:5|zstat",
        root=f"{temp_dir}/gbc_diff"
    )

    assert os.path.exists(os.path.join(temp_dir, "gbc_diff_R_elapsed.csv"))
    assert os.path.exists(os.path.join(temp_dir, "gbc_diff_volume_elapsed.csv"))
    assert os.path.exists(os.path.join(temp_dir, "gbc_diff_L_elapsed.csv"))
