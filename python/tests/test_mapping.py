from .utils import get_test_data_path
from general.parser import (
    read_generic_session_file,
    read_hcp_session_file,
    read_mapping_file,
    _parse_session_file_lines,
)
from general.utilities import _process_pipeline_hcp_mapping, _serialize_session


def _run_mapping_test(sf, mf):
    """Helper function performs mapping based on session and mapping file name

    Returns:
        t: object mapping result
        lines: serialized version of the mapping result
               without temporary rule information
    """
    session_file = get_test_data_path(sf)
    mapping_file = get_test_data_path(mf)

    m = read_mapping_file(mapping_file)
    s = read_generic_session_file(session_file)
    t = _process_pipeline_hcp_mapping(s, m)
    lines = _serialize_session(t)

    return t, lines


def _load_expected_mapping(sf):
    """Loads expected mapping result"""
    session_hcp_file = get_test_data_path(sf)
    return read_hcp_session_file(session_hcp_file)


def test_normal_mapping():
    """Normal mapping"""
    _, lines = _run_mapping_test("session2.txt", "mapping2.txt")
    result = _parse_session_file_lines(lines, "pipeline:hcp")
    expected = _load_expected_mapping("session2_hcp.txt")
    print("\n".join(lines))
    assert result == expected


def test_mapping_missing_se1():
    """Mapping with se images that do not form a pair"""
    _, lines = _run_mapping_test("session2_se.txt", "mapping2.txt")
    result = _parse_session_file_lines(lines, "pipeline:hcp")
    expected = _load_expected_mapping("session2_hcp_se.txt")
    print("\n".join(lines))
    assert result == expected


def test_mapping_missing_se2():
    """Mapping with se images that do not form a pair"""
    _, lines = _run_mapping_test("session2_se2.txt", "mapping2.txt")
    result = _parse_session_file_lines(lines, "pipeline:hcp")
    expected = _load_expected_mapping("session2_hcp_se2.txt")
    print("\n".join(lines))
    assert result == expected


def test_mapping_fm():
    """Mapping with fm images that do not form a pair"""
    _, lines = _run_mapping_test("session3.txt", "mapping3.txt")
    result = _parse_session_file_lines(lines, "pipeline:hcp")
    expected = _load_expected_mapping("session3_hcp.txt")
    print("\n".join(lines))
    assert result == expected


def test_mapping_mix_ge_fm():
    """FM-Phase FM-Magnitude pair interrupted by FM-GE (FSM specific)"""
    _, lines = _run_mapping_test("session3_fm_ge.txt", "mapping3.txt")
    result = _parse_session_file_lines(lines, "pipeline:hcp")
    expected = _load_expected_mapping("session3_hcp_fm_ge.txt")
    print("\n".join(lines))
    assert result == expected


def test_mapping_mix_se_fm():
    """Mapping with mixed SE and FM"""
    _, lines = _run_mapping_test("session4.txt", "mapping4.txt")
    result = _parse_session_file_lines(lines, "pipeline:hcp")
    expected = _load_expected_mapping("session4_hcp.txt")
    print("\n".join(lines))
    assert result == expected
