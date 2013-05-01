function [TS] = s_p2z4DFP(in, out, tail)

%	
%	Computes t-test against 0
%	conc - input files
%	target - output root filename
%	


if nargin < 3
	tail = 'two';
	if nargin < 2
	    out = strrep(in, '.img', '');
	    out = strrep(out, '.4dfp', '');
	    out = [out '_Z.4dfp.img'];
    end
end

% ======================================================
% 	----> read files

fprintf('Converting p-values to Z scores for [%s] ... reading data ', in);
p = reshape(g_Read4DFP(in), 48*48*64, []);				fprintf('.');


% ======================================================
% 	----> convert

fprintf(' converting ');
                                                               
%Z = fc_ptoz(1-(p/2),0,1);										fprintf('.');
Z = icdf('Normal', (1-(p/2)), 0, 1);							fprintf('.');
%Z = Z .* sign(mean(img, 2));									fprintf('.');

% ======================================================
% 	----> save results

fprintf(' saving %s', out);
g_Save4DFP(strcat(out, '_Z.4dfp.img'), Z);					fprintf('.');
%g_Save4DFP(strcat(out, '_MFz.4dfp.img'),mean(img,2));		fprintf('.');
fprintf(' done!\n');


