function [] = g_Conjunction4dfp(imgf, maskf, method, effect, q, data)

%
%	g_Conjunction4dfp
%
%	Reads image file, computes conjunction using g_Conjunction and saves results.
%
%	imgf	- input file, a 4dfp z-score image file of concatenated individual files
%	maskf	- optional mask image (4dfp image) 
%		: missing or empty -> takes Avi 333 brain mask
%		: 0 -> takes all non-zero voxels
%		: 1 -> takes all voxels
%	
%	for the rest of arguments see g_Conjunction.m
%
%	saves	 
%		: '_Conj_p'   -> conjunction results, zscores for u = 1 to u = n
%		: '_Conj_FDR' -> above thresholded with FDR
%		: '_Conj_c'   -> image of frequency of passing threshold
%	
%	Grega Repovš
%	v2.0  27.2.2008

% parsing arguments

if nargin < 6
	data = [];
	if nargin < 5
		q = 0.05;
		if nargin < 4
			effect = [];
			if nargin < 3
				method = [];
				if nargin < 2
					maskf = [];
				end
			end
		end
	end
end

%  ---- initializing

qs = num2str(q, '%1.3f');
imgpf = strrep(imgf, '.4dfp.img', '_Conj_p.4dfp.img');
imgtf = strrep(imgf, '.4dfp.img', ['_Conj_FDR' qs '.4dfp.img']);
imgcf = strrep(imgf, '.4dfp.img', '_Conj_c.4dfp.img');

fprintf('\n\nComputing conjunction with file %s, thresholding with FDR q=%.4f\n', imgf, q);

%  ---- reading image, computing conjunction

fprintf('... reading image ');
img = g_Read4DFP(imgf);
nvox = 48*48*64;
nsub = size(img,1)/nvox;
fprintf(' volumes: %d ', nsub);

img = reshape(img, nvox, nsub);
fprintf('... done\n');


%  ---- Creating image mask and masking image

fprintf('... masking image ');

if isempty(maskf)
	maskf = '/home/iac8/grepovs/ConMatlab/general/Nimage.4dfp.img';
end

if max(size(maskf)) == 1
	if maskf == 1
		mask = ones(size(img));
		mask = mask == 1;
	elseif maskf == 0
		mask = img ~= 0;
	end
else	
	mask = g_Read4DFP(maskf);
	mask = mask > 0;
end

mask(isnan(mask)) = 0;

mimg = img(mask,:);

fprintf('... done\n');

%  ---- Coing conjunction

fprintf('... starting conjunction analysis\n');
[mzp, mzt, mzc] = g_Conjunction(mimg, method, effect, q, data);
fprintf('... done\n');

%  ---- saving results

fprintf('... saving results ');

out = zeros(nvox,nsub);
out(mask,:) = mzp;
g_Save4DFP(imgpf, out);			fprintf('.');

out = zeros(nvox,nsub);
out(mask,:) = mzt;
g_Save4DFP(imgtf, out);			fprintf('.');

out = zeros(nvox,1);
out(mask) = mzc;
g_Save4DFP(imgcf, out);			fprintf('.');


fprintf(' done.\n\n');





