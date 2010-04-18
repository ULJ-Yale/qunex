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
fevents.events = fevents.events(events+1);

% ======================================================
% 	----> read in region file and create a mask

fprintf('... reading roi definition image\n');

roi = fc_Read4DFPn(roif,1);
roi = ismember(roi, roic);

% ======================================================
% 	----> read in bold runs

fprintf('... extracting data from run 1');

nevents = length(fevents.event);
frames = int16(fevents.frame);
vframes = int16(vframes);
sframes = int16(sframes);


files = fc_ReadConcFile(concf);
img = zeros(147456,fframes);
seed = zeros(nevents, 1);
volumes = zeros(147456, nevents);

img = getResiduals(char(files{1}),fframes);
c = 2;
for n = 1:nevents
	while frames(n) > fframes
		fprintf('%d', c);
		img = getResiduals(char(files{c}),fframes);
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

% ------------------------> set up matrices


y = volumes';  				
x = repmat(seed,1,147456);
N = size(x, 1);
fprintf('.');


% ------------------------> compute correlation

sx = sum(x,1);			fprintf('.');
sy = sum(y,1);			fprintf('.');
sx2 = sum(x.*x, 1);		fprintf('.');
sy2 = sum(y.*y, 1);		fprintf('.');
sxy = sum(x.*y, 1);		fprintf('.');

r = (N*sxy - sx.*sy)./sqrt((N*sx2 - sx.*sx).*(N*sy2 - sy.*sy));		fprintf('.');

% ------------------------> compute Fz and significance

Fz = 0.5*log((1+r)./(1-r));			fprintf('.');
Z = Fz/(1/sqrt(N-3));				fprintf('. done.');


% ======================================================
% 	----> writing images

fprintf('\n... writing images\n');

fc_Save4DFP(strcat(target, '_r.4dfp.img'),r);
fc_Save4DFP(strcat(target, '_Fz.4dfp.img'),Fz);
fc_Save4DFP(strcat(target, '_Z.4dfp.img'),Z);

fprintf('Done!\n');


% ======================================================
% 	----> GLM function

function Y = getResiduals(file, nf)

% 	----> read image file

Y = fc_Read4DFPn(file, nf);			fprintf('(r');

% 	----> Extract nuisance timeseries

TS = fc_ExtractNuisanceTS(Y);		fprintf('e');

% 	----> Omit first frames

omit = 5;
na = nf-omit;

% 	----> prepare GLM parameters

pl = zeros(na,1);
for n = 1:na
	pl(n)= (n-1)/(na-1);
end
pl = pl-0.5;

p2 = zeros(na,1);
for n = 1:na
	p2(n) = pl(n)*pl(n);
end 
p2 = (p2*4)-0.5;

p3 = zeros(na,1);
for n = 1:na
	p3(n) = pl(n)*pl(n)*pl(n);
end 
p3 = p3 - (min(p3)-0);
p3 = p3*16;
p3 = p3 - (pl+0.5)*3 - 0.5;

X = [ones(na,1) pl p2 p3 TS.V(omit+1:nf) TS.WM(omit+1:nf) TS.WB(omit+1:nf)];


% 	----> do GLM

yY = Y(:,omit+1:nf)';								fprintf('i');

xKXs   = spm_sp('Set', X); 			fprintf('s');
xKXs.X = full(xKXs.X);
pKX    = spm_sp('x-',xKXs); 		fprintf('-');

%beta  = xX.pKX*KWY;                  
res = spm_sp('r', xKXs, yY)';		fprintf('r) ');
Y(:,omit+1:nf) = res;

