function [] = fc_ComputeGroupDifference(group1file, group2file, targetf)

%	
%	fc_ComputeGroupDifference
%
%	signed p values and mean differences between groups are computed
%	
%	group1file   	- path to the file containing the data structure for patients
%   group2file		- path to the file containing the data structure for controls
%	targetf		- save name
%
%   Created by Joshua J Kim on 2008-07-29.
%   Small changes and additions Grega Repovs 2008-07-31
%

fprintf('\n\nComputing group differences ...');

group1 = load(group1file);
group2 = load(group2file);

[h, gdiff.diff_p] = ttest2(group1.data.Fz, group2.data.Fz, [], 'both', 'equal', 3);

gdiff.group1.data = group1.data;
gdiff.group1.file = group1file;

gdiff.group2.data = group2.data;
gdiff.group2.file = group2file;

gdiff.regions = group1.data.regions;

gdiff.diff_Fz = group1.data.group_Fz - group2.data.group_Fz;
gdiff.diff_p = gdiff.diff_p.*sign(gdiff.diff_Fz);

fprintf('\n\nSaving ...');

save(targetf, 'gdiff')

fprintf('\n\n FINISHED!\n\n');