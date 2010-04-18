function [TS] = s_TTestZero(conc, target, dtype)

%	
%	Computes t-test against 0
%	conc - input files
%	target - output root filename
%	

if nargin < 3
	dtype = 'double';
end
root = strrep(target, '.4dfp.img', '');

% ======================================================
% 	----> read files

fprintf('Computing t-test against 0 [%s] ... reading data ', conc);
img = reshape(g_Read4DFP(conc, dtype), 48*48*64, []);				fprintf('.');


% ======================================================
% 	----> compute t-test

fprintf(' computing ');
[h, p] = ttest(img, 0, 0.05, 'both', 2);						fprintf('.');
                                                               
%Z = fc_ptoz(1-(p/2),0,1);										fprintf('.');
Z = icdf('Normal', (1-(p/2)), 0, 1);							fprintf('.');
Z = Z .* sign(mean(img, 2));									fprintf('.');

% ======================================================
% 	----> save results

fprintf(' saving ');
g_Save4DFP([root '_Z.4dfp.img'], Z);					fprintf('.');
g_Save4DFP([root '_MFz.4dfp.img'],mean(img,2));		    fprintf('.');
fprintf(' done!\n');


