function [run] = g_CreateTaskRegressors(fidlf, concf, model, ignore)

%   
%   Returns task regressors for each bold run 
%   
%   INPUT
%   - fidlf - subject's fidl event file
%   - concf - subject's conc file or an array of run lengths
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
%   - ignore - what to do with frames to ignore
%       -> 'no' (don't do anything)
%       -> 'ignore' (ignore those frames)
%       -> 'specify' (create a separate regressor)
%       -> 'both' (ignore and specify)
%
%   OUTPUT
%   - run - array struct for each run
%     - regressors - cell array of regressor names taken from event file
%     - matrix - matrix of regressor values for the run
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
%   Grega Repovs - Created: 2008.07.11
%                - Updated: 2008.07.16
%                - Updated: 2011.01.24
%                - Updated: 2011.02.11
%                - Updated: 2011.07.31
%

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
nmodels = length(model);

% ---> convert string codes to number codes if necessary

for m = 1:nmodels
    if ischar(model(m).code)
        model(m).code = find(ismember(events.events, model(m).code)) - 1;
    end
end


%=========================================================================
%                                  loop over all the runs in the conc file

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
    
    for m = 1:nmodels
        
        relevant = in_run & ismember(events.event, model(m).code);
        nrelevant = sum(relevant);
        
        %------------------------- code for unassumed models
        
        if strcmp(model(m).hrf_type, 'u')
        
            mtx = zeros(nframes, model(m).length);
            rel_frame = events.frame(relevant);
            
            for ievent = 1:nrelevant
                for iframe = 1:model(m).length
                    target = rel_frame(ievent) - start_frame + iframe;
                    if target <= nframes
                        mtx(target, iframe) = 1;
                    end
                end
            end
            
            run(r).matrix = [run(r).matrix mtx];
            
            basename = join(events.events(model(m).code+1), '_');
            for iname = 1:model(m).length
                run(r).regressors = [run(r).regressors, [basename '_' num2str(iname)]];
            end
        
        
        %------------------------- code for block models
        
        elseif strcmp(model(m).hrf_type, 'block')
            
            ts = zeros(nframes, 1);
            soff = 0;
            eoff = 0;
            
            if ~isempty(model(m).length)
                soff = model(m).length(1);
                if length(model(m).length) > 1
                    eoff = model(m).length(2);
                end
            end
            
            rel_start = events.frame(relevant) - start_frame + 1;
            rel_end   = events.frame(relevant) - start_frame + events.elength(relevant);
            
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
                ts(e_start:e_end,1) = 1;
            end
            
            run(r).matrix = [run(r).matrix ts];
            run(r).regressors = [run(r).regressors, join(events.events(model(m).code+1), '_')];
        
        
        %------------------------- code for assumed models
        
        elseif ismember(model(m).hrf_type, {'boynton', 'SPM'})
            
            %======================================================================
            %                                                  create the right HRF
            
            hrf = [];

            if strcmp(model(m).hrf_type, 'boynton')
                % t = [0:3200]./100;
                t = [0:32*round(100/events.TR)]./round(100/events.TR);
                hrf = fmri_hemodyn(t, 2.25, 1.25, 2);  % with parameters as suggested in the source
            end

            if strcmp(model(m).hrf_type, 'SPM')
                hrf = spm_hrf(events.TR/100);    % leaving parameters to their defaults
            end

            if isempty(hrf)
                error('There was no valid HRF type specified! [model: %d]', m);
            end
            
            %======================================================================
            %                                           create the event timeseries

            % ts = zeros(round(events.TR*100)*nframes),1);
            ts = zeros(100*nframes,1);
            
            rel_times = events.event_s(relevant);
            rel_times = rel_times - (start_frame-1)*events.TR;
            
            rel_lengths = events.event_l(relevant);
            if (~isempty(model(m).length))
                rel_lengths(:) = model(m).length;
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
                ts(e_start:e_end,1) = 1;
            end
            
            %======================================================================
            %                          convolve event with HRF, downsample and crop

            ts = conv(ts, hrf);
            ts = ts(1:100*nframes);
            ts = mean(reshape(ts,100,nframes),1);
            if max(ts) > 0
                ts = ts/max(ts);
            end
            
            run(r).matrix = [run(r).matrix ts'];
            run(r).regressors = [run(r).regressors, join(events.events(model(m).code+1), '_')];
            
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
            ts(e_start:e_end,1) = 1;
        end
        
        if strcmpi(ignore, 'ignore') | strcmpi(ignore, 'both')
            run(r).matrix(ts==1,:) = 0;
        end
        if strcmpi(ignore, 'specify') | strcmpi(ignore, 'both')
            run(r).matrix = [run(r).matrix ts];
            run(r).regressors = [run(r).regressors, 'ignore'];
        end
        
    end
    %------------------------- end zero frames to ignore

end



%------------------------ additional functions

function [s] = join(strings, delim)

s = strings{1};
slength = length(strings);
if slength > 1
    for n = 2:slength
        s = [s delim strings{n}];
    end
end


%   ----> function to parse model description to model structure
%
%   - description
%     - pipe separated list of model information for each event
%       assumed: <fidl code>:<model>[:<length in s>] --- length assumed empty if not provided
%       unassumed: <fidl code>:<length in frames>
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


function [model] = parseModels(s)

a = splitby(s, '|');

for n = 1:length(a)

    b = splitby(a{n},':');
    model(n).code = b{1};
    
    % --- is field 2 a number ?
    
    if sum(isletter(b{2}))
        model(n).hrf_type = b{2};
        model(n).length = [];
    else
        model(n).hrf_type = 'u';
        model(n).length = str2num(b{2});
    end
    
    % --- do we have a third field ?
    
    if length(b) >= 3
        model(n).length = str2num(b{3});
    end
    if length(b) == 4
        model(n).length = [model(n).length str2num(b{4})];
    end
end



function [out] = splitby(s, d)
c = 0;    
while length(s) >=1
    c = c+1;
    [t, s] = strtok(s, d);
    if length(s) > 1, s = s(2:end); end
    out{c} = t;
end








