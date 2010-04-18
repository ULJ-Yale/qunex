function [ematrix] = g_CreateUnassumedResponseTaskRegressors(fidlfile, eventstring, nframes)

%	
%	Parameters:
%	fidlfile    : the path to the fidl file to use
%	eventstring : the string describing which events to code and how many frames to model
%               - format: 'event1,event2:nframesA|event3:nframesB'
%	nframes     : the number of frames for the eventmatrix (number of frames in the BOLD)
%	

%	Reads fidl event file and returns a structure that includes:
%	
%	frame   - frame number of the event start
%	elength - event length in frames
%	event_s - start of the event in s
%	event_l - length of the event in s
%	event   - event code
%	events  - list of event names
%	TR      - tr in s
%	

fevents = g_ReadEventFile(fidlfile);
tevents = parseEvents(eventstring);

ematrix = [];

for n = 1:length(tevents)
    tmatrix = zeros(nframes+30, tevents(n).frames);
    for f = 1:tevents(n).frames
        [x tcodes] = ismember(tevents(n).events, fevents.events);
        tcodes = tcodes - 1;
        tframes = fevents.frame(ismember(fevents.event, tcodes)) +f -1;
        tmatrix(tframes,f) = 1;
    end
    ematrix = [ematrix tmatrix];
end

ematrix = ematrix(1:nframes,:);

end

function [out] = parseEvents(s, names)
    a = splitby(s,'|');
    for n = 1:length(a)
        b = splitby(a{n}, ':');
        out(n).frames = str2num(b{2});
        out(n).events = splitby(b{1},',');
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
end