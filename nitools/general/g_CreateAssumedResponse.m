function [ts] = g_CreateAssumedResponse(TR, frames, delay, elength, hrf_type)

%``function [ts] = g_CreateAssumedResponse(TR, frames, delay, elength, hrf_type)``
%
%   Returns timecourse of an assumed response to an event.
%
%   INPUTS
%	======
%
%   --TR		 TR of the bold run
%   --frames	 number of frames over which to create response
%   --delay		 delay in s from the TR boundary
%   --elength	 duration of event in seconds
%   --hrf_type	 the type of assumed response to use
%
%       		 - 'boynton'
%       		 - 'SPM'
%       		 - 'gamma'
%       		 - 'empirical' (not yet implemented)
%
%   OUTPUTS
%	=======
%
%   - ts       - a timeseries of the task regressor
%


%   ~~~~~~~~~~~~~~~~~~
%
%   NOTES
%   - would be good to include other HRF types as well as estimated HRF
%
%   Changelog
%
%	2008-07-12 Grega Repovš
%			   Initial version
%   2017-02-11 Grega Repovš
%			   Updated to use general g_HRF function.
%


%======================================================================
%                                                  create the right HRF

hrf = [];

hrf_type = lower(hrf_type);

if ismember(hrf_type, {'boynton', 'spm', 'gamma'}
    hrf = g_HRF(0.1, hrf_type);
else
    error('ERROR: There was no valid HRF type specified [g_CreateTaskRegressors(TR, frames, delay, elength, hrf_type)]');
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

