function [] = g_PlotBoldTS(images, elements, masks, filename, skip, subjid, verbose)

%function [] = g_PlotBoldTS(images, elements, masks, filename, skip, subjid, verbose)
%
%		Creates and saves a plot of BOLD timeseries
%
%       images      - input image(s) as gmri images or paths
%		elements    - plot element specifications
%       masks       - one or multiple masks to use for extracting BOLD data
%       filename    - filename to save the plot to
%		skip		- how many frames to skip at the stat of the bold run
%		subjid		- subject code
%		verbose		- whether to be talkative
%
%   (c) Grega Repovs, 2015-10-17
%

%  ---- initializing

if nargin < 7 || isempty(verbose), verbose = false; end
if nargin < 6 || isempty(verbose), subjid = []; end
if nargin < 5 || isempty(skip), skip = 0; end
if nargin < 4 || isempty(filename), filename = 'BoldTSPlot.pdf'; end
if nargin < 3, masks = []; end
if nargin < 2, error('ERROR: Please specify images and plot elements!'); end

roi.V  = [4 5 14 15 24 43 44 72 221 701];
roi.WM = [2 7 41 46 85 192 219 703 3000:3035 4000:4035 3100:3181 4100:4181 5100:5117 5200:5217 13100:13175 14100:14175];
roi.GM = [3 8:13 16:20 26:28 42 47:56 58:60 96 97 136 137 163 164 169 176 216 218 220 222 225 226 250:255 400:439 500:508 550:558 601:628 640:679 702 1000:1035 2000:2035 1100:1104 1200:1202 1205:1207 1210:1212 1105:1181 2100:2104 2105:2181 2200:2002 2205:2207 2210:2212 7001:7020 7100:7101 8001:8014 9000:9006 9500:9506 11100:11175 12100:12175];
roi.WB = [roi.WM roi.GM];

sz.Stat = .10;
sz.GM   = 60;
sz.WM   = 30;
sz.V    = 7;
sz.WB   = 80;

sz.Fix  = 0;
sz.Var  = 0;
sz.VTop = .05;
sz.VBot = .01;
sz.IPad = .01;
sz.HPad = .05;

th.fd = 0.5;
th.dvarsme = 1.6;

dstart = skip + 1;

%  ---- Process images

img = gmrimage(images);

if ~isempty(masks)
	mask = gmrimage(masks);
else
	mask = [];
end

%  ---- Process figure parts

if ischar(elements)
	elements = g_ParseOptions([], elements, 'type=image|img=1|mask=[]|ROI=[]|name=[]|size=[]|use=0|scale=0|stats>type=fd,img=1');
end

nelements = length(elements);

for n = 1:nelements

	% ----> preprocess image entry

	if strcmp(elements(n).type, 'image')

		if elements(n).img > length(img)
			error('ERROR: The specified image does not exist! [%d of %d]', elements(n).img, length(img));
		end

		% ----> Define ROI

		if isempty(elements(n).ROI)
			if isfield(roi, elements(n).name)
				elements(n).ROI = roi.(elements(n).name);
				elements(n).size = sz.(elements(n).name);
				if verbose, fprintf('\n ---> added ROI codes for %s.', elements(n).name); end

			else
				if verbose, fprintf('\nWARNING: Unknown tissue type [%s], using all data!', elements(n).name); end
				elements(n).name = [elements(n).name ' (all)'];
			end
		end

		% ----> Create mask
		if ~isempty(elements(n).mask)
			if elements(n).mask > length(mask)
				error('ERROR: The specified mask does not exist! [%d of %d]', elements(n).mask, length(mask));
			end

			if img(elements(n).img).voxels ~= mask(elements(n).mask).voxels
				error('ERROR: Image and mask size does not match! [%d vs. %d]', img(elements(n).img).voxels, mask(elements(n).mask).voxels);
			end

			if isempty(elements(n).ROI)
				elements(n).mask = sum(img(elements(n).img).data, 2) > 0;
				if verbose, fprintf('\n ---> masking with nonzero!'); end
			else
				elements(n).mask = ismember(mask(elements(n).mask).image2D, elements(n).ROI);
				if verbose, fprintf('\n ---> masking with ROI!'); end
			end
		else
			if verbose, fprintf('\n ---> masking with nonzero!'); end
			elements(n).mask = sum(img(elements(n).img).data, 2) > 0;
		end


		% ----> Compute image size

		if isempty(elements(n).size)
			elements(n).size = sum(elements(n).mask);
		end
		sz.Var = sz.Var + elements(n).size;
		if verbose, fprintf('\n ---> added %s of size %d', elements(n).name, elements(n).size); end
	end

	% ----> preprocess stats entry

	if strcmp(elements(n).type, 'stats')
		for s = 1:length(elements(n).stats)

			id = elements(n).stats(s).img;
			if id > length(img)
				error('ERROR: The specified image does not exist! [%d of %d]', id, length(img));
			end

			if strcmp(elements(n).stats(s).type, 'fd')
				if isempty(img(id).fstats_hdr) || ~ismember('fd', img(id).fstats_hdr)
					error('\nERROR: FD data not present! [%s]', img(id).filename);
				end
				elements(n).stats(s).data = img(id).fstats(:, ismember(img(id).fstats_hdr, 'fd'));
			elseif ismember(elements(n).stats(s).type, {'dvars', 'dvarsm', 'dvarsme'})
				stats = img(id).mri_StatsTime('dvars');
				elements(n).stats(s).data = stats.(elements(n).stats(s).type);
			elseif strcmp(elements(n).stats(s).type, 'scrub')
				if isempty(img(id).use)
					error('\nERROR: Use data not present! [%s]', img(id).filename);
				end
			else
				error('\nERROR: Unknown stats type! [%s]', elements(n).stats(s).type);
			end
		end
		if isempty(elements(n).size)
			elements(n).size = sz.Stat;
		end
		sz.Fix = sz.Fix + sz.Stat;
	end
end


% ----> start building figure

f = figure;
set(f, 'PaperType', 'usletter');
set(f, 'PaperPosition', [0.25 0.25 8 10.5]);

sz.fac = (1 - (nelements-1) * sz.IPad - sz.VBot - sz.VTop - sz.Fix) / sz.Var;
vused = 1 - sz.VTop;

for n = 1:nelements

	if strcmp(elements(n).type, 'stats')
		vuse = elements(n).size;
		if verbose, fprintf('\n ---> stats of size: %.3f', vuse); end
	else
		vuse = elements(n).size * sz.fac;
		if verbose, fprintf('\n ---> image of size: %.3f', vuse); end
	end

	if verbose, fprintf('\n ---> subplot: %.3f %.3f %.3f %.3f', sz.HPad, vused - vuse, 1 - 2 * sz.HPad, vuse); end
	sp = subplot('Position', [sz.HPad vused - vuse 1 - 2 * sz.HPad vuse]);
	vused = vused - vuse - sz.IPad;

	if strcmp(elements(n).type, 'stats')
		data = [];
		fleg = {};
		for sn = 1:length(elements(n).stats)
			data = [data reshape(elements(n).stats(sn).data, [], 1) ./ th.(elements(n).stats(sn).type)];
			fleg{sn} = elements(n).stats(sn).type;
		end
		% data = data(dstart:end, :);

		plot(data);
		ylabel(sp, '');
		set(sp, 'XLim', [1 size(data, 1)]);
		set(sp, 'YLim', [0 3]);
		legend(fleg, 'Color', 'none', 'Box', 'off');
		line([1:size(data,1)]', ones(size(data,1),1), 'Color', [0.6 0.6 0.6]);

	else

		if elements(n).use == 1
			if verbose, fprintf('\n ---> ignoring bad frames'); end
			tmask = img(elements(n).img).use;
			if skip > 0
				tmask(1:skip) = 0;
			end
		else
			if verbose, fprintf('\n ---> using all data'); end
			tmask = ones(img(elements(n).img).frames, 1);
		end
		tmask = tmask > 0;

		data = img(elements(n).img).data(elements(n).mask,:);
		mimg = mean(data(:, tmask), 2);
		data = bsxfun(@minus, data, mimg);
		elements(n).imax = max(max(data(:, tmask)));
		elements(n).imin = min(min(data(:, tmask)));
		data(:, ~tmask) = elements(n).imin;

		if elements(n).scale == 0
			imagesc(data, [elements(n).imin, elements(n).imax]);
		else
			imagesc(data, [elements(elements(n).scale).imin, elements(elements(n).scale).imax]);
		end

		colormap(sp, gray);
		ylabel(sp, elements(n).name);
	end
	set(sp, 'YTick', []);
	if n < nelements
		set(sp, 'xTick', []);
	end

end

% ----> Title

txt = regexp(images, ';', 'split');
for t = 1:length(txt)
	[p, b, e] = fileparts(txt{t});
	txt{t} = [b e];
end
txt = strjoin(txt, ', ');
txt = strrep(txt, '_', '\_');

sp = subplot('Position', [sz.HPad  1 - sz.VTop 1 - 2 * sz.HPad sz.VTop]);
set(sp, 'YLim', [0 3]);
text(0, 0, {['\bf\fontsize{16}BOLD Timeseries Plot \rm|\color{red} ' subjid], ['\rm\fontsize{12}\color{black}' txt]}, 'VerticalAlignment', 'bottom');
set(sp, 'Visible', 'off');

saveas(f, filename);
close(f);

if verbose, fprintf('\n DONE\n'); end




