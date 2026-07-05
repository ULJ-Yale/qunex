#!/usr/bin/env python
# encoding: utf-8

import os
import sys

# Add the parent directory to the path to import qx_registry
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, parent_dir)
sys.path.insert(0, os.path.join(parent_dir, 'qx_utilities'))

from pathlib import Path

import qx_registry_build


def test_index_bash_commands_from_usage_heredoc(tmp_path: Path):
    """Index a bash command documented via usage() heredoc."""

    bash_root = tmp_path / "bash"
    bash_root.mkdir(parents=True, exist_ok=True)

    script = bash_root / "mycmd.sh"
    script.write_text(
        """#!/usr/bin/env bash

usage() {
    cat << EOF
``mycmd``

Short description line.

..  qx_command:
    type: utility
    aliases: mycmd_alias
    language: bash

Parameters:
    --foo (str, default 'bar'):
        Foo option.

EOF
    exit 0
}

if [[ $1 == "--help" ]]; then
    usage
fi
""",
        encoding="utf-8",
    )

    cmds = qx_registry_build.index_bash_commands(bash_root, source_id="core")
    assert len(cmds) == 1

    c = cmds[0]
    assert c.name == "mycmd"
    assert c.language == "bash"
    assert c.type == "utility"
    assert c.path == "mycmd.sh"
    assert c.aliases == ("mycmd_alias",)

    assert c.args == tuple()
    assert len(c.options) == 1
    assert c.options[0].name == "foo"
    assert c.options[0].type == "str"
    assert c.options[0].default == "bar"
    assert c.options[0].description == "Foo option."
