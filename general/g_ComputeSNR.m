function [] = g_ComputeSNR(filename, slice)

%function [] = g_ComputeSNR(filename, slice)
%	
%   Computes SNR for the given image.
%
%   Input
%       - filename: the filename of the image
%       - slice:    the slice to compute over
%		

%  ---- initializing

img = gmrimage(filename);
img.data = img.image4D;

m = squeeze(mean(mean(img.data,1),2));
sd = std(m,0,2);
m = mean(m,2);
snr = m./sd;

f = subplot(1,2,1);
plot(snr);
f = subplot(1,2,2);
boxplot(snr);
print(f, '-noui', '-dpng', [img.rootfilename '_SNR.png']);

