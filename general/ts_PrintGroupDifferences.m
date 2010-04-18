function [] = ts_PrintGroupDifferences(filename)

%	
%	ts_PrintGroupDifferences
%
%	Prints group mean correlations and differences by individual connections
%	
%	filename   	- path to the file containing the gdiff data structure
%
%   Created by Grega Repovs 2008-07-31
%


load(filename);
nroi = length(gdiff.regions);
ncon = nroi*(nroi-1)/2;

c = 0;
select = [];
for i = 1:nroi-1
	for j = i+1:nroi
		select = [select nroi*(i-1)+j];
		c = c + 1;
		con{c} = [gdiff.regions{i} ' - ' gdiff.regions{j}];
	end
end

g1r = gdiff.group1.data.group_r(select)';
g1p = gdiff.group1.data.group_p(select)';
g2r = gdiff.group2.data.group_r(select)';
g2p = gdiff.group2.data.group_p(select)';
gdp = gdiff.diff_p(select)';

fprintf('\n==================================================================');
fprintf('\nPrinting group comparison based on %s\n\n', filename);

fprintf('\nConnection\tGroup1 r\tGroup2 r\t\tGroup1 p\tGroup2 p\t\tDiff p\n');

for n = 1:ncon
    fprintf('%s\t%.3f\t%.3f\t\t%.4f\t%.4f\t\t%.4f\n', con{n}, g1r(n), g2r(n), g1p(n), g2p(n), gdp(n));
end

fprintf('\n\n');
