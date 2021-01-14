function [tp] = si_ExtractEventTimepoints(TR, ts, eventlist, timepoints)

%``function [tp] = si_ExtractEventTimepoints(ts, eventlist, timepoints)``
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

%   ~~~~~~~~~~~~~~~~~~
%
%   Changelog
%
% 	2010-10-09 Grega Repovs
%			   Initial version.
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


