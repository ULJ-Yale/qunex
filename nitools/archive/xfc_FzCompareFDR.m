function [out] = fc_FzCompareFDR(sfile, tfile, ofile, q1, q2)

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
bmask = fc_Read4DFP('Nimage.4dfp.img');
bmask(bmask > 1) = 1;

sifhfile = strrep(sfile, '.img', '.ifh');
tifhfile = strrep(tfile, '.img', '.ifh');

sifh = fc_ReadIFH(sifhfile);
tifh = fc_ReadIFH(tifhfile);

ss = sifh.samples;
ts = tifh.samples;


% --- getting and saving FDR thresholded p values for correlations of target image

fprintf('\n   Computing task FDR');

timgr = fc_FisherInv(timg);
timgt = abs(timgr.* sqrt((ts-2)./(1-timgr.*timgr)));
timgp = (1-cdf('t', timgt, ts))*2;

[timgp timgm] = fc_FDRThreshold(timgp, bmask, q1);

timgz = icdf('Normal', (1-timgp/2),0,1);
timgz(timgm < 1) = 0;
timgz = timgz.*sign(timg);
timgr(timgm < 1) = 0;

fprintf(' ... saving');

ztend = sprintf('_tZ_FDR_%.2f.4dfp.img', q1);
rtend = sprintf('_tr_FDR_%.2f.4dfp.img', q1);
tzfile = strrep(ofile, '.4dfp.img', ztend);
trfile = strrep(ofile, '.4dfp.img', rtend);
fc_Save4DFP(tzfile,timgz);
fc_Save4DFP(trfile,timgr);

fprintf(' ... done.');

% --- computing differences to rest

fprintf('\n   Computing difference to rest FDR');

sddiff 	= sqrt(1/(ss-3)+1/(ts-3));
Fzdiff 	= (timg - simg);
Zdiff	= Fzdiff./sddiff;

dimgp = (1-cdf('Normal', abs(Zdiff),0,1))*2;    % Z to p conversion

[dimgp dimgm] = fc_FDRThreshold(dimgp, timgm, q2);

Zdiff(dimgm < 1) = 0;
timgr(dimgm < 1) = 0;
timgz(dimgm < 1) = 0;

fprintf(' ... saving');

zdend = sprintf('_diff_Z_FDR_%.2f_%.2f.4dfp.img', q1, q2);
rtend = sprintf('_diff_tr_FDR_%.2f_%.2f.4dfp.img', q1, q2);
ztend = sprintf('_diff_tZ_FDR_%.2f_%.2f.4dfp.img', q1, q2);
dzfile = strrep(ofile, '.4dfp.img', zdend);
trfile = strrep(ofile, '.4dfp.img', rtend);
tzfile = strrep(ofile, '.4dfp.img', ztend);
fc_Save4DFP(dzfile,Zdiff);
fc_Save4DFP(trfile,timgr);
fc_Save4DFP(tzfile,timgz);

fprintf(' ... done.\n\n');




