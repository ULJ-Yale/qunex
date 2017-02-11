function [run] = g_CreateTaskRegressors(fidlf, concf, model)

%
%   Returns task regressors for each bold run
%
%   INPUT
%   - fidlf - subject's fidl event file
%   - concf - subject's conc file
%   - model - array structure that specifies what needs to be modelled and how
%     - code - event codes (used in fidl file)
%     - hrf_type
%       -> 'boynton' (assumed response)
%       -> 'SPM' (assumed response)
%       -> 'u' (unassumed response)
%     - length
%       - number of frames to model (for unasumed response)
%       - length of event in s (for assumed response - if empty, duration is taken from event file)
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
%
%   ---
%   Written by Grega Repovš - 2008-7-11
%
%   Changelog
%   2017-02-11 Grega Repovš: Updated to use the general g_HRF function.

events = g_ReadEventFile(fidlf);
frames = g_GetImageLength(concf);
nruns  = length(frames);
nmodels = length(model);

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
                    target = rel_frame - start_frame + 1 + iframe;
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

        else

        %------------------------- code for assumed models


            %======================================================================
            %                                                  create the right HRF

            hrf_type = lower(model(m).hrf_type);

            if ismember(hrf_type, {'boynton', 'spm', 'gamma'}
                hrf = g_HRF(0.1, hrf_type);
            else
                error('There was no valid HRF type specified! [model: %d]', m);
            end


            %======================================================================
            %                                           create the event timeseries

            ts = zeros(events.TR*nframes*10,1);

            rel_times = events.event_s(relevant);
            rel_times = rel_times - (start_frame-1)*events.TR;

            rel_lengths = events.event_l(relevant);
            if (~isempty(model(m).length))
                rel_lengths(:) = model(m).length;
            end

            for ievent = 1:nrelevant
                e_start = floor(rel_times(ievent)*10)+1;
                e_end = e_start + floor(rel_lengths(ievent)*10) -1;
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
            ts = resample(ts, 1, round(events.TR*10));
            ts = ts(1:nframes);
            ts = ts/max(ts);

            run(r).matrix = [run(r).matrix ts];
            run(r).regressors = [run(r).regressors, join(events.events(model(m).code+1), '_')];

        end

    %------------------------- end models loop
    end

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


