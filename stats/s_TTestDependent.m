function [TS] = s_TTestDependent(in1, in2, target, precision)

%	
%	Compute t-test for two depentend samples
%	conc - input files
%	target - output root filename
%	

if nargin < 4
	precision = 'double';
end

root = strrep(target, '.4dfp.img', '');

% ======================================================
% 	----> read files

fprintf('Computing dependent t-test [%s - %s]... reading data ', in1, in2);
img1 = reshape(g_Read4DFP(in1, precision), 48*48*64, []);				fprintf('.');
img2 = reshape(g_Read4DFP(in2, precision), 48*48*64, []);				fprintf('.');

% ======================================================
% 	----> compute t-test

fprintf(' computing ');
[h, p] = ttest(img1, img2, 0.05, 'both', 2);					fprintf('.');
%Z = ptoz(1-(p/2),0,1);											fprintf('.');
Z = icdf('Normal', (1-(p/2)), 0, 1);							fprintf('.');
d = mean(img1,2) - mean(img2,2);								fprintf('.');
Z = Z .* sign (d);												fprintf('.');

% ======================================================
% 	----> save results

fprintf(' saving ');
g_Save4DFP(strcat(root, '_Z.4dfp.img'),Z);					fprintf('.');
g_Save4DFP(strcat(root, '_dFz.4dfp.img'),d);					fprintf('.');
g_Save4DFP(strcat(root, '_dFz_all.4dfp.img'),img1-img2);					fprintf('.');
fprintf(' done!\n');


