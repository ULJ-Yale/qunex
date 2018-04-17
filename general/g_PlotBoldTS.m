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
%   USE
%   The function is used to create a plot of BOLD timeseries for quality control inspection. 
%   Specifically, it allows plotting of bold statistics as well as a "watershed" type plots,
%   where intensities of voxels over time are plotted as shades of grey. The function can plot
%   a configurable number of elements from multiple BOLD images, which allows visual inspection
%   of preprocessing effects. 
%
%   PARAMETERS
%   
%   Please note that the parameters are not described in the order taken by the function.
%
%   *images*
%   images can be either a semicolon separated list of bold files to be used, or an array of
%   gmrimage objects. The order in which the files are specified is the order in which they 
%   should be referenced in the elements specification.
% 
%   Example images parameter: 'bold1.nii.gz;bold1_g7_hpss_res.nii.gz'
%
%   do note that each image in the semicolon separated list can be a conc file or a set of
%   files separated with the pipe | character. In the following example:
%
%   'bold1.nii.gz|bold2.nii.gz;bold1_g7_hpss.nii.gz|bold2_g7_hpss.nii.gz'
%
%   the first two files would be concatenated to image 1 and the second pair to image 2.
%   This allows easy plotting of conatenated bolds.
%
%   Do note that these should be NIfTI files as most often signal from ventricles and
%   white matter is plotted and this information is not present in cifti files. If
%   these signals are not required, the function can work with cifti files as well.
%
%   *masks*
%   masks again can be either a single iamge or a set of images passed either as gmrimage
%   objects or as paths. If more than one mask is to be used, again a semicolumn separated 
%   list of paths can be provided. The masks are used to define the part of the image to
%   display. They can be an ROI mask or a segmentation image.
%
%   *elements*
%   elements can be either a structure that specifies, which elements the plot should have 
%   or a string that can be parsed into a structure using g_ParseOptions function. Each 
%   element can have the following fields:
% 
%   * name    ... The name or title of the element to draw. There are four standard names
%                 that can be used to simplify the latter definition of the mask, these are:
%                 V  - ventricles
%                 WM - white matter
%                 GM - gray matter
%                 WB - whole brain
%                 any other name can be used if desired. []
%   * type    ... Defines what will be drawn, it can be 'image' for actual signal values 
%                 or 'stats' for plot of summary statistics across voxels. [image]
%   * img     ... Defines, which image file the data to plot should be based on, it is
%                 an integer value, an index starting with 1. [1]
%   * mask    ... Defines, which of the mask images specified using masks parameter should
%                 be used to select only a specific part of the image to draw, it is an
%                 integer value, an index starting with 1. If a mask is not specified, then
%                 all the nonzero voxels across the image will be plotted. []
%   * ROI     ... An array of values that will be matched against the mask. Only those 
%                 voxels that match ROI values in the mask will be plotted. E.g. if in a 
%                 mask PFC is marked with 1, thalamus with 2, and cerebellum with 3, then
%                 ROI=[1] would plot only PFC voxels, and ROI=[2 3] would plot thalamus
%                 and cerebellum voxels. If one of the standard names is specified for 
%                 the name field (V, WM, GM, WB) and ROI is not specified, then the mask
%                 will be assumed to be a FreeSurfer aseg or aseg+aparc file and the 
%                 correct ROI values will be automatically used. []
%   * size    ... The vertical size of the element. For standard names it can be left 
%                 empty, otherwise it provides a relative size information, the actual
%                 size will be computed for all elements to fit a page. []
%   * use     ... Whether frames use information should be taken into account. If set to
%                 1 frames marked as bad in a bold file will be masked and their intensity
%                 will not be shown. If set to 0, then all frames will be plotted. Do take
%                 into account that voxel intensity values are mapped onto a grayscale
%                 image to show the whole range of values from lowest to highest, so
%                 if bad frames are plotted they can significantly change the mapping. [0]
%   * scale   ... Which element should intensity scaling be based on. If set to 0, the
%                 scaling will be based on the minimal and maximal value of data in this
%                 element, otherwise it should be a an integer value specifying the index
%                 of the relevant element. Setting elements to the same scale allows 
%                 direct comparison between them. This field is only relevant for image 
%                 type elements. [0]
%   * stats   ... This field is a structure with fields that provide additional information
%                 for stats type plots. It should define the following fields:
%     - type      ... A string that specifies, what statistic is plotted. Valid values are [fd]:
%                     fd - display frame displacement information
%                     dvars - display dvars values
%                     dvarsm - display image mean intensity normalised dvars values
%                     dvarsme - display timeseries median normalised dvarsm values
%                     V - mean ventricle signal
%                     WM - mean white matter signal
%                     GM - mean gray matter signal
%                     WB - mean whole brain signal
%                     GO - mean signal across the whole image
%                     scrub - whether the frame is to be used or scrubbed
%     - img       ... The index of the image the statistics refers to. [1]
%     - mask      ... The index of the mask that holds aseg or aseg+aparc image when 
%                     mean signal statistic is to be displayed. [1]
%                 Do note that if stats is structure array, multiple statistics will
%                 be plotted in the same element/graph.
%
%   An example string specification:
%
%   'type=stats|stats>type=fd,img=1>type=dvarsme,img=1;
%    type=image|name=V|img=1|mask=1;
%    type=image|name=WM|img=1|mask=1;
%    type=image|name=GM|img=1|mask=1;
%    type=image|name=GM|img=2|mask=1|use=1'
%
%   If the first image is raw bold, the second image fully preprocessed bold, and the mask
%   an aseg or aseg+aparc image, this specification would show frame displacement and dvarsme
%   information plotted in the same element, plots of ventricle, white matter, and gray matter 
%   signal in the raw image, and the gray matter signal from the preprocessed image with bad 
%   frames masked out. All images would be scaled to their individual range of signal values.
%
%   *skip*
%   skip provides information on how many frames from the start of the image to ignore. 
%   This is relevant for legacy data that does not use prescans and the signal is not yet
%   stable. It is set to 0 by default. The skipped frames are masked.
%
%   *subjid*
%   The subject id information to display in the title of the page.
%
%   *filename*
%   The path and filename for the resulting PDF. 'BoldTSPlot.pdf' by default.
%
%   *verbose*
%   Whether to print out the information about the progress of the plotting. False by default.
%
%   EXAMPLE USE
%   g_PlotBoldTS('bold1.nii.gz;bold1_g7_hpss_res.nii.gz', 'type=stats|stats>type=fd,img=1>type=dvarsme,img=1;type=image|name=V|img=1|mask=1;type=image|name=WM|img=1|mask=1;type=image|name=GM|img=1|mask=1;type=image|name=GM|img=2|mask=1|use=1', 'aseg.nii.gz', 'AP1937-BoldTSPlot.pdf', 0, 'AP1937', true);
%
%   ——————————————————————————
%   Written by Grega Repovs, 2015-10-17
%
%   Change log
%   2018-01-20 Grega Repovs
%            - Written detailed documentation
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

sz.Stat = .08;
sz.GM   = 60;
sz.WM   = 30;
sz.V    = 7;
sz.WB   = 80;
sz.GO   = 60;

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
    elements = g_ParseOptions([], elements, 'type=image|img=1|mask=[]|ROI=[]|name=[]|size=[]|use=0|scale=0|stats>type=fd,img=1,mask=1');
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
				if isfield(sz, elements(n).name)
					if verbose, fprintf('\n ---> imputing size for %s.', elements(n).name); end
					elements(n).size = sz.(elements(n).name);
				else
					if verbose, fprintf('\n ---> no size info found for %s.', elements(n).name); end
				end
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
			elseif ismember(elements(n).stats(s).type, {'V', 'WM', 'GM', 'WB'})
				tmask = ismember(mask(elements(n).stats(s).mask).image2D, roi.(elements(n).stats(s).type));
				stats = img(id).mri_StatsTime('m', tmask);
				elements(n).stats(s).data = stats.mean;
			elseif ismember(elements(n).stats(s).type, {'GO'})
				stats = img(id).mri_StatsTime('m');
				elements(n).stats(s).data = stats.mean;
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

% ... j2

j2 = sortrows([[64:-1:1]', jet], 1);
j2 = [j2(:,2:end); jet ];
j2 = j2(1:2:128,:);

j2 = sortrows([[64:-1:1]', hsv], 1);
j2 = [j2(:,2:end); hsv ];
j2 = j2(1:2:128,:);


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
		thline = false;
		for sn = 1:length(elements(n).stats)
			if isfield(th, elements(n).stats(sn).type)
				data = [data reshape(elements(n).stats(sn).data, [], 1) ./ th.(elements(n).stats(sn).type)];
				thline = true;
			else
				dmin = min(elements(n).stats(sn).data);
				dmax = max(elements(n).stats(sn).data);
				data = [data (reshape(elements(n).stats(sn).data, [], 1) - dmin) / (dmax - dmin) * 2.5 ];
			end

			fleg{sn} = elements(n).stats(sn).type;
		end
		% data = data(dstart:end, :);

		plot(data);
		ylabel(sp, '');
		set(sp, 'XLim', [1 size(data, 1)]);
		set(sp, 'YLim', [0 3]);
		legend(fleg, 'Color', 'none', 'Box', 'off');
		if thline
			line([1:size(data,1)]', ones(size(data,1),1), 'Color', [0.6 0.6 0.6]);
		end

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
		data(:, ~tmask) = 0.5;
		data(1:floor(size(data,1)/16), ~tmask) = elements(n).imin;

		if elements(n).scale == 0
			imagesc(data, [elements(n).imin, elements(n).imax]);
		else
			imagesc(data, [elements(elements(n).scale).imin, elements(elements(n).scale).imax]);
		end
		colormap(sp, j2);
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
%print(f,'-dpdf', '-r72', [filename '.pdf']);
close(f);

if verbose, fprintf('\n DONE\n'); end




function [s] = strjoin(c, d)
    s = [];
    for n = 1:length(c)
        s = [s c{n}];
        if n < length(c)
            s = [s d];
        end
    end
