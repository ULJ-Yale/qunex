function [out] = fc_ComputeSeedCorrelationMap(eventf, concf, roif, roic, events, sframes, vframes)

%	
%	eventf - fidl event file for the bold runs
%	concf - conc file for the bold runs
%	roif - region image file
%	roic - region to use as seed
%	events - events to include in the analysis
%	sframes - seed frames to include in the analysis
%	vframes - volume frames to include in the analysis
%	target - target file name to output
%

% 	----> filter out the events to include in the analysis

fprintf('\nStarting analysis\n... reading event data\n');

fevents = fc_ReadEventFile(eventf);
do = ismember(fevents.event, events);
fevents.event = fevents.event(do);
fevents.elength = fevents.elength(do);
fevents.frame = fevents.frame(do) + 1;
fevents.events = fevents.events(events);

% 	----> read in region file and create a mask

fprintf('... reading roi definition image\n');

roi = fc_Read4DFPn(roif,1);
roi = ismember(roi, roic);

% 	----> read in bold runs

fprintf('... reading bold volumes  ');

files = fc_ReadConcFile(concf);
l = length(files);
img = zeros(147456*251,l);
for f = 1:l
	img(:,f) = fc_Read4DFPn(char(files{f}),251);
	fprintf('%d ', f);
end
fprintf(' ... reshaping');

img = reshape(i, 147456, []);
fprintf(' ... done\n');

% 	----> extract seed data

nevents = length(fevents.event);
seed = zeros(nevents);

for n = 1:nevents
	t = sframes + fevents.frame(n);
	seed(n) = mean(mean(img(roi,t)));
end

% 	----> extract volume data

volumes = zeros(147456, nevents);

for n = 1:nevents
	t = vframes + fevents.frame(n);
	volumes(:,n) = mean(img(:,t),2);
end

clear img



