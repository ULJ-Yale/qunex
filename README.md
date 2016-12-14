Background
==========

Mind & Brain Lab Neuroimaging Utilities, i.e. niutilities are neuroimaging
preprocessing and analysis utilities that support multiple tasks through a
common user interface, designed to simplify multiple steps of neuroimaging
data preprocessing and analysis from sorting of dicom files to second level
statistical analysis. They often provide a wrapper for efficiently running
other tools and software either on a single computer or computer cluster
by using PBS or LSF scheduling.

The utilities make use of and assume that relevant information and data
is provided in a number of file formats, further described below. The utilities
assume and help maintain a specific folder structure, further described below.
A number of utilities depend on external dependencies and make use of data and
data templates provided in a separate library.

The utilities can be used as a self standing toolset, they were, however,
developed to efficiently integrate with a set of Matlab functions, methods and
utilities, and a modified version of HCP (Human Connectome Project)
preprocessing tools. They are best utilized as a part MNAP (Multimodal
Neuroimaging Analysis Pipeline).

The utilites are developed and maintained by Grega Repovš, [Mind and Brain
Lab], University of Ljubljana in collaboration with the [Anticevic Lab], Yale
University.


Usage and command documentation
===============================

The utilities are used through the `gmri` command. The general use form is:

`gmri <command> [option=value] [option=value] ...`

The list of commands and their specific documentation is provided throug `gmri`
command itself using the folowing options:

* `gmri -h` prints general help information,
* `gmri -l` lists all the available commands,
* `gmri -<command>` prints specific help for the specified command.

Perusing documentation, please note the following conventions used:

* Square brackets `[]` denote an option or argument that is optional the
  value listed in the brackets is the default value used if the argument
  is not explicitly specified
* Angle brackets `<>` describe the value that should be provided
* Dashes or "flags" (`-`) in the documentation define input variables.
* Commands, arguments, and option names are either in small or "camel" case.
* Use descriptions are in regular "sentence" case.
* Option values are usually specified in capital case (e.g. `YES`, `NONE`).



External dependencies
=====================


File formats
============




[Mind and Brain Lab]: http://mblab.si
[Anticevic Lab]: http://anticeviclab.yale.edu
