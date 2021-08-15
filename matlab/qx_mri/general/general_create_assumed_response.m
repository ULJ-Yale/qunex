% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

function [ts] = general_create_assumed_response(TR, frames, delay, elength, hrf_type)

%``function [ts] = general_create_assumed_response(TR, frames, delay, elength, hrf_type)``
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

%======================================================================
%                                                  create the right HRF

hrf = [];

hrf_type = lower(hrf_type);

if ismember(hrf_type, {'boynton', 'spm', 'gamma'}
    hrf = general_hrf(0.1, hrf_type);
else
    error('ERROR: There was no valid HRF type specified [general_create_task_regressors(TR, frames, delay, elength, hrf_type)]');
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

