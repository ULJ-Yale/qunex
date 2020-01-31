function [exsets] = mri_GetExtractionMatrices(obj, exlist, options)

%function [exsets] = mri_GetExtractionMatrices(obj, exlist, options)
%
%   Generates a set of matrices for extraction of data, one matrix for each specified
%   extraction sets, one line for each event to be extracted, coding for each point in
%   the timeseries the frames to be extracted (1) vs. those to be left (0).
%
%   INPUT
%   =====
%
%   obj       - Image object to create matrices for
%   exlist    - The definition of which events to use, specifically:
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
%                       s2  ... the second frame from the event onset 
%                       e1  ... the first frame from the event end 
%                       e0  ... the last frame of the event 
%                       e-2 ... the two frames before the event end
%                      example:
%                       '<fidlfile>|encoding:e-color,e-shape:s2:s2|delay:d-color,d-shape:s2:e0'
%   options   - A string specifying additional analysis options formated as pipe separated pairs of colon separated
%               key, value pairs: "<key>:<value>|<key>:<value>"
%               It takes the following keys and values:
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
%
%   ---
%   Written by Grega Repovš 2020-01-31.
%
%   Changelog

if nargin < 3 options = ''; end
if nargin < 2 error('ERROR: Events string has to be specified!'); end

% ----- parse options

default = 'badevents=use|verbose=false';
options = g_ParseOptions([], options, default);

verbose = strcmp(options.verbose, 'true')

% ----- check data

[fidlfile, exlist] = strtok(exlist, '|');
exlist = exlist(2:end);
exlist = strtrim(regexp(exlist, '\|', 'split'));
nexlists = length(exlist);

go = g_CheckFile(fidlfile, 'fidlfile', 'error');

if ~go
    error('ERROR: Fidl file was not found. Please check the path!\n\n');
end

if ~isnumeric(options.badevents)
    if ~ismember(options.badevents, {'use', 'ignore'}
        [options.badevents, ok] = str2num(options.badevents);
        if ~ok
            error('ERROR: badevents option is neither a number of a valid option [%s]!\n\n', options.badevents);
        end
    end
end

% ----- get fidl event list

elist = g_ReadEventFile(fidlf);

% ----- prepare run info

nruns = length(obj.runframes);
runid = ones(1, obj.frames);
runlimits = [1 obj.runframes(1)];
for n = 2:nruns
    runlimits(n,:) = [runlimits(n-1,2) + 1, runlimits(n-1,2) + obj.runframes(n)];
    runid(runlimits(n,1):runlimits(n,2)) = n;
end

tstemplate = zeros(1, obj.frames);

% ----- prepare extraction matrices

for n = 1:nexlists

    % --> extract the definition

    exdef = strtrim(regexp(exlist{n}, ':', 'split'));
    if length(exdef) ~= 4
        fprintf('WARNING: event extraction definition [%s] does not match the correct format. Skipping.\n', exlist{n});
        continue
    end
    
    exsets(n).exdef = exlist{n};
    exsets(n).title = exdef{1};

    eventset = strtrim(regexp(exdef{2}, ',', 'split'));
    startref = exdef{3}(1);
    [startoff, oks] = str2nun(exdef{3}(2:));
    endref = exdef{4}(1);
    [endoff, oke] = str2nun(exdef{4}(2:));

    ok = true;
    if ~all(ismember{startref, endref}, {'s', 'e'}); ok = false; end
    ok = ok & oks & oke;
    if ~ok
        fprintf('ERROR: start or end extraction definition [%s] does not match the correct format. Skipping.\n', exlist{n});
        continue
    end

    % --> create matrices

    exmat = [];

    for e = 1:length(eventset)
        eventcode    = find(ismember(elist.events, eventset(e)));
        eventidx     = ismember(elist.event, eventcode);
        eventstarts  = elist.frame(evendidx);
        eventlengths = elist.elength(eventidx);
        nexevents    = length(eventidx);
        
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

            % --> check that we are not outside of timeseries bounds
            if exstarts(x) < 1 | exends(x) > obj.frames
                continue
            end

            % --> create extraction mask
            exline(exstarts(x):exends(x)) = 1;

            % --> check that the extraction mask is in the same run as the event
            eventrun = runid(eventstarts(x));
            exrun    = unique(runid(exline == 1));
            if length(exrun) == 1 && exrun == eventrun
                exmat = [exmat; exline];
            end
        end
    end

    % --> check for bad frames

    if isnumeric(options.badevents)
        minok = options.badevents;
    else
        minok = 1;
    end

    if isnumeric(options.badevents) || strcmp(options.badevents, 'use')
        exmat   = bsxfun(@times, exmat, obj.use);
        okrows  = sum(exmat, 2) >= minok;
    elseif strcmp(options.badevents, 'ignore')
        ignore  = ~obj.use;
        okrows  = sum(bsxfun(@and, exmat, ignore)) == 0;
    end
            
    exsets(n).exmat = exmat(okrows);
end
