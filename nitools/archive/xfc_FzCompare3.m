function [out] = fc_FzCompare3(sfile, tfile, ofile)

%	
%	Compares two correlation maps and outputs map of differences
%	sfile 	- map to compare to
%	tfile	- map to compare
%   ofile  	- output file name
%	
%	! number of samples used to compute correlations are read form each corresponding ifh file
%	

%  ----- read images and ifh data

fprintf('\nReading...');

simg = fc_Read4DFP(sfile);
timg = fc_Read4DFP(tfile);

sifhfile = strrep(sfile, '.img', '.ifh');
tifhfile = strrep(tfile, '.img', '.ifh');

sifh = fc_ReadIFH(sifhfile);
tifh = fc_ReadIFH(tifhfile);

ss = sifh.samples;
ts = tifh.samples;

%  ----- do it

fprintf(' computing...');

sddiff 	= sqrt(1/(ss-3)+1/(ts-3));
Fzdiff 	= (timg - simg);
Zdiff	= Fzdiff./sddiff;

fprintf(' saving...');

Zofile = strrep(ofile, '.4dfp.img', '_Z.4dfp.img');
Fzofile = strrep(ofile, '.4dfp.img', '_Fz.4dfp.img');

fc_Save4DFP(Zofile,Zdiff);
fc_Save4DFP(Fzofile,Fzdiff);


fprintf(' done!\n');


