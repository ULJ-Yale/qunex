#!/usr/bin/env python3
# encoding: utf-8

"""
Extracts docstrings from files in unsupported languages (Bash and R) to files
named ``<language>.py`` in subdirectories of the $QUNEX_PATH/python/ folder.
"""

import re
import sys
import os

sys.path.append("../..")  # for $QUNEXPATH/docs/conf.py import
sys.path.append("../../../python")

from conf import napoleon_custom_sections
from importlib.util import spec_from_loader, module_from_spec
from importlib.machinery import SourceFileLoader

# this code imports python/qx_utilities/gmri to use all_qunex_commands list
spec = spec_from_loader("gmri", SourceFileLoader("gmri", "../../../python/qx_utilities/gmri"))
gmri = module_from_spec(spec)
spec.loader.exec_module(gmri)


def docstring_to_parameters(docstring, headings):
    """
    Extracts parameters to be included in Python function definition.
    """

    headings_string = "|".join(headings)

    sections = {}

    parameters = []

    sections["parameters"] = re.findall(r'(?i)(Parameters:[\s\S]*?(?:\n\n(?:' + headings_string + r'):|\Z))', docstring)

    for heading, section in sections.items():
        if sections[heading]:
            # parameters_section is list
            sections[heading] = sections[heading][0]
            if sections[heading] is tuple:
                sections[heading] = sections[heading][0]

    for heading, section in sections.items():
        if section:
            for result in re.findall("\n {4}--(\w+).*?(default .*)?\):", section):
                parameter = result[0]
                if result[1] not in ['', "default detailed below"]:
                    stripped = re.sub("^default ", "", result[1])
                    if stripped.lower() == "true":
                        stripped = "True"
                    elif stripped.lower() == "false":
                        stripped = "False"
                    parameter += f'={stripped}'
                    parameters.append((parameter, True))
                else:
                    parameters.append((parameter, False))

    # sort parameters - False first
    parameters.sort(key=lambda x: x[1])

    return [parameter for parameter, has_default_value in parameters]


def generate_heading_list():
    """
    Generate a list of all headings allowed by Sphinx Napoleon extension (as currently configured).
    """
    headings = [
        "args",
        "arguments",
        "attention",
        "attributes",
        "caution",
        "danger",
        "error",
        "example",
        "examples",
        "hint",
        "important",
        "keyword args",
        "keyword arguments",
        "methods",
        "note",
        "notes",
        "other parameters",
        "parameters",
        "return",
        "returns",
        "raise",
        "raises",
        "references",
        "see also",
        "tip",
        "todo",
        "warning",
        "warnings",
        "warn",
        "warns",
        "yield",
        "yields"
    ]
    # add custom headings from conf.py
    for heading in napoleon_custom_sections:
        if type(heading) is tuple:
            headings.append(heading[0])
        elif type(heading) is str:
            headings.append(heading)
    return headings


def extract_docstrings(input_dict):
    all_headings = generate_heading_list()

    output_dict = {}
    for lang, commands in input_dict.items():
        if len(commands) > 0:
            output_dict[lang] = {}
            for command in commands:
                command_split = command.split(".")
                function_name = command_split[-1]
                module_path = "/".join(command_split[:-2])
                # if there is at least one command per language
                source_file_path = os.path.abspath("../../../" + lang + "/" + module_path + "/" + function_name)
                if lang == "bash":
                    source_file_path += ".sh"
                elif lang == "r":
                    source_file_path += ".R"

                with open(source_file_path, "r") as file:
                    if lang == "bash":
                        docstring = re.findall("usage\(\) \{\n *cat << EOF\n([\s\S]*?)\nEOF", file.read())[0]
                    elif lang == "r":
                        docstring = re.findall("\n# {3}``" + function_name + "``\n(?:#.*\n)+", file.read())[0]
                        docstring = re.sub("(\n# {3}|\n#)", "\n", docstring)

                    # add function name, parameters, indentation and comment docstring
                    parameters = docstring_to_parameters(docstring, all_headings)
                    docstring = "    " + "\n    ".join(docstring.split("\n"))
                    docstring = f'def {function_name}({", ".join(parameters)}):\n    """\n{docstring}    """\n\n\n'

                    if not module_path in output_dict[lang]:
                        output_dict[lang][module_path] = []
                    output_dict[lang][module_path].append(docstring)
    return output_dict


def write_python_files(docstring_dict):
    for lang, inner_dict in docstring_dict.items():
        for module_path, functions in inner_dict.items():
            if len(functions) > 0:
                module_path = os.path.join("..", "..", "..", "python", module_path)
                os.makedirs(module_path, exist_ok=True)
                # create empty file __init__.py if it doesn't exist to mark
                # the directory as a module
                if not os.path.isfile(os.path.join(module_path, "__init__.py")):
                    with open(os.path.join(module_path, "__init__.py"), 'w'):
                        pass
                output_file_path = os.path.join(module_path, lang + ".py")
                with open(output_file_path, "w") as output_file:
                    # hardcoded module description
                    output_file.write('#!/usr/bin/env python\n'
                                      '# encoding: utf-8\n\n'
                                      '"""\n'
                                      'This file consists of docstrings extracted from functions in' + lang + '.\n'
                                                                                                              '"""\n\n\n')
                    output_file.write("".join(functions).strip())


if __name__ == "__main__":
    print("==> Generating Python-like docstrings from unsupported (bash and R) commands")
    unsupported_languages = [
        "bash",
        "r",
    ]

    unsupported_commands = {}
    for language in unsupported_languages:
        unsupported_commands[language] = []
    for full_name, description, language in gmri.all_qunex_commands:
        if language in unsupported_languages:
            unsupported_commands[language].append(full_name)

    docstrings = extract_docstrings(unsupported_commands)

    write_python_files(docstrings)
