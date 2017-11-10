function [TS] = fc_Preprocess(conc, ftarget, ctarget, omit, doIt, regress, task, efile, TR)

%	Written by Grega Repovš, 29.10.2007
%
%	Regression of events - 15.11.07
%
%	!!! add more options -> TR, bandpass values ...
%
%
%
%	
%	Does the preprocesing for the conc bold runs
%	Saves images in ftarget folder
%	Saves new conc files in the ctarget folder
%	Omits "omit" number of start frames from bandpassing and GLM
%	Does the steps specified in "do":
%		s - smooth
%		h - highpass
%		r - regress out nuisance
%		c - save coefficients in _coeff file
%		p - saves png image files of nusance ROI mask
%       l - lowpass
%
%	In regression it uses the regressors specified in "regress":
%		m - motion
%		v - ventricles
%		wm - white matter
%		wb - whole brain
%		d - first derivative
%		t - task 
%		e - events
%
%	It prepends task matrix to GLM regression 
%	It reads event data from efile fidl event file
%

if nargin < 9
	TR = '2.5';
end


fprintf('\nRunning preproces script v0.8.2\n');

% ======================================================
% 	----> prepare paths

ofiles = g_ReadConcFile(conc);
if ftarget(1) ~= '/'
	ftarget = strcat(pwd, '/', ftarget, '/');
end
if ctarget(1) ~= '/'
	ctarget = strcat(pwd, '/', ctarget, '/');
end

fprintf('\nWill be processing files:\n')
for n = 1:length(ofiles)
	path = strread(char(ofiles{n}), '%s', 'delimiter', '/');
	oname{n} = char(path(length(path)));
	fprintf('... %s\n', char(oname{n}));
	sname{n} = strrep(char(oname{n}), '.4dfp.img', '_g7.4dfp.img');
	hname{n} = strrep(char(sname{n}), '.4dfp.img', '_hpss.4dfp.img');
	rname{n} = strrep(char(hname{n}), '.4dfp.img', strcat('_res-', regress, '.4dfp.img'));
	cname{n} = strrep(char(rname{n}), '.4dfp.img', strcat('_coeff-', regress, '.4dfp.img'));
	lname{n} = strrep(char(rname{n}), '.4dfp.img', strcat('_bpss', '.4dfp.img'));
	sfiles{n} = strcat(ftarget, char(sname{n}));
	hfiles{n} = strcat(ftarget, char(hname{n}));
	rfiles{n} = strcat(ftarget, char(rname{n}));
	lfiles{n} = strcat(ftarget, char(lname{n}));
	cfiles{n} = strcat(ftarget, char(cname{n}));
end

path = strread(conc, '%s', 'delimiter', '/');
concname = char(path(length(path)));
sconcname = strrep(concname, '.conc', '_g7.conc');
hconcname = strrep(sconcname, '.conc', '_hpss.conc');
rconcname = strrep(hconcname, '.conc', strcat('_res-', regress, '.conc'));
cconcname = strrep(rconcname, '.conc', '_coeff.conc');
lconcname = strrep(rconcname, '.conc', '_bpss.conc');

% ======================================================
% 	----> smooth images

if strfind(doIt, 's')
	for n = 1:length(ofiles)
	    fprintf('... Running g_Smooth3D on %s ', char(ofiles{n}));
	    img = g_Read4DFP(char(ofiles{n}), 'single');
	    img = g_Smooth3D(img, 2);
	    fprintf(' ... saving');
	    g_Save4DFP(sfiles{n}, img);
	    img = [];
	    fprintf(' ... done!\n');
	end
    g_SaveConcFile(strcat(ctarget,sconcname), sfiles);
end

% ======================================================
% 	----> highpass filter images

if strfind(doIt, 'h')
	for n = 1:length(sfiles)
	    fprintf('... Running highpass bandpass_4dfp with %s ', char(sfiles{n}));
		[status result] = system(['bandpass_4dfp ' char(sfiles{n}) ' ' TR ' -bl.009 -n' num2str(omit) ' -ol4 -E -thpss ']);
		if ~status
		    [pathstr, name, ext, versn] = fileparts(char(sfiles{n}));
		    if ~strcmp([pathstr '/'], ftarget)
		        fprintf(' ... moving file');
    	        tomove = strrep(hname{n},'.img', '.*');
    	        system(['mv -f ' pathstr '/' tomove ' ' ftarget]);
	        end
	        fprintf('... done!\n');
	    else
		    fprintf('... there was an error, further processing aborted!\n %s: ', result);
		    break;
	    end
	end
    if ~status
	    g_SaveConcFile(strcat(ctarget,hconcname), hfiles);
    else
	    return;
    end
end


% ======================================================
% 	----> do GLM removal of nuisance regressors
%

if strfind(doIt, 'r')

	fprintf('\nRunning nuisance signal removal (%s)\n', hconcname);

	for ni = 1:length(hfiles)

		fprintf('... bold %d ', ni);

		%	----> create regressors
	
		ifh = g_ReadIFH(strrep(char(hfiles{ni}), '.img', '.ifh'));
		nf = ifh.frames; 

		% 	----> read image file

		Y = g_Read4DFPn(char(hfiles{ni}), nf);			fprintf('read');

		% 	----> Extract nuisance timeseries

		if (~isempty(strfind(regress, 'v')) | ~isempty(strfind(regress, 'wm')) | ~isempty(strfind(regress, 'wb')))
			if strfind(doIt, 'p')
				TS = fc_ExtractNuisanceTS(Y, char(ofiles{ni}), ftarget, regress);		fprintf(', nuisance timeseries extracted');
			else
				TS = fc_ExtractNuisanceTS(Y, char(ofiles{ni}), false, regress);		fprintf(', nuisance timeseries extracted');
			end
		end

		% 	----> prepare trend parameters

		na = nf-omit;
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

		% 	----> get movement data

		if strfind(regress, 'm')
			md = ReadMovFile(char(ofiles{ni}), nf);
		end

		% 	----> put together nuisances

		nuisance = [];
	
		if strfind(regress, 'm')
			nuisance = [nuisance md];
		end
	
		if strfind(regress, 'v')
			nuisance = [nuisance TS.V];
		end
	
		if strfind(regress, 'wm')
			nuisance = [nuisance TS.WM];
		end
	
		if strfind(regress, 'wb')
			nuisance = [nuisance TS.WB];
		end
	
		% 	----> if requested, get first derivatives

		if strfind(regress, 'd')
			d = [zeros(1,size(nuisance,2));diff(nuisance)];
			nuisance = [nuisance d];
		end

		% 	----> put all regressors together

		if strfind(regress, 't')
			X = [task(omit+1:nf,:) ones(na,1) pl p2 p3 nuisance(omit+1:nf,:)];
		else
			X = [ones(na,1) pl p2 p3 nuisance(omit+1:nf,:)];
		end

		% 	----> do GLM

		fprintf(', GLM: ');

		yY = Y(:,omit+1:nf)';				fprintf('data');

		xKXs   = spm_sp('Set', X); 			fprintf(', space');
		xKXs.X = full(xKXs.X);
		
		if strfind(doIt, 'c')
			pKX   = spm_sp('x-',xKXs); 		fprintf(', inverted');
			coeff  = pKX*yY; 					fprintf(', coeff');
		end
		
		res = spm_sp('r', xKXs, yY)';		fprintf(', residuals');
		Y(:,omit+1:nf) = res;
		
		if strfind(doIt, 'c')
			g_Save4DFP(char(cfiles{ni}), coeff');
		end
		g_Save4DFP(char(rfiles{ni}), Y);	fprintf(', saved\n');
	
	end
	
	if strfind(doIt, 'c')
		g_SaveConcFile(strcat(ctarget,cconcname), cfiles);
	end
	g_SaveConcFile(strcat(ctarget,rconcname), rfiles);
end

% ======================================================
% 	----> lowpass filter images

if strfind(doIt, 'l')
	for n = 1:length(sfiles)
	    fprintf('... Running lowpass bandpass_4dfp with %s ', char(rfiles{n}));
		[status result] = system(['bandpass_4dfp ' char(rfiles{n}) ' ' TR ' -bh.08 -n' num2str(omit) ' -oh2 -E -tbpss ']);
		if ~status
		    [pathstr, name, ext, versn] = fileparts(char(rfiles{n}));
		    if ~strcmp([pathstr '/'], ftarget)
		        fprintf(' ... moving file');
    	        tomove = strrep(lname{n},'.img', '.*');
    	        system(['mv -f ' pathstr '/' tomove ' ' ftarget]);
	        end
	        fprintf('... done!\n');
	    else
		    fprintf('... there was an error, further processing aborted!\n %s: ', result);
		    break;
	    end
	end
    if ~status
	    g_SaveConcFile(strcat(ctarget,lconcname), lfiles);
    else
	    return;
    end
end




return



% ======================================================
% 	----> read movement files

function x = ReadMovFile(file, nf)

path = strread(file, '%s', 'delimiter', '/');
toreplace = char(path(length(path)-1));
file = strrep(file, toreplace, 'movement');
file = strrep(file, '.4dfp.img', '.dat');
file = strrep(file, '_atl', '');

x = zeros(nf,6);

fin = fopen(file, 'r');
s = fgetl(fin);
for n = 1:nf
	s = fgetl(fin);
	line = strread(s);
	x(n,:) = line(2:7);
end
fclose(fin);






