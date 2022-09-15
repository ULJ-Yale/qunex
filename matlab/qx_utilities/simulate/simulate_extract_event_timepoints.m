function [tp] = simulate_extract_event_timepoints(TR, ts, eventlist, timepoints)

%``simulate_extract_event_timepoints(TR, ts, eventlist, timepoints)``
%   
%   Function that extracts specified timepoints from each event.
%
%   Parameters:
%       --TR (float):
%           TR of the timeseries in seconds.
%
%       --ts (timeseries):
%           Timeseries.
%
%       --eventlist (array):
%           List of events to extract data for.
%
%       --timepoints (vector):
%           Timepoints within each event to extract values for.
%
%   Returns:
%       tp
%           Matrix of extracted timepoints.
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 4
    error('ERROR: Not enough parameters to extract event timepoints!');
end

% --- set up variables

nevents = size(eventlist,1);
tp      = zeros(nevents, size(ts,2));
timepoints  = timepoints';

% --- extract

for n = 1:nevents
    points = timepoints + ceil(eventlist(n,1)./TR) -1;
    tp(n,:) = mean(ts(points,:),1);
end
