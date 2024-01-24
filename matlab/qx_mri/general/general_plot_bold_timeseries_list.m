function [] = general_plot_bold_timeseries_list(flist, elements, filename, skip, fformat, verbose)

%``general_plot_bold_timeseries_list(flist, elements, filename, skip, fformat, verbose)``
%
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

%  ---- initializing

if nargin < 6 || isempty(verbose), verbose = false; end
if nargin < 5 || isempty(fformat), fformat = 'pdf'; end
if nargin < 4 || isempty(skip), skip = 0; end
if nargin < 3 || isempty(filename), filename = ''; end
if nargin < 2 || isempty(elements), elements = 'type=stats|stats>type=dvarsme,img=1>type=fd,img=1;type=image|name=V|mask=1;type=image|name=WM|mask=1;type=image|name=GM|mask=1;type=image|name=V|mask=1|img=2|use=1|scale=2;type=image|name=GM|mask=1|img=2|use=1|scale=4'; end
if nargin < 1, error('ERROR: Please specify at least file list!'); end


%  ---- Check and load list

if verbose, fprintf('\n\nChecking ...\n'); end
general_check_file(flist, 'image file list', 'error');

list = general_read_file_list(flist);

for n = 1:list.nsessions
    if verbose, fprintf('\n ---> processing %s', list.session(n).id); end

    [tpath tfile] = fileparts(list.session(n).files{1});
    tfile = regexp(tfile, '(^.*?)[._]', 'tokens');
    tfile = tfile{1};
    tfile = tfile{1};
    tfile = [tpath filesep 'movement' filesep filename tfile '_tsplot.' fformat];

    imgfiles = strjoin(list.session(n).files, ';');
    maskfiles = list.session(n).roi;

    general_plot_bold_timeseries(imgfiles, elements, maskfiles, tfile, skip, list.session(n).id, false);
end

if verbose, fprintf('\n ===> DONE\n'); end

function [s] = strjoin(c, d)
    s = [];
    for n = 1:length(c)
        s = [s c{n}];
        if n < length(c)
            s = [s d];
        end
    end
