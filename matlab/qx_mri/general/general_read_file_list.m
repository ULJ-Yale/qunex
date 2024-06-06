function [list] = general_read_file_list(flist, sessions, check, verbose)

%``general_read_file_list(flist, sessions, check, verbose)``
%
%   Reads a list of files and returns a structure with file information.
%
%   Parameters:
%       --flist (string or structure array):
%           A path to the list file, a well structured string, or a sessions
%           structure array.
%       --sessions (str, default 'all'):
%           A comma separated list of sessions to retain in the returned 
%           sessions structure array. 'all' retaines all the sessions.
%       --check (str, default ''):
%           A comma separated list of elements that each session has to
%           have or a warning is reported.
%       --verbose (boolean, default false):
%           Whether to report on progress.
%
%   Output:
%       list
%           A structure with the following fields
%           - session
%               A structure array with information:
%               - id      ... session id
%               - roi     ... path to a session ROI file
%               - glm     ... path to a session glm file
%               - fidl    ... path to a session fidl file
%               - files   ... cell array of file paths
%               - folder  ... sessions root folder
%           - nsessions
%               number of sessions in the list
%           - nfiles
%               number of all files in the list
%           - listname
%               the name of the list file or the listname specified in the string
%           - missing
%               structure with information on missing data, with fields:       
%               - fields     ... a list of missing fields
%               - sessions   ... a vector specifying whether a session has any 
%                                missing data
%               - sessionids ... a list of missing session ids
%
%   Notes:
%       The function reads the file list and returns a structure array with the
%       information on each session. It is also possible to pass the list in 
%       the input string itself. In this case, it has to start with 
%       'listname:<name>' and all the regular lines of the list file can then be
%       passed with pipe ('|') instead of newline. Example::
%
%           'listname:wmlist|session id:OP483|file:bold1.nii.gz|roi:aseg.nii.gz'
%
%   Examples:
%
%       [sessions, nsessions] = general_read_file_list('scz.list', 'all', [], true);
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 4 || isempty(verbose),   verbose = false; end
if nargin < 3,                         check = []; end
if nargin < 2 || isempty(sessions), sessions = 'all'; end
if nargin < 1 || isempty(flist)
    error('general_read_file_list: flist parameter missing!');
end

if ~isempty(check)
    check = strtrim(regexp(check, ',', 'split'));
end

if ~isempty(sessions)
    sessions = strtrim(regexp(sessions, ',', 'split'));
end

if verbose, fprintf('\n ... reading file list: '); end
if verbose
    report = 'full';
else
    report = 'error';
end

% ---> create structure from file or string

if ischar(flist)

    if any(strfind(flist, '|')) && (any(strfind(flist, 'subject id:')) || any(strfind(flist, 'session id:')))
        if starts_with(flist, 'listname:')
            files = regexp(flist, '\|', 'split');
            list.listname = strtrim(regexp(files{1}, ':', 'split'));
            list.listname = list.listname{2};
            files = files(2:end);
        else
            error('ERROR in general_read_file_list. It seems that a file list string description is provided, but it does not start with ''listname:''. Please check your command call!');
        end
    else
        general_check_file(flist, 'list file', 'errorstop', '');
        [lpath, list.listname, lext] = fileparts(flist);
        files = {};
        infile = fopen(flist);
        while feof(infile) == 0
            files{end+1} = fgetl(infile);
        end
    end

    nsessions = 0;    
    nf        = -9;
    

    for s = files(:)'
        s = strtrim(s{1});
        % -- replace 'subject id' with 'session id'
        s = strrep(s, 'subject id:', 'session id:');
        if length(s) > 0 && s(1) == '#'
            continue
        end
        if ~isempty(strfind(s, 'session id:'))
            nsessions = nsessions + 1;
            nf  = 0;
            [t, s] = strtok(s, ':');
            list.session(nsessions).id = strtrim(s(2:end));
            continue
        end
        if nf < 0
            continue
        elseif ~isempty(strfind(s, 'roi:'))
            [t, s] = strtok(s, ':');
            list.session(nsessions).roi = strtrim(s(2:end));
        elseif ~isempty(strfind(s, 'file:'))
            [t, s] = strtok(s, ':');
            nf = nf + 1;
            list.session(nsessions).files{nf} = strtrim(s(2:end));
        elseif ~isempty(strfind(s, 'conc:'))
            [t, s] = strtok(s, ':');
            list.session(nsessions).conc = strtrim(s(2:end));
        elseif ~isempty(strfind(s, 'fidl:'))
            [t, s] = strtok(s, ':');
            slist.ession(nsessions).fidl = strtrim(s(2:end));
        elseif ~isempty(strfind(s, 'glm:'))
            [t, s] = strtok(s, ':');
            list.session(nsessions).glm = strtrim(s(2:end));
        elseif ~isempty(strfind(s, 'folder:'))
            [t, s] = strtok(s, ':');
            list.session(nsessions).folder = strtrim(s(2:end));
        end
    end
elseif isstruct(flist)
    list      = flist;
    nsessions = length(list.session);
else
    error('ERROR: unknown input to general_read_file_list! The flist parameter is neither a string nor a struct. Please check your call!');
end

% ---> check structure

prepend   = '       ... ';
nfiles    = 0;
fields    = {'roi', 'conc', 'fidl', 'glm', 'folder'};
names     = {'ROI image', 'conc file', 'fidl file', 'GLM file', 'folder'};
f2name    = containers.Map(fields, names);

for s = 1:nsessions
    if verbose, fprintf('\n     - session id: %s\n', list.session(s).id); end

    % -- check other fields

    for field = fields
        field = field{1};
        if isfield(list.session(s), field) && ~isempty(list.session(s).(field))
            if ~general_check_file(list.session(s).(field), f2name(field), report, prepend);
                list.session(s).(field) = '';
            end
        end
    end

    % -- check files

    if isfield(list.session(s), 'files') && ~isempty(list.session(s).files)
        keep = logical([]);
        for n = 1:length(list.session(s).files)
            keep = [keep general_check_file(list.session(s).files{n}, 'image file', report, prepend)];
        end
        list.session(s).files = list.session(s).files(keep);
        nfiles = nfiles + sum(keep);
    end
end

% -- additional checks
if nsessions == 0
    fprintf('\n\nERROR: No session id information present in list file: %s! Please check file format!\n\n', flist);
    error('ERROR: Could not read the provided filelist.');
end

% -- prepare missing data information
list.missing.sessionids = {};

% -- filter sessions
sessionids = {list.session.id};
if ~ismember('all', sessions)
    list.session = list.session(ismember(sessionids, sessions));
    nsessions = length(list.session);
    list.missing.sessionids = setdiff(sessions, sessionids);
end

if nsessions == 0
    fprintf('\n\nWARNING: None of the requested sessionids were present in list file: %s! Please check your list file!\n\n', flist);
end

% -- check data
list.missing.fields   = {};
list.missing.sessions = zeros(1, nsessions);

if ~isempty(check)    
    for s = 1:nsessions
        for c = check
            c = c{1};
            if ~isfield(list.session(s), c) || isempty(list.session(s).(c))
                if isempty(list.missing.fields)
                    fprintf('\n\nWARNING: Some sessions in the list are missing required information.\n\n');
                end
                fprintf('       - session %s is missing %s field\n', list.session(s).id, c);
                if ~ismember({c}, list.missing.fields)
                    list.missing.fields{end + 1} = c;
                end
                list.missing.sessions(s) = 1;
            end
        end
    end
end

list.nsessions = nsessions;
if isfield(list.session, 'files')
    list.nfiles = length([list.session.files]);
else
    list.nfiles = 0;
end

if verbose, fprintf('\n ... done'); end
