function [TS] = s_TTestZeroNonzero(conc, target, dtype)

%
%   function [TS] = s_TTestZeroNonzero(conc, target, dtype)
%	
%	Computes t-test against 0
%	conc - input files
%	target - output root filename
%	

if nargin < 3
	dtype = 'double';
end

target = strrep(target, '.img', '');
target = strrep(target, '.conc', '');
target = strrep(target, '.4dfp', '');


% ======================================================
% 	----> read files

fprintf('Computing t-test against 0 [%s] ... reading data ', conc);
img = reshape(g_Read4DFP(conc, dtype), 48*48*64, []);				fprintf('.');


% ======================================================
%   ----> compute mean

fprintf(' computing mean');

ok = sum(img~=0, 2);                                            fprintf('.');
m = sum(img, 2)./ok;                                            fprintf('.');

% 	----> compute t-test

fprintf(' ttest');
img(img==0) = NaN;
[h, p] = ttest(img, 0, 0.05, 'both', 2);						fprintf('.');
                                                               
%Z = fc_ptoz(1-(p/2),0,1);										fprintf('.');
Z = icdf('Normal', (1-(p/2)), 0, 1);							fprintf('.');
Z = Z .* sign(m);	            								fprintf('.');

% ======================================================
% 	----> save results

fprintf(' saving ');
g_Save4DFP(strcat(target, '_Z.4dfp.img'), Z);					fprintf('.');
g_Save4DFP(strcat(target, '_MFz.4dfp.img'),m);		fprintf('.');
fprintf(' done!\n');


