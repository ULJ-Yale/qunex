function [out] = fc_FzCompare2(sfile, ss, tfile, ts, selection, ofile)

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
taverage = mean(timg(:,selection),2);

sdev = sqrt((1/(ss-3))+(1/(ts-3)));
diffimage = (taverage-saverage)./sdev;


fprintf(' saving...');
fc_Save4DFP(ofile,diffimage);

saverage = saverage./(1/sqrt(ss-3));
taverage = taverage./(1/sqrt(ts-3));

saveragename = strrep(sfile, 't0-15_Fz', 'average_Z');
taveragename = strrep(ofile, 'task-rest', 'task_average');

fc_Save4DFP(saveragename,saverage);
fc_Save4DFP(taveragename,taverage);

fprintf('\nDone!\n');


