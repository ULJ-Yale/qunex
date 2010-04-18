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
beh 	= [];

first = true;
while feof(fin) == 0
	s = fgetl(fin);
	s = strrep(s, 'NA', 'NaN');
	
	data = strread(s, '%f');
	
	if length(data) >= 3
	
		frame 	= [frame data(1)/TR];
		elength = [elength data(3)/TR];
		event 	= [event data(2)];
	
		if first
			nbeh = length(data)-3;
			first = false;
		end
		if nbeh
			beh = [beh; data(4:end)'];
		end
	end
end

fclose(fin);

out.frame = frame';
out.elength = elength';
out.event = event';
out.events = events;
out.beh = beh;
out.TR = TR;
