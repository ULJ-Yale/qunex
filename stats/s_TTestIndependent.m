function [TS] = s_TTestIndependent(in1, in2, target, precision)

%	
%	Compute t-test against 0
%	in - input files
%	target - output root filename
%	precision to be used in computing ('single' or 'double')
%


if nargin < 4
	precision = 'double';
end
root = strrep(target, '.4dfp.img', '');

% ======================================================
% 	----> read files

fprintf('Computing independent ttest [%s - %s] ... reading data ', in1, in2);
img1 = reshape(g_Read4DFP(in1, precision), 48*48*64, []);		fprintf('.');
img2 = reshape(g_Read4DFP(in2, precision), 48*48*64, []);		fprintf('.');
fprintf(' done!');

% ======================================================
% 	----> compute t-test

fprintf(' computing ');
[h, p] = ttest2(img1, img2, 0.05, 'both', 'equal', 2);			fprintf('.');
Z = icdf('Normal', (1-(p/2)), 0, 1);							fprintf('.');
d = mean(img1,2) - mean(img2,2);								fprintf('.');
Z = Z .* sign (d);												fprintf('.');

% ======================================================
% 	----> save results

fprintf(' saving ');
g_Save4DFP([root '_Z.4dfp.img'],Z);		fprintf('.');
g_Save4DFP([root '_dFz.4dfp.img'],d);		fprintf('.');
fprintf(' done!\n');



