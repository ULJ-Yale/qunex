function [ts] = g_CreateAssumedResponse(TR, frames, delay, elength, hrf_type)

%   
%   Returns timecourse of an assumed response to an event 
%   
%   INPUT
%   - TR        - TR of the bold run
%   - frames    - number of frames over which to create response
%   - delay     - delay in s from the TR boundary
%   - elength   - duration of event in seconds
%   - hrf_type  - the type of assumed response to use
%       -> 'boynton' 
%       -> 'SPM'  
%       -> 'empirical' (not yet implemented)
%
%   OUTPUT
%   - ts       - a timeseries of the task regressor
%
%   NOTES
%   - would be good to include other HRF types as well as estimated HRF
%
%   Grega Repovš - 2008.7.12
%


%======================================================================
%                                                  create the right HRF

hrf = [];

if strcmp(hrf_type, 'boynton')
    t = [0:320]./10;
    hrf = fmri_hemodyn(t, 2.25, 1.25, 2);  % with parameters as suggested in the source
end

if strcmp(hrf_type, 'SPM')
    hrf = spm_hrf(0.1);    % leaving parameters to their defaults
end

if isempty(hrf)
    error('There was no valid HRF type specified [g_CreateTaskRegressors(TR, frames, delay, elength, hrf_type)]');
end

%======================================================================
%                                           create the event timeseries

ts = zeros(TR*frames*10,1);
e_start = floor(delay*10)+1;
e_end = e_start + floor(elength*10) -1;
if e_end > length(ts)
    e_end = length(ts);
end
ts(e_start:e_end,1) = 1;


%======================================================================
%                          convolve event with HRF, downsample and crop

ts = conv(ts, hrf);
ts = resample(ts, 1, round(TR*10));
ts = ts(1:frames);

