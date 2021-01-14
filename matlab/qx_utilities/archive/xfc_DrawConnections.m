function [niz] = fc_DrawConnections(m, p, t, roi, cord)

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

rnames = true;
if nargin < 4
	rnames = false;
end

coords = false;
if nargin > 4
	coords = true;
end
 
%   --- set variables

nregions = ceil(sqrt(length(m)*2));
thickness = 2.;

if rnames

	if coords
		x = cord(1,1);
		y = cord(1,2);
	else
		x = 10 * n;
		y = 10 * n;
	end
	
	fprintf('\n\nDrawRegions({{"%s", %f, %f}', roi{1}, x, y);
	for n = 2:nregions
		if coords
			x = cord(n,1);
			y = cord(n,2);
		else
			x = 10 * n;
			y = 10 * n;
		end
		fprintf(', {"%s", %f, %f}', roi{n}, x, y);
	end
	fprintf('})');
else
	fprintf('\n\nDrawRegions({{"1", 10, 10}');
	for n = 2:nregions
		fprintf(', {"%d", %d0, %d0}', n, n, n );
	end
	fprintf('})');
end

c = 1;
for i = 1:nregions-1
	for j = i+1:nregions
		if (p(c)<t)
			if (m(c) > 0)
				color = ['green'];
			else
				color = ['red'];
			end			
			if (p(c) > 0)
				thickness = (1-log(p(c)))/2;
			else
				thickness = 7;
			end
			if thickness == Inf
				thickness = 7;
			end
			
			if rnames
				fprintf('\nConnectRegions("%s", "%s", %s, %f)', roi{i}, roi{j}, color, thickness);
			else
				fprintf('\nConnectRegions("%d", "%d", %s, %f)', i, j, color, thickness);			
			end
		end
		c = c + 1;
	end
end

fprintf('\n\n');
