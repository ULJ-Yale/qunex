#!/usr/bin/env python3
# encoding: utf-8

"""
Extracts docstrings from unsupported languages to files named ``<language>.py`` in the python/qx_utilities folder.

Warning:
    Only qx_utilities commands in bash and R can currently be used with this script.
"""

import re
import sys
import os

# import headings from docs/conf.py
sys.path.insert(0, "../..")

from conf import napoleon_custom_sections
from importlib.util import spec_from_loader, module_from_spec
from importlib.machinery import SourceFileLoader

# paths
sys.path.insert(0, "../../../python")
sys.path.insert(0, "../../../python/qx_utilities")

# this code imports python/qx_utilities/gmri to use all_qunex_commands list
spec = spec_from_loader("gmri", SourceFileLoader("gmri", "../../../python/qx_utilities/gmri"))
gmri = module_from_spec(spec)
spec.loader.exec_module(gmri)


def docstring_to_parameters(docstring, headings):
    """
    Extracts parameters to be included in Python function definition - def().

    Warning:
        This function is currently hardcoded not to include parameters from
        `Specific parameters` section. This can easily be adjusted in the code.
    """

    headings_string = "|".join(headings)

    sections = {}

    parameters = []

    sections["parameters"] = re.findall(r'(?i)(Parameters:[\s\S]*?(?:\n\n(?:' + headings_string + r'):|\Z))', docstring)
    sections["specific_parameters"] = re.findall(r'(?i)(Specific parameters:[\s\S]*?(?:\n\n(?:' + headings_string + r'):|\Z))', docstring)

    for heading, section in sections.items():
        if sections[heading]:
            # parameters_section is list
            sections[heading] = sections[heading][0]
            if sections[heading] is tuple:
                sections[heading] = sections[heading][0]

    for heading, section in sections.items():
        if section:
            # "if" below hardcoded to only include parameters from the "Parameters" section
            # remove "if" to include Specific parameters
            if heading == "parameters":
                for result in re.findall("\n {4}--(\w+).*?(default .*)?\):", section):
                    parameter = result[0]
                    if result[1] not in ['', "default detailed below"]:
                        parameter += f'={result[1].strip("default ")}'
                        parameters.append((parameter, True))
                    else:
                        parameters.append((parameter, False))

    # sort parameters - False first
    parameters.sort(key = lambda x: x[1])

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
        # if there is at least one command per language
        if len(commands) > 0:
            # hardcoded module description
            output_dict[lang] = ['#!/usr/bin/env python\n# encoding: utf-8\n\n"""\nThis file consists of docstrings from ' + lang + ' commands.\n"""\n\n\n']
            for command in commands:
                command_split = command.split(".")
                function_name = command_split[-1]
                file_path = os.path.abspath("../../../" + lang + "/" + command_split[0] + "/" + "/".join(command_split[2:]))
                if lang == "bash":
                    file_path += ".sh"
                elif lang == "r":
                    file_path += ".R"

                with open(file_path, "r") as file:
                    if lang == "bash":
                        docstring = re.findall("usage\(\) \{\n *cat << EOF\n([\s\S]*?)\nEOF", file.read())[0]
                    elif lang == "r":
                        docstring = re.findall("\n# {3}``" + function_name + "``\n(?:#.*\n)+", file.read())[0]
                        docstring = re.sub("(\n# {3}|\n#)", "\n", docstring)

                    # add function name, parameters, indentation and comment docstring
                    parameters = docstring_to_parameters(docstring, all_headings)
                    docstring = "    " + "\n    ".join(docstring.split("\n"))
                    docstring = f'def {function_name}({", ".join(parameters)}):\n    """\n{docstring}    """\n\n\n'

                    output_dict[lang].append(docstring)
    return output_dict


def write_python_files(docstring_dict):
    for lang, lines in docstring_dict.items():
        if len(lines) > 0:
            output_file_path = "../../../python/qx_utilities/" + lang + ".py"
            # join strings and write file to python/qx_utilities directory
            with open(output_file_path, "w") as output_file:
                output_file.write("".join(lines).strip())


if __name__ == "__main__":
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