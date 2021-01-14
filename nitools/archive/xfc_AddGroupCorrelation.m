function [] = fc_AddGroupCorrelation(fname)

%	
%%	fc_AddGroupCorrelation
%
%	r, Fz, p, group p, mean group Fz, and mean group correlations are added to the input data structure
%	
%	fname   	- path to the file containing the original data structure
%
% 	Created by Joshua J Kim on 2008-07-29.
%
%   Small changes and additions Grega Repovs 2008-07-31
%
%

fprintf('\n\nAdding group correlations ...');

file = load(fname);

nsub = length(file.data.ts);
nroi = length(file.data.regions);

file.data.r = zeros(nroi,nroi,nsub);
file.data.p = zeros(nroi,nroi,nsub);

for s = 1:nsub
	[file.data.r(:,:,s) file.data.p(:,:,s)] = corr(file.data.ts{s});
end

file.data.Fz = fc_Fisher(file.data.r);

[h, file.data.group_p] = ttest(file.data.Fz, 0, [], 'both', 3);

file.data.group_Fz = mean(file.data.Fz, 3);
file.data.group_r = fc_FisherInv(file.data.group_Fz);

fprintf('\n\nSaving ...');

data = file.data;

save(strrep(fname,'.mat', '_groupcorr'), 'data');

fprintf('\n\n FINISHED!\n\n');
