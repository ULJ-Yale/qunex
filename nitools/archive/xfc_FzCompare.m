function [out] = fc_FzCompare(sfile, ss, tfile, ts, ofile)

%	
%	
%	
%	
%	
%	
%	
%	
%	

%  ----- read images

fprintf('\nReading...');

simg = fc_Read4DFP(sfile);
timg = fc_Read4DFP(tfile);

simg = reshape(simg, 48*48*64, []);
timg = reshape(timg, 48*48*64, []);

snum = size(simg, 2);
tnum = size(timg, 2);

%  ----- do it

fprintf(' computing...');

saverage = mean(simg, 2);
saverage = repmat(saverage, 1, snum);
sdev = sqrt((1/(ss-3))+(1/(ts-3)));

diffimage = (timg-saverage)./sdev;


fprintf(' saving...');
fc_Save4DFP(ofile,diffimage);

saverage = saverage(:,1);
saverage = saverage./(1/sqrt(ss-3));
averagename = strrep(sfile, 't0-15_Fz', 'average_Z');
fc_Save4DFP(averagename,saverage);

fprintf('\nDone!\n');


