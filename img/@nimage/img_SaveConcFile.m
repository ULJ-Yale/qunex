function [] = img_SaveConcFile(file, files)

% function [] = img_SaveConcFile(file, files)
%	
%	Saves a conc file 
%
%   Input
%	    file    - path to conc file
%	    files   - list of image files
%	

file = strtrim(file);
[fout message] = fopen(file,'w');
if fout == -1
    error('\n\nERROR: Could not open %s for saving. Please check your paths!\n\nMatlab message: %s', file, message);
end

fprintf(fout, '    number_of_files: %d\n', length(files));
for n = 1:length(files)
	fprintf(fout, '               file:%s\n', files{n});
end
fclose(fout);
