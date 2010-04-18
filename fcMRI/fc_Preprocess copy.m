function [TS] = fc_Preprocess(conc, ftarget, ctarget, omit, do)

%	Written by Grega Repovš, 29.10.2007
%	
%	Does the preprocesing for the conc bold runs
%	Saves images in ftarget folder
%	Saves new conc files in the ctarget folder
%	Omits "omit" number of start frames from bandpassing and GLM
%	Does the steps specified in "do":
%		s - smooth
%		b - bandpass
%		r - regress out nuisance
%

% ======================================================
% 	----> prepare paths

ofiles = fc_ReadConcFile(conc);
if ftarget(1) ~= '/'
	ftarget = strcat(pwd, '/', ftarget, '/');
end
if ctarget(1) ~= '/'
	ctarget = strcat(pwd, '/', ctarget, '/');
end

for n = 1:length(ofiles)
	path = strread(char(ofiles{n}), '%s', 'delimiter', '/');
	oname{n} = char(path(length(path)));
	sname{n} = strrep(char(oname{n}), '.4dfp.img', '_g7.4dfp.img');
	bname{n} = strrep(char(sname{n}), '.4dfp.img', '_hpss.4dfp.img');
	rname{n} = strrep(char(bname{n}), '.4dfp.img', '_res.4dfp.img');
	sfiles{n} = strcat(ftarget, char(sname{n}));
	bfiles{n} = strcat(ftarget, char(bname{n}));
	rfiles{n} = strcat(ftarget, char(rname{n}));
end

path = strread(conc, '%s', 'delimiter', '/');
concname = char(path(length(path)));
sconcname = strrep(concname, '.conc', '_g7.conc');
bconcname = strrep(sconcname, '.conc', '_hpss.conc');
rconcname = strrep(bconcname, '.conc', '_res.conc');

% ======================================================
% 	----> smooth images

if strfind(do, 's')
	for n = 1:length(ofiles)
		system(['gauss_4dfp ' char(ofiles{n}) ' .735452 ']);
		[pathstr, name, ext, versn] = fileparts(char(ofiles{n}));
		tomove = strrep(sname{n},'.img', '.*');
		system(['mv ' pathstr '/' tomove ' ' ftarget]);
	end

	SaveConcFile(strcat(ctarget,sconcname), sfiles);
end

% ======================================================
% 	----> highpass filter images

if strfind(do, 'b')
	for n = 1:length(sfiles)
		system(['bandpass_4dfp ' char(sfiles{n}) ' 2.5 -bl.009 -n' num2str(omit) ' -ol4 -E -thpss ']);
	%	[pathstr, name, ext, versn] = fileparts(char(sfiles{n}));
	%	tomove = strrep(bname{n},'.img', '.*');
	%	system(['mv ' pathstr '/' tomove ' ' ftarget]);
	end

	SaveConcFile(strcat(ctarget,bconcname), bfiles);
end


% ======================================================
% 	----> do GLM removal of nuisance regressors
%

if strfind(do, 'r')

	fprintf('\nRunning nuisance signal removal (%s)\n', concname);

	for ni = 1:length(bfiles)
	
		fprintf('... bold %d ', ni);
	
		%	----> create regressors
		
		ifh = fc_ReadIFH(strrep(char(bfiles{ni}), '.img', '.ifh'));
		nf = ifh.frames; 
	
		% 	----> read image file

		Y = fc_Read4DFPn(char(bfiles{ni}), nf);			fprintf('read');

		% 	----> Extract nuisance timeseries

		TS = fc_ExtractNuisanceTS(Y, char(ofiles{ni}), ftarget);		fprintf(', nuisance timeseries extracted');
	
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
	
		md = ReadMovFile(char(ofiles{ni}), nf);
	
		% 	----> get first derivatives
	
		nuisance = [md TS.V TS.WM TS.WB];
	
		d = [zeros(1,size(nuisance,2));diff(nuisance)];
		nuisance = [nuisance d];
	
		% 	----> put all regressors together
	
		X = [ones(na,1) pl p2 p3 nuisance(omit+1:nf,:)];
	
		% 	----> do GLM

		fprintf(', GLM: ');

		yY = Y(:,omit+1:nf)';				fprintf('data');

		xKXs   = spm_sp('Set', X); 			fprintf(', space');
		xKXs.X = full(xKXs.X);
		pKX    = spm_sp('x-',xKXs); 		fprintf(', inverted');

		%beta  = xX.pKX*KWY;                  
		res = spm_sp('r', xKXs, yY)';		fprintf(', residuals');
		Y(:,omit+1:nf) = res;
	
		fc_Save4DFP(char(rfiles{ni}), Y);	fprintf(', saved\n');
		
	end

	SaveConcFile(strcat(ctarget,rconcname), rfiles);
end





return


% ======================================================
% 	----> save conc files

function x = SaveConcFile(file, files)

fout = fopen(file,'w');
fprintf(fout, '    number_of_files: %d\n', length(files));
for n = 1:length(files)
	fprintf(fout, '               file:%s\n', files{n});
end
fclose(fout);


% ======================================================
% 	----> read movement files

function x = ReadMovFile(file, nf)

path = strread(file, '%s', 'delimiter', '/');
toreplace = char(path(length(path)-1));
file = strrep(file, toreplace, 'movement');
file = strrep(file, '_atl.4dfp.img', '.dat');

x = zeros(nf,6);

fin = fopen(file, 'r');
s = fgetl(fin);
for n = 1:nf
	s = fgetl(fin);
	line = strread(s);
	x(n,:) = line(2:7);
end
fclose(fin);






