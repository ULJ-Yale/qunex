function [snr, sd] = g_ComputeSNRGroup(flist, target, fmask)

%	
%	function [snr, sd] = g_ComputeSNRGroup(flist, fmask target)
%	
%	Computes SNR and SD for the whole group.
%	
%	flist   	- conc-like style list of subject image files or conc files: 
%                  subject id:<subject_id>
%                  roi:<path to the individual's ROI file>
%                  file:<path to bold files - one per line>
%	mask		- an array mask defining which frames to use (1) and which not (0)
%   target      - file to save results into
%	
% 	Created by Grega Repovš on 2010-11-22.
% 	Modified by Grega Repovš on 2010-11-23.
%
% 	Copyright (c) 2010. All rights reserved.


fprintf('\n\nStarting ...');

if nargin < 3
    target = [];
    if nargin < 2
    	mask = [];
    end
end


%   ------------------------------------------------------------------------------------------
%   -------------------------------------------------- make a list of all the files to process

fprintf('\n ... listing files to process');

files = fopen(flist);
c = 0;
af = 0;
while feof(files) == 0
    s = fgetl(files);
    if ~isempty(strfind(s, 'subject id:'))
        c = c + 1;
        [t, s] = strtok(s, ':');        
        subject(c).id = strtrim(s(2:end));
        nf = 0;
    elseif ~isempty(strfind(s, 'roi:'))
        [t, s] = strtok(s, ':');        
        subject(c).roi = strtrim(s(2:end));
        g_CheckFile(subject(c).roi);
    elseif ~isempty(strfind(s, 'file:'))
        nf = nf + 1;
        af = af + 1;
        [t, s] = strtok(s, ':');        
        subject(c).files{nf} = strtrim(s(2:end));
        g_CheckFile(s(2:end));        
    end
end


fprintf(' ... done.');


%   ------------------------------------------------------------------------------------------
%   -------------------------------------------- The main loop ... go through all the subjects

%   --- Get variables ready first


nsubjects = length(subject);
snr = zeros(af,1);
sd  = zeros(af,1);
[path, fname] = fileparts(flist);
fout = fopen(fullfile(target, [fname '_SNR_report.txt']), 'w');
fprintf(fout, 'image\tSNR\tSD\n');

c = 1;
for s = 1:nsubjects
    
    %   --- reading in image files
    tic; 
	fprintf('\n ... processing %s', subject(s).id);
	
	nfiles = length(subject(s).files);
	for n = 1:nfiles
		[snr(c) sd(c)] = g_ComputeSNR(subject(s).files{n}, [], fmask, target, [], [subject(s).id '_file_' num2str(n)]);
		fprintf(fout, '%s\t%.3f\t%.3f\n', subject(s).files{n}, snr(c), sd(c));
		c = c +1;
	end

end

fclose(fout);
