function [version] = general_get_qunex_version()

%``function [] = general_get_qunex_version()``
%
%   Function for retrieving qunex version.
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

% read environment variables
tools = getenv('TOOLS');
qunexrepo = getenv('QUNEXREPO');

% create the path to version file
version_file = strcat(tools, '/', qunexrepo, '/VERSION.md');

% read the version file
fid = fopen(version_file);
version = fgetl(fid);
fclose(fid);
