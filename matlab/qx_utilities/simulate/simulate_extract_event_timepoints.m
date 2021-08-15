% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

function [tp] = simulate_extract_event_timepoints(TR, ts, eventlist, timepoints)

%``function [tp] = simulate_extract_event_timepoints(ts, eventlist, timepoints)``
%	
%   Function that extract specified timepoints from each event.
%
%   INPUTS
%	======
%
%   --TR            TR of the timeseries
%   --ts            timeseries
%   --eventlist     list of events to extract data for
%   --timepoints    timepoints within each event to extract values for
%
%   OUTPUT
%	======
%
%   tp
%		matrix of extracted timepoints
%

if nargin < 3
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


