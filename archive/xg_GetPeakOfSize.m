function [roi] = g_GetPeakOfSize(in, nroi, sspaces)

%	
%	g_GetPeakOfSize
%
%	v1.0 © Grega Repovš, 29. Feb 2008
%
%	Finds the higest magnitude cluster of contiguous voxels and returns mask of selected voxels.
%
%	Arguments
%	- in 	: 3D matrix of values
%	- nroi	: requested cluster size
%	- sspace: optional matrix with definition of subspaces to search
%
%	Returns
%	- roi	: a matrix of selected voxels for each of the specified subspaces
%
%	Note
%	- includes positive voxels only
%		

%  ---- initializing

if nargin == 3
	sscodes = unique(sspaces(sspaces > 0));
	nss = length(sscodes);
else
	sspaces = ones(size(in));
	sscodes = 1;
	nss = 1;
end

stats = regionprops(sspaces, 'BoundingBox');
bb = reshape([stats.BoundingBox], 6,[])';

x1 = ceil(bb(:,1));
y1 = ceil(bb(:,2));
z1 = ceil(bb(:,3));
x2 = x1 + bb(:,4) -1;
y2 = y1 + bb(:,5) -1;
z2 = z1 + bb(:,6) -1;

roi = zeros(size(in));


% ---- starting subspaces loop

for ss = 1:nss
	ssc = sscodes(ss);

	ssin = in;
	ssin(sspaces ~= ssc) = 0;
	ssin = ssin(y1(ssc):y2(ssc), x1(ssc):x2(ssc), z1(ssc):z2(ssc));
	ssroi = zeros(size(ssin));

	svox = sort(reshape(ssin, [], 1), 1, 'descend');
	nrel = sum(svox>0);
	nvox = size(svox,1);

	if nrel < nroi
		start = nrel;
	else
		start = nroi;
	end
	
	done = false;
	for n = start:nrel
	
		% get a list of clusters with voxels above threshold
	
		[L num] = bwlabeln(ssin >= svox(n), 6);
		stats = regionprops(L, 'Area');
		areas = [stats.Area];	
	
		% get a list of clusters of requested size
	
		targets = find(areas >= nroi);  		
	
		% if target clusters exist pick one with the highest value
	
		ntargets = length(targets);
	
		if (ntargets > 0)
			mmax = 1;
			if (ntargets > 1)
				vmax = 0;
				for m = 1:ntargets
					cmax = mean(mean(mean(ssin(L == targets(m)))));
					if (cmax > vmax)
						vmax = cmax;
						vmax = m;
					end
				end
			end	
			ssroi(L == targets(mmax)) = ssc; 
			done = true;	
			break
		end
	end


	% --- this is the case when there are no clusters of non-zero values of requested size - we're returning the biggest

	if ~done
		msize = max(areas);
		targets = find(areas == msize);

		ntargets = length(targets);

		mmax = 1;
		if (ntargets > 1)
			vmax = 0;
			for m = 1:ntargets
				cmax = mean(mean(mean(ssin(L == targets(m)))));
				if (cmax > vmax)
					vmax = cmax;
					vmax = m;
				end
			end
		end	
		ssroi(L == targets(mmax)) = ssc;
	end
	
	% --- add voxels tom the roi mask

	roi(y1(ssc):y2(ssc), x1(ssc):x2(ssc), z1(ssc):z2(ssc)) = roi(y1(ssc):y2(ssc), x1(ssc):x2(ssc), z1(ssc):z2(ssc)) + ssroi;

end


