function [] = g_FindPeaks_v2(fin, fout, t, mins, maxs)

%
%	Creates an roi file with peak regions of mins and maxs size over threshold t
%
%		

%  ---- initializing

img = fc_Read4DFP(fin);
img(img < t) = 0;
simg = sort(unique(img));

img = reshape(img, 48, 64, 48);
roi = zeros(size(img));
c = 1;

work = true;

fprintf('\nStarting\n      Th   Unique   Voxels    Areas    Small    Right\n                 ');

last = 0;
while work
	
	report = false;
	
	if last == simg(1)
		simg = simg(2:end);
	end
	last = simg(1);
	
	s = 1;
	[L num] = bwlabeln(img >= simg(1));
	stats = regionprops(L, 'Area');
	
	areas = [stats.Area];	
	
	small = find(areas < mins);  		% list of regions smaller than mins	
	img(ismember(L, small)) = 0;		% zeroing those regions
	if (length(small) > 0)
		report = true;
	end
	
	if(length(find(areas > maxs)) == 0)	% check if there are still regions too big if not, there is no need for another iteration
		work = false;
	end
	
	%areas(small) = maxs+100000;			% set small to overly big and 
	right = find((areas <= maxs) & (areas >= mins));		% find the regions of the right size
	
	for n = 1:length(right)						% set the regions of the right size into the region map
		roi(ismember(L, right(n))) = c;
		c = c + 1;
		report = true;
	%	fprintf(' region added\n');
	end
	
	img(ismember(L, right)) = 0;		% set the image to zero for the new regions so that they are excluded from further analysis
	
	% simg = simg(1:sum(sum(sum(img>simg(end)))));
	
	if (report)	
		timg = sort(unique(img(img>0)));
	
		if(length(timg)<length(simg))
			simg = timg;
		end
	end

	if length(simg) == 0
		break
	end
	
	if length(simg) == 1
		big = find(areas > maxs);
		for n = 1:length(big)						% set the regions of the right size into the region map
			roi(ismember(L, big(n))) = c;
			c = c + 1;
		%	fprintf(' region added\n');
		end
		break
	end
	
	if (report)	
		fprintf('\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b%8.4f %8d %8d %8d %8d %8d\n                 ', simg(1), length(simg), sum(areas), length(areas), length(small), length(right));
	else
		fprintf('\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b%8.4f %8d', simg(1), length(simg));
	end
end

fprintf('\nRegions created: %d', c-1);
fprintf('\n... Saving');
fc_Save4DFP(fout, roi);
fprintf('\n... Done.\n');

