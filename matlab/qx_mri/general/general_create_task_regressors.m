function [model] = general_create_task_regressors(fidlf, concf, model, ignore, check)

%``general_create_task_regressors(fidlf, concf, model, ignore, check)``
%
%   Create task regressors for each bold run.
%
%   INPUTS
%   ======
%
%   --fidlf     session's fidl event file
%   --concf     session's conc file or an array of run lengths
%   --model     array structure that specifies what needs to be modelled and how 
%               or a string description:
%
%               decription
%                   description of the model
%               regressor
%                   a structure array that specifies each regressor with fields:
%
%                   - name - given name
%                   - code - event codes (used in fidl file)
%                   - hrf_type:
%                       - 'boynton' (assumed response)
%                       - 'SPM' (assumed response)
%                       - 'gamma' (assumed response)
%                       - 'u' (unassumed response)
%                       - 'block' (block response)
%               normalize
%                   - run - normalize hrf based regressors to amplitude 1 within 
%                           each run separately (old behavior)
%                   - uni - normalize hrf based regressors universaly to hrf 
%                           area-under-the-curve = 1 (new behavior)
%               length
%                  - number of frames to model (for unasumed response)
%                  - length of event in s (for assumed response - if empty, 
%                    duration is taken from event file)
%                  - start and end offset in frames (for block response)
%
%               weight
%                   - column
%                   - normalize (within vs. across)
%                   - method    (z, 01, -11, none)
%
%   --ignore    what to do with frames to ignore ['no']
%
%               - 'no' (don't do anything)
%               - 'ignore' (ignore those frames)
%               - 'specify' (create a separate regressor)
%               - 'both' (ignore and specify)
%
%   --check     how to handle event mismatch between fidlf and model ['warning']
%
%               - 'ignore' (don't do anything)
%               - 'warning' (throw a warning)
%               - 'error' (throw an error)
%
%   OUTPUT
%   ======
%
%   model
%       struct with the specified model
%
%       - run ... struct array with per run data
%
%           - regressors - cell array of regressor names taken from event file
%           - matrix - matrix of regressor values for the run
%
%       - columns ... description of columns
%
%           - event - event name
%           - frame - frame of that event (for unassumed models)
%
%       - regressor
%       - description
%       - ignore
%       - fidl
%
%   USE
%   ===
%
%   The function takes a session's fidl and conc file and based on the
%   information provided in the model variable generates a matrix of regressors
%   for each bold file separately. It returns the information in a data
%   structure.
%
%   The input model can be specified as a struct variable (as described above)
%   or using a specificaly structured string. The string should provide a pipe 
%   separated list of regressor descriptions for each event:
%
%   - assumed regressors: "<fidl code>:<hrf>[-run|-uni][:<length in s>]"
%     Example 1: "encoding:SPM-uni:5" - model encoding using SPM HRF with 
%     5 second duration, normalize the regressor universaly (see below).
%     If the length is not provided, the duration specified in the fidl file
%     will be used.
%     Example 2: "response:boynton-run" - model response using Boynton
%     HRF function, take the duration from the fidl file. Normalize the
%     regressor amplitude to value 1 within each run separately.
%
%   - unassumed regressors: "<fidl code>:<length in frames>"
%     Example 1: "congruent:8" - model congruent trials using separate
%     regressors across 8 frames following the event start.
%
%   - each regressor info can follow with ">" and a weight descriptor in a form
%     "<name of the resulting regressor>[:<behavioral column to use from fidl 
%     file (1-based)>[:<normalization span>[:<normalization method>]]]"
%     Example 1: "delay:SPM-uni>delay_precision:2:within:z" - scale the assumed
%     regressor for each trial by the values provided in the second extra column
%     in the fidl file. Before applying the scaling, normalize the values from 
%     the second column to z-scores taking into account only the values that 
%     pertain to delay trials.
%     Example 2: "emotional:11>emotional_rt:3:across:-11" - scale the 11 
%     unassumed regressors for each trial by values provided in the third extra
%     column in the fidl file. Before applying the scaling, normalize the values
%     to span -1 to 1 across all the values in the fidl file column.
%
%   Assumed HRF regressors normalization
%   hrf_types `boynton` and `SPM` can be marked with an additional flag denoting
%   how to normalize the regressor. 
%   
%   In case of `<hrf function>-uni`, e.g. 
%   'boynton-uni' or 'SPM-uni', the HRF function will be normalized to have 
%   the area under the curve equal to 1. This ensures uniform and universal, 
%   scaling of the resulting regressor across all event lengths. In addition,
%   the scaling is not impacted by weights (e.g. behavioral coregressors), which
%   in turn ensures that the weights are not scaled.
%
%   In case of `<hrf function>-run`, e.g. `boynton-run` or `SPM-run`, the 
%   resulting regressor is normalized to amplitude of 1 within each bold run 
%   separately. This can result in different scaling of regressors with different 
%   durations, and of the same regressor across different runs. Scaling in this 
%   case is performed after the signal is weighted, so in effect the scaling of  
%   weights (e.g. behavioral regressors), can differ across bold runs.
%
%   The flag can be abbreviated to '-r' and '-u'. If not specified, '-uni' will
%   be assumed.
%
%   EXAMPLE USE
%   ===========
%
%   ::
%
%       model = general_create_task_regressors('OP354-flanker.fidl', ...
%       'OP354-flanker.conc', 'taskblock:boynton-uni|congruent:7|incongruent:7', ...
%       'ignore');
%
%   NOTES
%   =====
%
%   Assumed response regressors now get normalized to HRF area-under-the-curve = 1
%   by default. This results in different assumed HRF regressor scaling and 
%   resulting GLM beta estimates as of QuNex version 0.93.4.
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

% ---> set variables

if nargin < 4 || isempty(ignore),   ignore   = 'no';      end
if nargin < 5 || isempty(check), check = 'warning'; end
if ~any(strcmpi({'ignore','warning','error'},check))
    error('\nERROR: Option [%s] for handleEM argument is invalid! Valid options are ''ignore'', ''warning'' and ''error''.\n',check);
end

% ---> get event data

tevents = general_read_event_file(fidlf);

% ---> get data on run lengths

if isa(concf, 'char')
    frames = general_get_image_length(concf);
else
    frames = concf;
end
nruns  = length(frames);

% ---> get model data

if isa(model, 'char')
    model = parseModels(model);
end
nregressors = length(model.regressor);

% ---> convert string codes to number codes if necessary and check if event
% in the model exists in the fidl file

for m = 1:nregressors
    if isempty(model.regressor(m).code)
        model.regressor(m).code = find(ismember(tevents.events, model.regressor(m).event)) - 1;
    end
    % -- check normalize and set it to default if not set
    if ~isfield(model.regressor(m), 'normalize') || isempty(model.regressor(m).normalize)
        model.regressor(m).normalize = 'uni';
    end
    % if ~any(strcmp(tevents.events,model.regressor(m).name))
    %     switch lower(check)
    %         case 'warning'
    %             warning('\general_create_task_regressors: Event [%s] from the model not found in the fidl file!\n', model.regressor(m).name);
    %         case 'error'
    %             error('\nERROR: Event [%s] from the model not found in the fidl file!\n', model.regressor(m).name);
    %     end
    % end
end


%=========================================================================
%                         loop over all the models and compute the weights

tevents.weights = ones(tevents.nevents, nregressors);
valide  = tevents.event >= 0;
nvalide = sum(valide);

for m = 1:nregressors
    if ~isempty(model.regressor(m).weight.column)
        w = tevents.beh(:, model.regressor(m).weight.column);
        
        % --- are we normalizing at all
        
        if ~strcmp(model.regressor(m).weight.method, 'none')
            
            % --- what are we normalizing over > create a mask, extract relevant data
            
            wm = ones(nvalide, 1) == 1;
            if model.regressor(m).weight.normalize(1) == 'w'
                wm = ismember(tevents.event(valide), model.regressor(m).code);
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
        
        tevents.weights(valide, m) = w;
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
    
    in_run = (tevents.frame >= start_frame) & (tevents.frame <= end_frame);
    
    run(r).matrix = [];
    run(r).regressors = {};
    
    %------------------------- loop over models
    
    for m = 1:nregressors
        
        relevant = in_run & ismember(tevents.event, model.regressor(m).code);
        nrelevant = sum(relevant);
        
        basename = model.regressor(m).name;
        
        model.regressor(m).hrf_type = lower(model.regressor(m).hrf_type);
        
        %------------------------- code for unassumed models
        
        if strcmp(model.regressor(m).hrf_type, 'u')
            
            mtx = zeros(nframes, model.regressor(m).length);
            rel_frame  = tevents.frame(relevant);
            rel_weight = tevents.weights(relevant, m);
            
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
            
            rel_start   = tevents.frame(relevant) - start_frame + 1;
            rel_end     = tevents.frame(relevant) - start_frame + tevents.elength(relevant);
            rel_weights = tevents.weights(relevant, m);
            
            for ievent = 1:nrelevant
                e_start = rel_start(ievent) + soff;
                e_end   = rel_end(ievent) + eoff;
                if e_end > length(ts)
                    e_end = length(ts);
                end
                if(e_start < 1)
                    fprintf('r:%d, m:%d, ie:%d, sf:%d, tr:%.4f\n', r, m, ievent, e_start, tevents.TR);
                    fprintf('\n');
                    fprintf('%d ', relevant);
                    fprintf('\n');
                    fprintf('%d ', in_run);
                    fprintf('\n');
                    fprintf('%d ', frames);
                    fprintf('\n');
                    fprintf('%.2f ', tevents.event_s(relevant));
                end
                % fprintf('\n -> e_start: %d, e_end: %d', e_start, e_end);
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
            
            hrf = general_hrf(tevents.TR/100, model.regressor(m).hrf_type);
            
            %======================================================================
            %                                           create the event timeseries
            
            % ts = zeros(round(tevents.TR*100)*nframes),1);
            ts = zeros(100*nframes,1);
            
            rel_times   = tevents.event_s(relevant);
            rel_times   = rel_times - (start_frame-1) * tevents.TR;
            rel_weights = tevents.weights(relevant, m);
            
            rel_lengths = tevents.event_l(relevant);
            if (~isempty(model.regressor(m).length))
                rel_lengths(:) = model.regressor(m).length;
            end
            
            for ievent = 1:nrelevant
                % e_start = floor(rel_times(ievent)*100)+1;
                % e_end = e_start + floor(rel_lengths(ievent)*100) -1;
                e_start = floor(rel_times(ievent)/tevents.TR*100)+1;
                e_end   = e_start + floor(rel_lengths(ievent)/tevents.TR*100)-1;
                
                if e_end > length(ts)
                    e_end = length(ts);
                end
                if(e_start < 1)
                    fprintf('r:%d, m:%d, ie:%d, sf:%d, tr:%.4f\n', r, m, ievent, start_frame, tevents.TR);
                    fprintf('\n');
                    fprintf('%d ', relevant);
                    fprintf('\n');
                    fprintf('%d ', in_run);
                    fprintf('\n');
                    fprintf('%d ', frames);
                    fprintf('\n');
                    fprintf('%.2f ', tevents.event_s(relevant));
                end
                ts(e_start:e_end,1) = rel_weights(ievent);
            end
            
            %======================================================================
            %                          convolve event with HRF, downsample and crop
            
            ts = conv(ts, hrf);
            ts = ts(1:100*nframes);

            % -- normalize universaly with HRF area-under-the-curve = 1
            if strcmp(model.regressor(m).normalize, 'uni')
                ts = ts ./ sum(hrf(hrf>0));
            end

            ts = mean(reshape(ts, 100, nframes), 1);

            % -- normalize per run to max amplitude = 1
            if strcmp(model.regressor(m).normalize, 'run')
                if max(ts) > 0
                    ts = ts/max(ts);
                end
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
        
        relevant  = in_run & (tevents.event == -1);
        nrelevant = sum(relevant);
        
        rel_start = tevents.frame(relevant) - start_frame + 1;
        rel_end   = tevents.frame(relevant) - start_frame + tevents.elength(relevant);
        
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
model.fidl   = tevents;




%   ---> function to parse model description to model structure
%
%   - description
%     - pipe separated list of regressor information for each event
%       assumed: <fidl code>:<hrf>[-run|-uni][:<length in s>] --- length is assumed empty if not provided
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
%     - normalize
%       -> run (normalize hrf based regressors to amplitude 1 within each run separately -- old behavior)
%       -> uni (normalize hrf based regressors universaly to hrf area-under-the curve = 1 - n -- new behavior)
%     - length
%       - number of frames to model (for unasumed response)
%       - length of event in s (for assumed response - if empty, duration is taken from event file)
%       - start and end offset in frames (for block response)
%     - weight
%       - name
%       - column
%       - normalize (within vs. across)
%       - method    (z, 01, -11, none)
%
%   Assumed HRF regressors normalization
%   hrf_types `boynton` and `SPM` can be marked with an additional flag denoting
%   how to normalize the regressor. 
%   
%   In case of `<hrf function>-uni`, e.g. 
%   'boynton-uni' or 'SPM-uni', the HRF function will be normalized to have 
%   the area under the curve equal to 1. This ensures uniform and universal, 
%   scaling of the resulting regressor across all event lengths. In addition,
%   the scaling is not impacted by weights (e.g. behavioral coregressors), which
%   in turn ensures that the weights are not scaled.
%
%   In case of `<hrf function>-run`, e.g. `boynton-run` or `SPM-run`, the 
%   resulting regressor is normalized to amplitude of 1 within each bold run 
%   separately. This can result in different scaling of regressors with different 
%   durations, and of the same regressor across different runs. Scaling in this 
%   case is performed after the signal is weighted, so in effect the scaling of  
%   weights (e.g. behavioral regressors), can differ across bold runs.
%
%   The flag can be abbreviated to '-r' and '-u'. If not specified, '-uni' will
%   be assumed. The default has changed from the original '-run', which will 
%   result in different default assumed HRF regressor scaling and resulting GLM 
%   beta estimates as of QuNex version 0.93.4.


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

    % --- normalization type

    if ~isempty(strfind(regressor(n).hrf_type, '-u'))
        regressor(n).normalize = 'uni';
    elseif ~isempty(strfind(regressor(n).hrf_type, '-r'))
        regressor(n).normalize = 'run';
    else
        regressor(n).normalize = 'uni';
    end

    if ~isempty(strfind(regressor(n).hrf_type, '-'))
        regressor(n).hrf_type = regressor(n).hrf_type(1:strfind(regressor(n).hrf_type, '-')-1);
    end

    % --- do we have a third field ?
    
    if length(b) >= 3
        regressor(n).length = str2num(b{3});
    end
    if length(b) == 4
        regressor(n).length = [regressor(n).length str2num(b{4})];
    end
    
    % --=> deal with weighting specification
    
    regressor(n).name             = strjoin(regressor(n).event, '|');
    regressor(n).weight.column    = [];
    regressor(n).weight.normalize = [];
    regressor(n).weight.method    = [];
    
    if length(m) > 1
        c = strtrim(splitby(m{2}, ':'));
        nc = length(c);
        
        if nc > 0, regressor(n).name             = c{1}         ; else regressor(n).name             = [];       end
        if nc > 1, regressor(n).weight.column    = str2num(c{2}); else regressor(n).weight.normalize = [];       end
        if nc > 2, regressor(n).weight.normalize = c{3}         ; else regressor(n).weight.normalize = 'within'; end
        if nc > 3, regressor(n).weight.method    = c{4}         ; else regressor(n).weight.method    = 'z';      end
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








