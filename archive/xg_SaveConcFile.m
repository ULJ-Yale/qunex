function [] = g_SaveConcFile(file, files)

%	
%	Reads a conc file and returns a list of files
%	
%	files - list of paths
%	

[fout message] = fopen(file,'w');
if fout == -1
    error('\n\nERROR: Could not open %s for saving. Please check your paths!\n\nMatlab message: %s', file, message);
end

fprintf(fout, '    number_of_files: %d\n', length(files));
for n = 1:length(files)
	fprintf(fout, '               file:%s\n', files{n});
end
fclose(fout);
