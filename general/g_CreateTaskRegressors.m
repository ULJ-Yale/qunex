function [model] = g_CreateTaskRegressors(fidlf, concf, model, ignore)

%
%   Returns task regressors for each bold run
%
%   INPUT
%   - fidlf - subject's fidl event file
%   - concf - subject's conc file or an array of run lengths
%   - model - array structure that specifies what needs to be modelled and how or a string description
%     - decription - description of the model
%     - regressor  - a structure array that specifies each regressor with fields:
%         - name - given name
%         - code - event codes (used in fidl file)
%         - hrf_type
%           -> 'boynton' (assumed response)
%           -> 'SPM' (assumed response)
%           -> 'gamma' (assumed response)
%           -> 'u' (unassumed response)
%           -> 'block' (block response)
%         - length
%           - number of frames to model (for unasumed response)
%           - length of event in s (for assumed response - if empty, duration is taken from event file)
%           - start and end offset in frames (for block response)
%         - weight
%           - column
%           - normalize (within vs. across)
%           - method    (z, 01, -11, none)
%   - ignore - what to do with frames to ignore
%       -> 'no' (don't do anything)
%       -> 'ignore' (ignore those frames)
%       -> 'specify' (create a separate regressor)
%       -> 'both' (ignore and specify)
%
%   OUTPUT
%   - model - struct with the specified model
%     - run - struct array with per run data
%       - regressors - cell array of regressor names taken from event file
%       - matrix - matrix of regressor values for the run
%     - columns - description of columns
%       - event - event name
%       - frame - frame of that event (for unassumed models)
%     - regressor
%     - description
%     - ignore
%     - fidl
%
%   NOTES
%   - would be good to include other HRF types as well as estimated HRF
%   - !!! assumed response regressors get normalized to 1 only within each run !!!!
%   ... perhaps add a normalizing pass for all regressors at the end of the script
%   - !!! it only correctly works with TR precision to 1 decimal point ... should perhaps change to 2 decimal points
%   -> changed 2011.07.31
%   - !!! might be better to change downsampling to summation
%   -> changed to area under the curve 2011.07.31
%
%   ---
%   Grega Repovs - Created: 2008-07-11
%
%   Changelog
%          2008-07-16 Grega Repovš - Updated
%          2011-01-24 Grega Repovš - Updated
%          2011-02-11 Grega Repovš - Updated
%          2011-07-31 Grega Repovš - Updated
%          2015-10-23 Grega Repovš - Updated (Error reporting for missing event info.)
%          2016-02-04 Grega Repovš - Updated (Added behavioral regressors and changed output structure)
%          2017-02-11 Grega Repovš - Updated to use the general g_HRF function.



% ---> set variables

if nargin < 4
    ignore = [];
end

if isempty(ignore)
    ignore = 'no';
end


% ---> get event data

events = g_ReadEventFile(fidlf);

% ---> get data on run lengths

if isa(concf, 'char')
    frames = g_GetImageLength(concf);
else
    frames = concf;
end
nruns  = length(frames);

% ---> get model data

if isa(model, 'char')
    model = parseModels(model);
end
nregressors = length(model.regressor);

% ---> convert string codes to number codes if necessary

for m = 1:nregressors
    if isempty(model.regressor(m).code)
        model.regressor(m).code = find(ismember(events.events, model.regressor(m).event)) - 1;
    end
end


%=========================================================================
%                         loop over all the models and compute the weights

events.weights = ones(events.nevents, nregressors);
valide  = events.event >= 0;
nvalide = sum(valide);

for m = 1:nregressors
    if ~isempty(model.regressor(m).weight.column)
        w = events.beh(:, model.regressor(m).weight.column);

        % --- are we normalizing at all

        if ~strcmp(model.regressor(m).weight.method, 'none')

            % --- what are we normalizing over > create a mask, extract relevant data

            wm = ones(nvalide, 1) == 1;
            if model.regressor(m).weight.normalize(1) == 'w'
                wm = ismember(events.event(valide), model.regressor(m).code);
            end

            tw = w(wm);

            % --- normalize

            switch strtrim(model.regressor(m).weight.method)

            case 'z'
                tw = zscore(tw);

            case '01'
                tw = (tw - min(tw)) / (max(tw) - min(tw));

            case '-11'
                tw = (tw - min(tw)) / (max(tw) - min(tw)) * 2 - 1;

            otherwise
                error('\nERROR: No known option for behavioral covariates normalization method [%s]!\n', model.regressor(m).weight.method);

            end

            % --- embed back

            w(wm) = tw;
            w(~wm) = 0;
        end

        events.weights(valide, m) = w;
    end
end


%=========================================================================
%                                  loop over all the runs in the conc file

model.columns.event = {};
model.columns.frame = [];

for r = 1:nruns

    %------------------------- set base variables

    nframes = frames(r);
    if r > 1
        start_frame = sum(frames(1:r-1)) + 1;
    else
        start_frame = 1;
    end
    end_frame = start_frame + nframes - 1;

    in_run = (events.frame >= start_frame) & (events.frame <= end_frame);

    run(r).matrix = [];
    run(r).regressors = {};

    %------------------------- loop over models

    for m = 1:nregressors

        relevant = in_run & ismember(events.event, model.regressor(m).code);
        nrelevant = sum(relevant);

        basename = model.regressor(m).name;

        model.regressor(m).hrf_type = lower(model.regressor(m).hrf_type);

        %------------------------- code for unassumed models

        if strcmp(model.regressor(m).hrf_type, 'u')

            mtx = zeros(nframes, model.regressor(m).length);
            rel_frame  = events.frame(relevant);
            rel_weight = events.weights(relevant, m);

            for ievent = 1:nrelevant
                for iframe = 1:model.regressor(m).length
                    target = rel_frame(ievent) - start_frame + iframe;
                    if target <= nframes
                        mtx(target, iframe) = rel_weight(ievent);
                    end
                end
            end

            run(r).matrix = [run(r).matrix mtx];

            for iname = 1:model.regressor(m).length
                run(r).regressors = [run(r).regressors, [basename '.' num2str(iname)]];
            end
            if r == 1
                model.columns.event(end+1:end+model.regressor(m).length) = {basename};
                model.columns.frame(end+1:end+model.regressor(m).length) = 1:model.regressor(m).length;
            end


        %------------------------- code for block models

        elseif strcmp(model.regressor(m).hrf_type, 'block')

            ts = zeros(nframes, 1);
            soff = 0;
            eoff = 0;

            if ~isempty(model.regressor(m).length)
                soff = model.regressor(m).length(1);
                if length(model.regressor(m).length) > 1
                    eoff = model.regressor(m).length(2);
                end
            end

            rel_start   = events.frame(relevant) - start_frame + 1;
            rel_end     = events.frame(relevant) - start_frame + events.elength(relevant);
            rel_weights = events.weights(relevant, m);

            for ievent = 1:nrelevant
                e_start = rel_start(ievent) + soff;
                e_end   = rel_end(ievent) + eoff;
                if e_end > length(ts)
                    e_end = length(ts);
                end
                if(e_start < 1)
                    fprintf('r:%d, m:%d, ie:%d, sf:%d, tr:%.4f\n', r, m, ievent, e_start, events.TR);
                    fprintf('\n');
                    fprintf('%d ', relevant);
                    fprintf('\n');
                    fprintf('%d ', in_run);
                    fprintf('\n');
                    fprintf('%d ', frames);
                    fprintf('\n');
                    fprintf('%.2f ', events.event_s(relevant));
                end
                ts(e_start:e_end, 1) = rel_weights(ievent);
            end

            run(r).matrix = [run(r).matrix ts];
            run(r).regressors = [run(r).regressors, basename];
            if r == 1
                model.columns.event(end+1) = {basename};
                model.columns.frame(end+1) = 1;
            end


        %------------------------- code for assumed models

        elseif ismember(model.regressor(m).hrf_type, {'boynton', 'spm', 'gamma'})

            %======================================================================
            %                                                  create the right HRF

            hrf = g_HRF(events.TR/100, model.regressor(m).hrf_type);

            %======================================================================
            %                                           create the event timeseries

            % ts = zeros(round(events.TR*100)*nframes),1);
            ts = zeros(100*nframes,1);

            rel_times   = events.event_s(relevant);
            rel_times   = rel_times - (start_frame-1) * events.TR;
            rel_weights = events.weights(relevant, m);

            rel_lengths = events.event_l(relevant);
            if (~isempty(model.regressor(m).length))
                rel_lengths(:) = model.regressor(m).length;
            end

            for ievent = 1:nrelevant
                % e_start = floor(rel_times(ievent)*100)+1;
                % e_end = e_start + floor(rel_lengths(ievent)*100) -1;
                e_start = floor(rel_times(ievent)/events.TR*100)+1;
                e_end   = e_start + floor(rel_lengths(ievent)/events.TR*100)-1;

                if e_end > length(ts)
                    e_end = length(ts);
                end
                if(e_start < 1)
                    fprintf('r:%d, m:%d, ie:%d, sf:%d, tr:%.4f\n', r, m, ievent, start_frame, events.TR);
                    fprintf('\n');
                    fprintf('%d ', relevant);
                    fprintf('\n');
                    fprintf('%d ', in_run);
                    fprintf('\n');
                    fprintf('%d ', frames);
                    fprintf('\n');
                    fprintf('%.2f ', events.event_s(relevant));
                end
                ts(e_start:e_end,1) = rel_weights(ievent);
            end

            %======================================================================
            %                          convolve event with HRF, downsample and crop

            ts = conv(ts, hrf);
            ts = ts(1:100*nframes);
            ts = mean(reshape(ts, 100, nframes), 1);
            if max(ts) > 0
                ts = ts/max(ts);
            end

            run(r).matrix = [run(r).matrix ts'];
            run(r).regressors = [run(r).regressors, basename];

            if r == 1
                model.columns.event(end+1) = {basename};
                model.columns.frame(end+1) = 1;
            end

        end

    %------------------------- end models loop
    end

    %======================================================================
    %                                                 zero frames to ignore

    if ~strcmpi(ignore, 'no')

        ts = zeros(nframes, 1);

        relevant  = in_run & (events.event == -1);
        nrelevant = sum(relevant);

        rel_start = events.frame(relevant) - start_frame + 1;
        rel_end   = events.frame(relevant) - start_frame + events.elength(relevant);

        for ievent = 1:nrelevant
            e_start = rel_start(ievent);
            e_end   = rel_end(ievent);
            if e_end > nframes
                e_end = nframes;
            end
            ts(e_start:e_end, 1) = 1;
        end

        if strcmpi(ignore, 'ignore') | strcmpi(ignore, 'both')
            run(r).matrix(ts==1, :) = 0;
        end
        if strcmpi(ignore, 'specify') | strcmpi(ignore, 'both')
            run(r).matrix = [run(r).matrix ts];
            run(r).regressors = [run(r).regressors, 'ignore'];
        end

    end
    %------------------------- end zero frames to ignore

end

model.run    = run;
model.ignore = ignore;
model.fidl   = events;




%   ----> function to parse model description to model structure
%
%   - description
%     - pipe separated list of regressor information for each event
%       assumed: <fidl code>:<hrf>[:<length in s>] --- length assumed empty if not provided
%       unassumed: <fidl code>:<length in frames>
%     - each regressor info can follow with ">" and a weight descriptor in a form
%       <name of the resulting regressor>[:<behavioral column to use from fidl file (1-based)>[:<normalization span>[:<normalization method>]]]
%
%   - model - array structure that specifies what needs to be modelled and how or a string description
%     - code - event codes (used in fidl file)
%     - hrf_type
%       -> 'boynton' (assumed response)
%       -> 'SPM' (assumed response)
%       -> 'u' (unassumed response)
%       -> 'block' (block response)
%     - length
%       - number of frames to model (for unasumed response)
%       - length of event in s (for assumed response - if empty, duration is taken from event file)
%       - start and end offset in frames (for block response)
%     - weight
%       - name
%       - column
%       - normalize (within vs. across)
%       - method    (z, 01, -11, none)


function [model] = parseModels(s)

a = strtrim(splitby(s, '|'));

for n = 1:length(a)

    m = strtrim(splitby(a{n}, '>'));
    if length(m) == 0
        continue
    end

    % --=> deal with the event modelling specification

    b = strtrim(splitby(m{1}, ':'));
    regressor(n).event = strtrim(splitby(b{1}, ','));
    regressor(n).code  = [];

    if length(b) == 0
        continue
    end

    % --- do we have event modelling info?

    if length(b) == 1
        error('\nERROR: Can not parse event model, no information given for event: %s\n', b{1});
    end

    % --- is field 2 a number ?

    if sum(isletter(b{2}))
        regressor(n).hrf_type = b{2};
        regressor(n).length = [];
    else
        regressor(n).hrf_type = 'u';
        regressor(n).length = str2num(b{2});
    end

    % --- do we have a third field ?

    if length(b) >= 3
        regressor(n).length = str2num(b{3});
    end
    if length(b) == 4
        regressor(n).length = [regressor(n).length str2num(b{4})];
    end

    % --=> deal with weighting specification

    if length(m) > 1
        c = strtrim(splitby(m{2}, ':'));
        nc = length(c);

        if nc > 0, regressor(n).name             = c{1}         ; else regressor(n).name             = [];       end
        if nc > 1, regressor(n).weight.column    = str2num(c{2}); else regressor(n).weight.normalize = [];       end
        if nc > 2, regressor(n).weight.normalize = c{3}         ; else regressor(n).weight.normalize = 'within'; end
        if nc > 3, regressor(n).weight.method    = c{4}         ; else regressor(n).weight.method    = 'z';      end
    else
        regressor(n).name             = strjoin(regressor(n).event, '|');
        regressor(n).weight.column    = [];
        regressor(n).weight.normalize = [];
        regressor(n).weight.method    = [];
    end

end

model.regressor   = regressor;
model.description = s;



function [out] = splitby(s, d)
c = 0;
while length(s) >=1
    c = c+1;
    [t, s] = strtok(s, d);
    if length(s) > 1, s = s(2:end); end
    out{c} = t;
end








