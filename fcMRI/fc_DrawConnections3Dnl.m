function [niz] = fc_DrawConnections3Dnl(roi, m, p, t)

%	
%	Takes two sets of ROI timeseries and computes correlations and partial correlations. 
%	It returns the original structure plus correlations, partial correlations and samples
%
%	niz.timeseries 	= structure that holds event x timeseries x region datablock
%	frames			= which frames of the timeseries to take into computation
%	nsamples		= how many samples to draw
%
%	outputs niz.corr.
%		bsr			= sample x correlation matrix
%		bspr		= sample x partial correlation matrix
%	

%   --- set variables

nregions = size(roi,1);

fim = fopen('test.trk','w');
i = fwrite(fim, [48 64 48], 'int');
i = fwrite(fim, [3 3 3], 'float');

c = 1;
for i = 1:nregions-1
	for j = i+1:nregions
		if (p(c)<t)
			if (m(c) > 0)
				color = ['green'];
			else
				color = ['red'];
			end			
						
			x = roi(j, 1)*3;
			y = roi(j, 2)*3; 
			z = roi(j, 3)*3;
			
			xs = (roi(i,1) - roi(j,1))*3/200;
			ys = (roi(i,2) - roi(j,2))*3/200;
			zs = (roi(i,3) - roi(j,3))*3/200;
			
			x = fwrite(fim, [200], 'int');
			for n = 1:200
				x = fwrite(fim, [x+n*xs y+n*ys z+n*zs], 'float');
			end
					
		end
		c = c + 1;
	end
end

i = fwrite(fim, [0], 'int');
fclose(fim);