function [out] = fc_ReadEventFile(file)

%	
%	Reads fidl event file and returns a structure that includes:
%	
%	frame - frame number of the event start
%	elength - event length in frames
%	event - event code
%	events - list of event names
%	TR - tr in s
%	

fin = fopen(file);
s = fgetl(fin);
events = strread(s, '%s');
TR = str2num(char(events(1)));
events = events(2:length(events));

frame 	= [];
elength = [];
event 	= [];
beh     = [];
ignore  = [];

while feof(fin) == 0
	s = fgetl(fin);
	s = strrep(s, 'NA', 'NaN');
	t = sscanf(s, '%f')';
	nelements = length(t);
	
	if nelements == 2
	    ignore = [ignore; floor(t(1)/TR) abs(t(2))];
    elseif nelements >= 3
        frame 	= [frame; floor(t(1)/TR)];
    	elength = [elength; floor(t(3)/TR)];
    	event 	= [event; t(2)];
    end
    if nelements >3
        beh = [beh; t(4:end)];
	end
end

fclose(fin);

% -----------------------------------------------------   create mask based on ignore information

if ~isempty(ignore)
    minframes = ignore(end,1)+ignore(end,2)-1;
    mask = ones(minframes,1);
    nignores = size(ignore,1);
    for n = 1:nignores
        mask(ignore(n):ignore(n,1)+ignore(n,2)-1,1) = 0;
    end
else
    mask = [];
end

out.frame = frame;
out.elength = elength;
out.event = event;
out.events = events;
out.ignore = ignore;
out.mask = mask;
out.TR = TR;
