from .utils import get_test_data_path
from general.parser import read_generic_session_file, read_hcp_session_file, read_mapping_file, _parse_session_file_lines
from general.utilities import _process_pipeline_mapping, _serialize_session


def _run_mapping_test(sf, mf):
    session_file = get_test_data_path(sf)
    mapping_file = get_test_data_path(mf)

    m = read_mapping_file(mapping_file)
    s = read_generic_session_file(session_file)
    t = _process_pipeline_mapping(s, m)
    lines = _serialize_session(t)
    
    return t, lines

def _load_expected_mapping(sf):
    session_hcp_file = get_test_data_path(sf)
    return read_hcp_session_file(session_hcp_file)
    
def test_normal_mapping():
    _, lines = _run_mapping_test("session2.txt", "mapping2.txt")
    result = _parse_session_file_lines(lines, "pipeline:hcp")
    expected = _load_expected_mapping("session2_hcp.txt")
    assert result == expected


def test_mapping_extra_se():
    _, lines = _run_mapping_test("session2_se.txt", "mapping2.txt")
    result = _parse_session_file_lines(lines, "pipeline:hcp")
    expected = _load_expected_mapping("session2_hcp_se.txt")
    assert result == expected

def test_mapping_missing_se():
    _, lines = _run_mapping_test("session2_se2.txt", "mapping2.txt")
    result = _parse_session_file_lines(lines, "pipeline:hcp")
    expected = _load_expected_mapping("session2_hcp_se2.txt")
    assert result == expected

def test_mapping_fm():
    _, lines = _run_mapping_test("session3.txt", "mapping3.txt")
    result = _parse_session_file_lines(lines, "pipeline:hcp")
    expected = _load_expected_mapping("session3_hcp.txt")
    print("\n".join(lines))
    assert result == expected