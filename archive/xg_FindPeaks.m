function [] = g_FindPeaks(fin, fout, t, mins, maxs)

%
%	Creates an roi file with peak regions of mins and maxs size over threshold t
%
%		

%  ---- initializing

img = fc_Read4DFP(fin);
img(img < t) = 0;
simg = sort(img, 'descend');
simg = simg(1:sum(img>=t));

img = reshape(img, 48, 64, 48);
roi = zeros(size(img));
c = 1;

work = true;

fprintf('\nStarting\n  Voxels    Areas    Small    Right\n');

while 1
	s = 1;
	[L num] = bwlabeln(img > simg(end));
	stats = regionprops(L, 'Area');
	
	areas = [stats.Area];	
	
	small = find(areas < mins);  		% list of regions smaller than mins	
	img(ismember(L, small)) = 0;		% zeroing those regions
	
	if(length(find(areas > maxs)) == 0)	% check if there are still regions too big if not, there is no need for another iteration
		work = false;
	end
	
	%areas(small) = maxs+100000;			% set small to overly big and 
	right = find((areas <= maxs) & (areas > mins));		% find the regions of the right size
	
	for n = 1:length(right)						% set the regions of the right size into the region map
		roi(ismember(L, right(n))) = c;
		c = c + 1;
	%	fprintf(' region added\n');
	end
	
	img(ismember(L, right)) = 0;		% set the image to zero for the new regions so that they are excluded from further analysis
	
	simg = simg(1:sum(sum(sum(img>simg(end)))));
	
	if length(simg) == 0
		break
	end
	
	tail = sum(simg == simg(end));
	simg = simg(1:length(simg)-tail);
	
	if length(simg) == 0
		big = find(areas > maxs);
		for n = 1:length(big)						% set the regions of the right size into the region map
			roi(ismember(L, big(n))) = c;
			c = c + 1;
		%	fprintf(' region added\n');
		end
		break
	end
			
	fprintf('%8d %8d %8d %8d\n', length(simg), length(areas), length(small), length(right));
end

fprintf('\nRegions created: %d', c-1);
fprintf('\n... Saving');
fc_Save4DFP(fout, roi);
fprintf('\n... Done.\n');

