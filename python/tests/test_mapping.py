import pytest
from general.exceptions import CommandError, SpecFileSyntaxError
from general.parser import (
    _parse_session_file_lines,
    read_generic_session_file,
    read_hcp_session_file,
    read_mapping_file,
)
from general.utilities import (
    _match_or_rule,
    _process_pipeline_hcp_mapping,
    _reserved_bold_numbers,
    _serialize_session,
    _simple_glob_match,
)

from .utils import get_test_data_path


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


def test_glob_match_patterns():
    """Test the _simple_glob_match function with various patterns"""
    # Test exact match
    assert _simple_glob_match("T1w", "T1w") == True
    assert _simple_glob_match("T1w", "T2w") == False

    # Test * at the beginning
    assert _simple_glob_match("rfMRI_REST_AP", "*_AP") == True
    assert _simple_glob_match("rfMRI_REST_PA", "*_AP") == False
    assert _simple_glob_match("BOLD_Task", "*BOLD_Task") == True

    # Test * at the end
    assert _simple_glob_match("rfMRI_REST_AP", "rfMRI_*") == True
    assert _simple_glob_match("rfMRI_REST_AP_SBRef", "rfMRI_*") == True
    assert _simple_glob_match("tfMRI_REST_AP", "rfMRI_*") == False

    # Test * in the middle
    assert _simple_glob_match("rfMRI_REST_AP", "rfMRI_*_AP") == True
    assert _simple_glob_match("rfMRI_TASK_AP", "rfMRI_*_AP") == True
    assert _simple_glob_match("rfMRI_REST_PA", "rfMRI_*_AP") == False

    # Test multiple *
    assert _simple_glob_match("rfMRI_REST_AP_SBRef", "rfMRI_*_AP_*") == True
    assert _simple_glob_match("rfMRI_TASK_AP_Run1", "rfMRI_*_AP_*") == True
    assert _simple_glob_match("rfMRI_REST_PA_SBRef", "rfMRI_*_AP_*") == False

    # Test * at both ends
    assert _simple_glob_match("prefix_middle_suffix", "*middle*") == True
    assert _simple_glob_match("just_middle", "*middle*") == True
    assert _simple_glob_match("no_match", "*middle*") == False


def test_mapping_glob_basic():
    """Test glob-based mapping with simple patterns"""
    _, lines = _run_mapping_test("session_glob1.txt", "mapping_glob1.txt")
    result = _parse_session_file_lines(lines, "pipeline:hcp")
    expected = _load_expected_mapping("session_glob1_hcp.txt")
    print("\n".join(lines))
    assert result == expected


def test_mapping_glob_priority():
    """Test that exact name matches take priority over glob patterns"""
    _, lines = _run_mapping_test("session_glob2.txt", "mapping_glob2.txt")
    result = _parse_session_file_lines(lines, "pipeline:hcp")
    expected = _load_expected_mapping("session_glob2_hcp.txt")
    print("\n".join(lines))
    assert result == expected


def test_mapping_glob_conflict():
    """Test that conflicting glob patterns raise an error"""
    with pytest.raises(SpecFileSyntaxError) as exc_info:
        _run_mapping_test("session_glob3.txt", "mapping_glob3.txt")

    error_msg = str(exc_info.value.error)
    print(error_msg)
    assert "conflicting" in error_msg.lower()
    assert "rfMRI_REST_AP_SBRef" in error_msg


def test_mapping_phenc_in_source_and_rule_agree():
    """phenc defined in both source and mapping with the same value is allowed.

    once the source session file carries auto-detected phenc tags, a mapping
    rule repeating the same phenc must not be treated as a conflict.
    """
    t, _ = _run_mapping_test("session_phenc_dup.txt", "mapping_phenc_dup.txt")
    images = t["images"]
    # image 04 (boldref) and 05 (bold) both define phenc(AP) on both sides
    assert images[(4,)]["phenc"] == "AP"
    assert images[(5,)]["phenc"] == "AP"


def test_mapping_phenc_in_source_and_rule_conflict():
    """phenc defined in both source and mapping with different values errors."""
    with pytest.raises(SpecFileSyntaxError) as exc_info:
        _run_mapping_test("session_phenc_dup.txt", "mapping_phenc_conflict.txt")

    error_msg = str(exc_info.value.error)
    print(error_msg)
    assert "phenc" in error_msg.lower()
    assert "AP" in error_msg and "PA" in error_msg


# ---- "or" rule tests (|| variants) ----


def test_mapping_or_first_variant():
    """When the first variant exists, it is used."""
    _, lines = _run_mapping_test("session_or1.txt", "mapping_or1.txt")
    result = _parse_session_file_lines(lines, "pipeline:hcp")
    expected = _load_expected_mapping("session_or1_hcp.txt")
    print("\n".join(lines))
    assert result == expected


def test_mapping_or_fallback_variant():
    """When the first variant is missing, the second is used."""
    _, lines = _run_mapping_test("session_or2.txt", "mapping_or1.txt")
    result = _parse_session_file_lines(lines, "pipeline:hcp")
    expected = _load_expected_mapping("session_or2_hcp.txt")
    print("\n".join(lines))
    assert result == expected


def test_mapping_or_no_match():
    """When none of the variants exist, no rule is applied."""
    _, lines = _run_mapping_test("session_or3.txt", "mapping_or1.txt")
    result = _parse_session_file_lines(lines, "pipeline:hcp")
    expected = _load_expected_mapping("session_or3_hcp.txt")
    print("\n".join(lines))
    assert result == expected


def test_mapping_or_glob_variants():
    """Or-rules with glob patterns: second glob variant matches."""
    _, lines = _run_mapping_test("session_or4.txt", "mapping_or2.txt")
    result = _parse_session_file_lines(lines, "pipeline:hcp")
    expected = _load_expected_mapping("session_or4_hcp.txt")
    print("\n".join(lines))
    assert result == expected


def test_or_rule_parsing():
    """Verify that the parser stores or-rules correctly."""
    mapping_file = get_test_data_path("mapping_or1.txt")
    m = read_mapping_file(mapping_file)

    or_rules = m["group_rules"]["or"]
    assert len(or_rules) == 2

    # first or-rule: T1w_HiRes || T1w_LowRes => T1w
    assert or_rules[0]["variants"] == ["T1w_HiRes", "T1w_LowRes"]
    assert or_rules[0]["rule"]["hcp_image_type"] == ("T1w",)

    # second or-rule: T2w_HiRes || T2w_LowRes => T2w
    assert or_rules[1]["variants"] == ["T2w_HiRes", "T2w_LowRes"]
    assert or_rules[1]["rule"]["hcp_image_type"] == ("T2w",)

    # regular rules should not be affected
    assert "SpinEchoFieldMap_AP" in m["group_rules"]["name"]
    assert len(m["group_rules"]["or"]) == 2


def test_or_rule_parsing_with_globs():
    """Verify that or-rules with glob patterns are parsed correctly."""
    mapping_file = get_test_data_path("mapping_or2.txt")
    m = read_mapping_file(mapping_file)

    or_rules = m["group_rules"]["or"]
    assert len(or_rules) == 1
    assert or_rules[0]["variants"] == ["rfMRI_REST1*", "rfMRI_REST2*", "tfMRI*"]
    assert or_rules[0]["rule"]["hcp_image_type"] == ("bold", None, "rest")


def test_match_or_rule_exact_name():
    """_match_or_rule matches exact-name variants per image."""
    or_rules = [
        {"variants": ["T1w_HiRes", "T1w_LowRes"], "rule": {"hcp_image_type": ("T1w",)}},
    ]
    # first variant matches
    assert _match_or_rule("T1w_HiRes", or_rules) == {"hcp_image_type": ("T1w",)}
    # second variant matches
    assert _match_or_rule("T1w_LowRes", or_rules) == {"hcp_image_type": ("T1w",)}
    # neither matches
    assert _match_or_rule("SomethingElse", or_rules) is None


def test_match_or_rule_glob():
    """_match_or_rule handles glob-pattern variants per image."""
    or_rules = [
        {
            "variants": ["rfMRI_REST1*", "rfMRI_REST2*"],
            "rule": {"hcp_image_type": ("bold", None, "rest")},
        },
    ]
    # first glob matches
    assert _match_or_rule("rfMRI_REST1_AP", or_rules) == {
        "hcp_image_type": ("bold", None, "rest")
    }
    # second glob matches
    assert _match_or_rule("rfMRI_REST2_AP", or_rules) == {
        "hcp_image_type": ("bold", None, "rest")
    }
    # no match
    assert _match_or_rule("tfMRI_WM_AP", or_rules) is None


def test_match_or_rule_priority():
    """Earlier variants take priority for the same image name."""
    rule_a = {"hcp_image_type": ("T1w",), "additional_tags": []}
    rule_b = {"hcp_image_type": ("T2w",), "additional_tags": []}
    or_rules = [
        {"variants": ["T1w*", "T1w_LowRes"], "rule": rule_a},
        {"variants": ["T1w_LowRes"], "rule": rule_b},
    ]
    # first or-rule's first alt matches via glob
    assert _match_or_rule("T1w_LowRes", or_rules) is rule_a


def test_or_rule_parser_rejects_empty_variant():
    """Parser should reject or-rules with an empty variant."""
    from general.parser import _parse_mapping_file_lines

    with pytest.raises(SpecFileSyntaxError):
        _parse_mapping_file_lines(["T1w_HiRes ||  => T1w"])

    with pytest.raises(SpecFileSyntaxError):
        _parse_mapping_file_lines([" || T1w_LowRes => T1w"])
