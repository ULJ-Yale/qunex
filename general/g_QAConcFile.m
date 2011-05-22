function [r] = g_QAConcFile(file, do, target)

%	
%	Reads a conc file and returns a list of files
%	
%	files - list of paths
%	

if nargin < 3
    target = strrep(file, ".conc", "");
    if nargin < 2
        do = {'m','sd'}
    end
end

if ~iscell(do)
    do = {do};
end


files = g_ReadConcFile(file);
nfiles = length(files);
nstats = length(do);

t = gmrimage(files{1}, [], 1);
for nr = 1:nstats
    r(nr) = t.zeroframes(nfiles);
end

for n = 1:nfiles
    d = gmrimage(files{n});
    d = d.mri_Stats(do);
    d.data = d.image2D;
    for nr = 1:nstats
        r(nr).data(:,n) = d.data(:,nr);
    end
end

for nr = 1:nstats
    r(nr).mri_saveimage([target '.' do{nr}]);
end
