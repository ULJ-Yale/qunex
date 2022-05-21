from .utils import get_test_data_path
from general.parser import read_generic_session_file, read_hcp_session_file, read_mapping_file

def test_read_generic_session_file():
    filename = get_test_data_path("session1.txt")
    sess = read_generic_session_file(filename)
    assert sess["id"] == "12345_1"
    assert sess["subject"] == "12345"
    assert len(sess["paths"]) == 3
    assert "bids" in sess["paths"]
    assert len(sess["pipeline_ready"]) == 0
    assert len(sess["images"]) == 2


def test_read_generic_session_file_complex():
    filename = get_test_data_path("session2.txt")
    sess = read_generic_session_file(filename)
    assert sess["id"] == "HCPA001"
    assert sess["subject"] == "HCPA001"
    assert len(sess["paths"]) == 4
    assert "dicom" in sess["paths"]
    assert len(sess["pipeline_ready"]) == 0
    assert len(sess["images"]) == 49


def test_read_hcp_session_file():
    filename = get_test_data_path("session2_hcp.txt")
    sess = read_hcp_session_file(filename)
    assert sess["id"] == "HCPA001"
    assert sess["subject"] == "HCPA001"
    assert len(sess["paths"]) == 4
    assert "dicom" in sess["paths"]
    assert len(sess["pipeline_ready"]) == 1
    assert len(sess["images"]) == 49
    assert "se" in sess["images"][(71,)]
    assert sess["images"][(71,)]["hcp_image_type"] == ("SE-FM", "AP")
    assert "se" in sess["images"][(131,)]
    assert sess["images"][(131,)]["hcp_image_type"] == ("bold", 2, "rest")


def test_read_mapping_file():
    filename = get_test_data_path("mapping2.txt")
    rules = read_mapping_file(filename)
    assert len(rules["group_rules"]["image_number"]) == 2
    assert len(rules["group_rules"]["name"]) == 10