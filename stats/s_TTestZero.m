function [TS] = s_TTestZero(conc, target, dtype)

%	
%	Computes t-test against 0
%	conc - input files
%	target - output root filename
%	

if nargin < 3
	dtype = 'single';
end


% ======================================================
% 	----> read files

fprintf('Computing t-test against 0 [%s] ... reading data ', conc);
img = gmrimage(conc, dtype);                                fprintf('.');
img.data = img.image2D;		
m = img.zeroframes(1);
Z = img.zeroframes(1);


% ======================================================
% 	----> compute t-test

fprintf(' computing ');
m.data = mean(img.data, 2);					                    fprintf('.');
[h, p] = ttest(img.data, 0, 0.05, 'both', 2);					fprintf('.');
                                                               
%Z = fc_ptoz(1-(p/2),0,1);										fprintf('.');
p = icdf('Normal', (1-(p/2)), 0, 1);							fprintf('.');
Z.data = p .* sign(m.data);								        fprintf('.');

% ======================================================
% 	----> save results

fprintf(' saving ');
Z.mri_saveimage([Z.rootfilename 'Z'])                   fprintf('.');
m.mri_saveimage([m.rootfilename '_M'])                   fprintf('.');
fprintf(' done!\n');


