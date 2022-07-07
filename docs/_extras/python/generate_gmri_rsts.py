#!/usr/bin/env python3
# encoding: utf-8

"""
Automatically generates .rst files in docs/api/gmri directory.
"""

import sys
from importlib.util import spec_from_loader, module_from_spec
from importlib.machinery import SourceFileLoader

# this code imports python/qx_utilities/gmri to use all_qunex_commands list
sys.path.insert(0, "../../../python/qx_utilities")
spec = spec_from_loader("gmri", SourceFileLoader("gmri", "../../../python/qx_utilities/gmri"))
gmri = module_from_spec(spec)
spec.loader.exec_module(gmri)

if __name__ == "__main__":
    directory_path = "../../api/gmri"

    for full_name, description, language in gmri.all_qunex_commands:
        function_name = full_name.split(".")[-1]
        file_content = f'{function_name}\n{"=" * len(function_name)}\n\n'
        if language.lower() in ["python", "bash", "r"]:
            file_content += f'.. autofunction:: {full_name}\n'
        elif language == "matlab":
            file_content += f'.. mat:autofunction:: {full_name}\n'
        else:
            raise Exception("Language " + language + " is not supported.")

        with open(directory_path + f'/{function_name}.rst', "w") as output_file:
            output_file.write(file_content)
