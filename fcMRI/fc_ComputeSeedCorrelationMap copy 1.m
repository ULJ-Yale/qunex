function [out] = fc_ComputeSeedCorrelationMap(eventf, concf, roif, roic, events, sframes, vframes, fframes, target)

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

% ======================================================
% 	----> filter out the events to include in the analysis

fprintf('\nStarting analysis\n... reading event data\n');

fevents = fc_ReadEventFile(eventf);
do = ismember(fevents.event, events);
fevents.event = fevents.event(do);
fevents.elength = fevents.elength(do);
fevents.frame = fevents.frame(do) + 1;
fevents.events = fevents.events(events);

% ======================================================
% 	----> read in region file and create a mask

fprintf('... reading roi definition image\n');

roi = fc_Read4DFPn(roif,1);
roi = ismember(roi, roic);

% ======================================================
% 	----> prepare GLM parameters

pl = zeros(fframes,1);
for n = 1:fframes
	pl(n)= (n-1)/(fframes-1);
end
pl = pl-0.5;

for n = 1:fframes
	p2(n) = pl(n)*pl(n);
end 
p2 = (p2*4)-0.5;

for n = 1:fframes
	p3(n) = pl(n)*l(n)*l(n);
end 
p3 = p3 - (min(p3)-0);
p3 = p3*16;
p3 = p3 - (pl+0.5)*3;









% ======================================================
% 	----> read in bold runs

fprintf('... extracting data from run 1 ');

nevents = length(fevents.event);
frames = int16(fevents.frame);
vframes = int16(vframes);
sframes = int16(sframes);


files = fc_ReadConcFile(concf);
img = zeros(147456,fframes);
seed = zeros(nevents, 1);
volumes = zeros(147456, nevents);

img = fc_Read4DFPn(char(files{1}),251);
c = 2;
for n = 1:nevents
	while frames(n) > fframes
		fprintf('%d ', c);
		img = fc_Read4DFPn(char(files{c}),251);
		c = c + 1;
		frames = frames - fframes;
	end

	ts = sframes + frames(n);
	tv = vframes + frames(n);
	seed(n) = mean(mean(img(roi,ts)));
	volumes(:,n) = mean(img(:,tv),2);
end

fprintf(' ... done\n');

% ======================================================
% 	----> computing correlations

fprintf('... computing correlations ');

fprintf('i ');
volumes = volumes';

fprintf('r ');
[r, p] = corr(seed, volumes);

fprintf('fz ');
fz = Fisher(r);

fprintf('z ');
z = ptoz(1-(p(1)/2),0,1);



fprintf('\n... writing images\n');

fc_Save4DFP(strcat(target, '_r.4dfp.img'),r);
fc_Save4DFP(strcat(target, '_p.4dfp.img'),p);
fc_Save4DFP(strcat(target, '_Fz.4dfp.img'),fz);
fc_Save4DFP(strcat(target, '_z.4dfp.img'),z);

fprintf('Done!\n');




