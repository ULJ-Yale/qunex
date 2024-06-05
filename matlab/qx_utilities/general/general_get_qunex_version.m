function [version] = general_get_qunex_version()

%``general_get_qunex_version()``
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
fid = fopen(version_file, 'r');
if fid == -1
    version = 'unknown';
else
    version = fgetl(fid);
    fclose(fid);
end

