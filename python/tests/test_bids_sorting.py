from .utils import get_test_data_path
import json
from general.bids import _sort_bids_images
import ast


def test_bids_sorting_bold_sbref():
    """Test if bold and sbref images are sorted in the correct order"""
    bids_f = get_test_data_path("../../qx_utilities/templates/import_bids.txt")
    orig_f = get_test_data_path("bids_bold_sbref.json")
    ans_f = get_test_data_path("bids_bold_sbref_sorted.json")

    with open(bids_f) as f:
        bids = ast.literal_eval(f.read())

    with open(orig_f) as f:
        bidsData = json.load(f)

    with open(ans_f) as f:
        bidsData_ans = json.load(f)

    _sort_bids_images(bidsData, bids)
    print(json.dumps(bidsData))
    assert bidsData == bidsData_ans
