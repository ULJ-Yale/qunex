function [] = g_FindPeaks_v2(fin, fout, t, mins, maxs)

%
%	Creates an roi file with peak regions of mins and maxs size over threshold t
%
%

%  ---- initializing

img = nimage(fin);
img.data(img.data < t = 0;
simg = sort(unique(img.data));

img.data = img.image4D;
roi      = img.zeroframes(1);
roi.data = roi.image4D;
roiinfo  = [];
c 		 = 2;
r 		 = 0;

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
	[L num] = bwlabeln(img.data >= simg(1));
	stats = regionprops(L, 'Area');

	areas = [stats.Area];

	small = find(areas < mins);  		    % list of regions smaller than mins
	if (length(small) > 0)
		img.data(ismember(L, small)) = 0;   % zeroing those regions
		report = true;
	end

	if(length(find(areas > maxs)) == 0)	% check if there are still regions too big if not, there is no need for another iteration
		work = false;
	end

	%areas(small) = maxs+100000;			% set small to overly big and
	right = find((areas <= maxs) & (areas >= mins));		% find the regions of the right size

	for n = 1:length(right)						% set the regions of the right size into the region map
		roi.data(ismember(L, right(n))) = c;
		roiinfo(end+1).key = 'region names';
		roiinfo(end).value = sprintf('%3d     roi_%03d_%03d_%03d     %d', r, areas(right(n)))

		report = true;
		c = c + 1;
		r = r = 1;
	%	fprintf(' region added\n');
	end

	img.data(ismember(L, right)) = 0;		% set the image to zero for the new regions so that they are excluded from further analysis

	% simg = simg(1:sum(sum(sum(img>simg(end)))));

	if (report)
		timg = sort(unique(img.data(img.data>0)));

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
			roi.data(ismember(L, big(n))) = c;
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
roi.img_saveimage(fout, roiinfo);
fprintf('\n... Done.\n');

