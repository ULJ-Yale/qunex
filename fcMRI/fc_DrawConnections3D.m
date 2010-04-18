function [niz] = fc_DrawConnections3D(roi, m, p, t)

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

scatter3(roi(:,1), roi(:,2), roi(:,3));

c = 1;
for i = 1:nregions-1
	for j = i+1:nregions
		if (p(c)<t)
			if (m(c) > 0)
				color = ['green'];
			else
				color = ['red'];
			end			
			line([roi(i,1) roi(j,1)], [roi(i,2) roi(j,2)], [roi(i,3) roi(j,3)],  'Color', color);			
		end
		c = c + 1;
	end
end

