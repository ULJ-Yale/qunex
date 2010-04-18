function [ifh] = g_ReadIFH(file)

%	
%	Reads a conc file and returns a list of files
%	
%	files - list of paths
%	

file = strrep(file, '.img', '.ifh');

[fin message]= fopen(file);
if fin == -1
    fprintf('\n\nWARNING: Could not open %s for reading. Returning empty header. Please check your paths!\nMatlab message: %s\n', file, message);
    ifh = [];
    return
end
c = 1;
while feof(fin) == 0
	s = fgetl(fin);
	[key, value] = strtok(s, ':=');
	value = strtrim(strrep(value, ':=', ''));
	key = strtrim(key);
	ifh.key{c} = key;
	ifh.value{c} = value;
	c = c + 1;
end
fclose(fin);

ifh.frames = str2num(char(ifh.value(ismember(ifh.key, {'matrix size [4]'}))));
ifh.samples = str2num(char(ifh.value(ismember(ifh.key, {'number of samples'}))));


%----

%function s = strtrim(s)
% V = char([9 10 11 12 13 32]);
% 
% t=1;
% while t == 1
%     if length(s)>1 & ismember(s(1), V)
%         s = s(2:length(s));
%     else
%         t == 0;
%     end
% end
% 
% t=1;
% while t == 1
%     if length(s)>1 & ismember(s(length(s)), V)
%         s = s(1:length(s)-1);
%     else
%         t == 0;
%     end
% end

