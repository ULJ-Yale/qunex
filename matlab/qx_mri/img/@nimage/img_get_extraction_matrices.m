function [exsets] = img_get_extraction_matrices(obj, frames, options)

%function [exsets] = img_get_extraction_matrices(obj, frames, options)
%
%   Generates a set of matrices for extraction of data, one matrix for each specified
%   extraction sets, one line for each event to be extracted, coding for each point in
%   the timeseries the frames to be extracted (1) vs. those to be left (0).
%
%   INPUT
%   =====
%
%   obj       - Image object to create matrices for
%   frames    - The definition of which frames to extract, specifically:
%               ->  a numeric array mask defining which frames to use (1) and which not (0), or 
%               ->  a single number, specifying the number of frames to skip at the start of each bold, or
%               ->  a string describing which events to extract timeseries for, and the frame offset from 
%                   the start and end of the event in format: 
%                   '<fidlfile>|<extraction name>:<event list>:<extraction start>:<extraction end>') 
%                   where:
%                   -> fidlfile         ... is a path to the fidle file that defines the events    
%                   -> extraction name  ... is the name for the specific extraction definition    
%                   -> event list       ... is a comma separated list of events for which data is to be extracted    
%                   -> extraction start ... is a frame number relative to event start or end when the extraction should start    
%                   -> extraction end   ... is a frame number relative to event start or end when the extraction should start    
%                      the extraction start and end should be given as '<s|e><frame number>'. E.g.:
%                       s0  ... the frame of the event onset 
%                       s2  ... the third frame of the event
%                       e0  ... the frame at the start of which the event ended
%                       e1  ... the second frame after the event end 
%                       e-1 ... the frame at the end of which the event ended
%
%                      | s0 | s1 | s2   ...   e-2 | e-1 | e0 | e1
%                      |<- event start  ... event end ->|
%
%                      example:
%                       '<fidlfile>|encoding:e-color,e-shape:s2:s2|delay:d-color,d-shape:s2:e0'
%                       This example will extract two timeseries. The first timeseries will be named encoding, it will 
%                       take the third frame following the onset of events e-color and e-shape. The second timeseries
%                       will be named delay and will include all the frames from the third frame following the event 
%                       onset to the first frame following the event end of the d-color or d-shape events.
%
%                       encoding: | 0 0 1 0 0 ...
%                                 |<- e-color or e-shape event onset
%
%                       delay:    | 0 0 1 1 1 ..................... 1 | 1 0 0 
%                                 |<- d-color or d-shape event onset  |<- d-color or d-shape event end
%
%   options   - A string specifying additional analysis options formated as pipe separated pairs of colon separated
%               key, value pairs: "<key>:<value>|<key>:<value>"
%               It takes the following keys and values:
%               -> ignore    ... a comma separated list of information to identify frames to ignore, options are:
%                                -> use      ... ignore frames as marked in the use field of the bold file
%                                -> fidl     ... ignore frames as marked in .fidl file (only available with event extraction)
%                                -> <column> ... the column name in *_scrub.txt file that matches bold file to be used for ignore mask
%                                ['use, fidl']
%               -> badevents ... what to do with events that have frames marked as bad, options are:
%                                -> use      ... use any frames that are not marked as bad
%                                -> <number> ... use the frames that are not marked as bad if at least <number> ok frames exist
%                                -> ignore   ... if any frame is marked as bad, ignore the full event
%                                ['use']
%               -> verbose   ... Whether to be verbose 'true' or not 'false', when running the analysis ['false']
%
%   RESULTS
%   =======
%
%   exsets    - A numbered structure with fields:
%               -> title   ... title of the computed extraction
%               -> exdef   ... definition of extraction
%               -> exmat   ... extraction matrix for each event occurence
%               -> eind    ... event indeces for each retained row
%               -> estat   ... statistics (number of good trials) for each event
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 3 options = ''; end
if nargin < 2 error('ERROR: Events string has to be specified!'); end

% ----- parse options

default = 'ignore=use,fidl|badevents=use|verbose=false|debug=false';
options = general_parse_options([], options, default);

verbose = strcmp(options.verbose, 'true');
printdebug = strcmp(options.debug, 'true');

if printdebug
    general_print_struct(options, 'img_get_extraction_matrices options used');
end

% ---> creating use mask

toignore  = strtrim(regexp(options.ignore, ',', 'split'));
useframes = ones(1, length(obj.use));
fignore   = false;

for ti = toignore
    if ismember('use', ti)
        useframes = obj.use & useframes;
    elseif ismember('fidl', ti)
        fignore = true;
    else 
        useScrub = find(ismember(obj.scrub_hdr, ti));
        if isempty(useScrub)
            error('ERROR: The specified ignore field (%s) is not valid!', ti{1});
        end
        useframes = useframes & obj.scrub(:, useScrub)' == 0;
    end
end

obj.use = useframes;

% ----- prepare run info

nruns = length(obj.runframes);
runid = ones(1, obj.frames);
runlimits = [1 obj.runframes(1)];
for n = 2:nruns
    runlimits(n,:) = [runlimits(n-1,2) + 1, runlimits(n-1,2) + obj.runframes(n)];
    runid(runlimits(n,1):runlimits(n,2)) = n;
end

tstemplate = zeros(1, obj.frames);


% ----- extracting based on numeric data

if isnumeric(frames)
    if length(frames) == 1
        exmat = ones(1, obj.frames);
        if frames > 0
            for n = 1:nruns
                exmat(runlimits(n,1):runlimits(n,1)+frames) = 0;
            end
        end
    elseif length(frames) > 1
        if length(frames) ~= obj.frames
            error('ERROR: The length of the extraction matrix [%s] does not match the number of image frames!', length(frames), obj.frames);
        end
        exmat = frames;
    else
        exmat = ones(1, obj.frames);
    end

    % mask out frames to ignore
    exmat(obj.use ~= 1) = 0;

    exsets.title = 'timeseries';
    exsets.exdef = frames;
    exsets.exmat = exmat;
    exsets.eind  = [1];
    exsets.estat = sum(exmat,2);
    return
end

% ----- extracting based on events

% ----- check data

[fidlfile, exlist] = strtok(frames, '|');
exlist = exlist(2:end);
exlist = strtrim(regexp(exlist, '\|', 'split'));
nexlists = length(exlist);

go = general_check_file(fidlfile, 'fidlfile', 'error');

if ~go
    error('ERROR: Fidl file was not found. Please check the path!\n\n');
end

if ~isnumeric(options.badevents)
    if ~ismember(options.badevents, {'use', 'ignore'})
        [options.badevents, ok] = str2num(options.badevents);
        if ~ok
            error('ERROR: badevents option is neither a number nor a valid option [%s]!\n\n', options.badevents);
        end
    end
end

% ----- get fidl event list

elist = general_read_event_file(fidlfile);

% ----- take out frames to ignore based on fidl

if fignore
    ignoreidx = find(elist.event == -1);
    for idx = ignoreidx
        if elist.frame(idx) <= obj.frames
            if elist.frame(idx) + elist.elength(idx) > obj.frames
                obj.use(elist.frame(idx):end) = 0;
            else
                obj.use(elist.frame(idx):elist.frame(idx)+elist.elength(idx)) = 0;
            end
        end
    end
end

% ----- prepare extraction matrices

c = 0;
for n = 1:nexlists

    % ---> extract the definition

    exdef = strtrim(regexp(exlist{n}, ':', 'split'));
    if length(exdef) ~= 4
        fprintf('WARNING: event extraction definition [%s] does not match the correct format. Skipping.\n', exlist{n});
        continue
    end
    
    c = c + 1;
    exsets(c).exdef = exlist{n};
    exsets(c).title = exdef{1};

    eventset = strtrim(regexp(exdef{2}, ',', 'split'));
    startref = exdef{3}(1);
    [startoff, oks] = str2num(exdef{3}(2:end));
    endref = exdef{4}(1);
    [endoff, oke] = str2num(exdef{4}(2:end));

    ok = true;
    if ~all(ismember({startref, endref}, {'s', 'e'})); ok = false; end
    ok = ok & oks & oke;
    if ~ok
        fprintf('ERROR: start or end extraction definition [%s] does not match the correct format. Skipping.\n', exlist{n});
        continue
    end

    % ---> create matrices

    exmat = [];

    for e = 1:length(eventset)
        eventcode    = find(ismember(elist.events, eventset(e))) -1;
        eventidx     = ismember(elist.event, eventcode);
        eventstarts  = elist.frame(eventidx);
        eventlengths = elist.elength(eventidx);
        nexevents    = sum(eventidx);

        % if verbose; fprintf('... -> eventcodes %s -> eventids %s -> nevents %s\n', num2str(eventcode), num2str(eventidx), num2str(nexevents)); end
        
        if startref == 's'
            exstarts = eventstarts + startoff;
        else
            exstarts = eventstarts + eventlengths + startoff;
        end

        if endref == 's'
            exends = eventstarts + endoff;
        else
            exends = eventstarts + eventlengths + endoff;
        end            

        for x = 1:nexevents
            exline = tstemplate;

            % ---> check that we are not outside of timeseries bounds
            if exstarts(x) < 1 | exends(x) > obj.frames
                continue
            end

            % ---> create extraction mask
            exline(exstarts(x):exends(x)) = 1;

            % ---> check that the extraction mask is in the same run as the event
            eventrun = runid(eventstarts(x));
            exrun    = unique(runid(exline == 1));
            if length(exrun) == 1 && exrun == eventrun
                exmat = [exmat; exline];
            end
        end
    end

    % ---> check for bad frames

    if isnumeric(options.badevents)
        minok = options.badevents;
    else
        minok = 1;
    end

    % fprintf('-> obj.use size %s\n', num2str(size(obj.use)));
    % fprintf('-> exmat size %s\n', num2str(size(exmat)));

    eind  = [1:size(exmat,1)]';
    
    if isnumeric(options.badevents) || strcmp(options.badevents, 'use')
        exmat  = bsxfun(@times, exmat, obj.use);
        estat  = sum(exmat, 2);
        okrows = estat >= minok;
    elseif strcmp(options.badevents, 'ignore')
        estat  = sum(bsxfun(@times, exmat, obj.use), 2);
        ignore = ~obj.use;
        okrows = sum(bsxfun(@and, exmat, ignore), 2) == 0;
    end

    exsets(c).exmat = exmat(okrows, :);
    exsets(c).eind  = eind(okrows);
    exsets(c).estat = estat;
end