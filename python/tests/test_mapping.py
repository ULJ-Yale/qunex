from .utils import get_test_data_path
from general.parser import (
    read_generic_session_file,
    read_hcp_session_file,
    read_mapping_file,
    _parse_session_file_lines,
)
from general.utilities import (
    _reserved_bold_numbers,
    _process_pipeline_hcp_mapping,
    _serialize_session,
)
from general.exceptions import CommandError
import pytest


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
    expected = _load_expected_mapping("session2_se_hcp.txt")
    print("\n".join(lines))
    assert result == expected


def test_mapping_missing_se2():
    """Mapping with se images that do not form a pair"""
    _, lines = _run_mapping_test("session2_se2.txt", "mapping2.txt")
    result = _parse_session_file_lines(lines, "pipeline:hcp")
    expected = _load_expected_mapping("session2_se2_hcp.txt")
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
    expected = _load_expected_mapping("session3_fm_ge_hcp.txt")
    print("\n".join(lines))
    assert result == expected


def test_mapping_mix_se_fm():
    """Mapping with mixed SE and FM"""
    _, lines = _run_mapping_test("session4.txt", "mapping4.txt")
    result = _parse_session_file_lines(lines, "pipeline:hcp")
    expected = _load_expected_mapping("session4_hcp.txt")
    print("\n".join(lines))
    assert result == expected


def test_mapping_bids():
    """Mapping bids

    import bids produces image number with leading zeros
    """
    _, lines = _run_mapping_test("session1.txt", "mapping1.txt")
    result = _parse_session_file_lines(lines, "pipeline:hcp")
    expected = _load_expected_mapping("session1_hcp.txt")
    print("\n".join(lines))
    assert result == expected


def test_get_bold_numbers_in_mapping_file():
    """Get all the bold numbers used in a mapping file

    Bold numbers explicitly used in bold_num tags are considered
    reserved and will be skipped when assign bold numbers
    sequentially
    """

    mapping_file = get_test_data_path("mapping_boldnum1.txt")
    m = read_mapping_file(mapping_file)
    assert _reserved_bold_numbers(m) == set([5, 6])


def test_get_bold_numbers_in_mapping_file2():
    """Get all the bold numbers used in a mapping file

    Bold numbers explicitly used in bold_num tags are considered
    reserved and will be skipped when assign bold numbers
    sequentially
    """

    mapping_file = get_test_data_path("mapping_boldnum2.txt")
    m = read_mapping_file(mapping_file)
    assert _reserved_bold_numbers(m) == set([6, 7])


def test_mapping_bold_num1():
    """Mapping bold number

    When bold_num is defined in the mapping file, the mapping should respect the tag
    when assigning bold number
    """
    _, lines = _run_mapping_test("session1_boldnum1.txt", "mapping_boldnum1.txt")
    result = _parse_session_file_lines(lines, "pipeline:hcp")
    expected = _load_expected_mapping("session1_boldnum1_hcp.txt")
    print("\n".join(lines))
    assert result == expected

    _, lines = _run_mapping_test("session2_boldnum1.txt", "mapping_boldnum1.txt")
    result = _parse_session_file_lines(lines, "pipeline:hcp")
    expected = _load_expected_mapping("session2_boldnum1_hcp.txt")
    print("\n".join(lines))
    assert result == expected

    _, lines = _run_mapping_test("session3_boldnum1.txt", "mapping_boldnum1.txt")
    result = _parse_session_file_lines(lines, "pipeline:hcp")
    expected = _load_expected_mapping("session3_boldnum1_hcp.txt")
    print("\n".join(lines))
    assert result == expected


def test_mapping_bold_num2():
    """Mapping bold number

    When bold_num is defined in the mapping file, the mapping should respect the tag
    when assigning bold number, bold_num for boldrefs overwrites its designated
    number
    """
    _, lines = _run_mapping_test("session1_boldnum2.txt", "mapping_boldnum2.txt")
    result = _parse_session_file_lines(lines, "pipeline:hcp")
    expected = _load_expected_mapping("session1_boldnum2_hcp.txt")
    print("\n".join(lines))
    assert result == expected

    _, lines = _run_mapping_test("session2_boldnum2.txt", "mapping_boldnum2.txt")
    result = _parse_session_file_lines(lines, "pipeline:hcp")
    expected = _load_expected_mapping("session2_boldnum2_hcp.txt")
    print("\n".join(lines))
    assert result == expected

    _, lines = _run_mapping_test("session3_boldnum2.txt", "mapping_boldnum2.txt")
    result = _parse_session_file_lines(lines, "pipeline:hcp")
    expected = _load_expected_mapping("session3_boldnum2_hcp.txt")
    print("\n".join(lines))
    assert result == expected


def test_mapping_bold_num6():
    """Mapping bold number

    A torough test of bold_num mapping based on real world BIDS data.
    """
    _, lines = _run_mapping_test("session6.txt", "mapping6.txt")
    result = _parse_session_file_lines(lines, "pipeline:hcp")
    expected = _load_expected_mapping("session6_hcp.txt")
    print("\n".join(lines))
    assert result == expected


def test_mapping_manual_se_fm():
    """Honor manually assigned spin-echo and field-map numbers

    When se/fm is defined in the session / mapping file, the mapping should respect the tag
    when assigning bold number
    """
    _, lines = _run_mapping_test("session_manual1.txt", "mapping_manual_se1.txt")
    result = _parse_session_file_lines(lines, "pipeline:hcp")
    expected = _load_expected_mapping("session_manual1_hcp1.txt")
    print("\n".join(lines))
    assert result == expected

    _, lines = _run_mapping_test("session_manual1.txt", "mapping_manual_se2.txt")
    result = _parse_session_file_lines(lines, "pipeline:hcp")
    expected = _load_expected_mapping("session_manual1_hcp2.txt")
    print("\n".join(lines))
    assert result == expected

    with pytest.raises(CommandError) as exc_info:
        _run_mapping_test("session_manual1.txt", "mapping_manual_se3_err.txt")
    print(exc_info.value.args)

    # se defined in session file, so we will not run auto assign for other spin-echo images.
    _, lines = _run_mapping_test("session_manual2.txt", "mapping_manual_se4.txt")
    result = _parse_session_file_lines(lines, "pipeline:hcp")
    expected = _load_expected_mapping("session_manual2_hcp4.txt")
    print("\n".join(lines))
    assert result == expected

    # This mapping file expects se images to be auto-assigned and uses them.
    with pytest.raises(CommandError) as exc_info:
        _run_mapping_test("session_manual2.txt", "mapping_manual_se1.txt")
    print(exc_info.value.args)
