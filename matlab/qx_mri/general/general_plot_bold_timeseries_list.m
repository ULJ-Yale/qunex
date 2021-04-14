% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

function [] = general_plot_bold_timeseries_list(flist, elements, filename, skip, fformat, verbose)

%``function [] = general_plot_bold_timeseries_list(flist, elements, filename, skip, fformat, verbose)``
%
%   Creates and saves a plot of BOLD timeseries for a list of sessions.
%
%	INPUTS
%	======
%
%   --flist       list of files in the standard format
%   --elements    plot element specification
%   --filename    root filename to save the plot to
%   --skip        how many frames to skip at the stat of the bold run
%   --fformat     plot output format
%   --verbose     whether to be talkative
%
%   USE
%	===
%
%   This function runs general_plot_bold_timeseries function on a list of sessions making it
%   simpler to generate BOLD timeseries plots for a set sessionss. For more
%   information on generation of plots, please see documentation for
%   general_plot_bold_timeseries.
%
%   PARAMETERS
%	==========
%
%   flist
%		A path to the standard list file. The list has to provide for each
%		sessions as many 'file:' entries as there are images refered to by the
%		element specification, and one 'roi:' entry to be used as a mask. For
%		typical use the first file would be a raw bold image, the second file a
%		preprocessed bold image, and roi file an aparc or aparc+aseg
%		segmentation in the same resolution as the bold files. Do note that
%		these should be NIfTI files as most often signal from ventricles and
%		white matter is plotted and this information is not present in cifti
%		files. If these signals are not required, the function can work with
%		cifti files as well.
%
%   elements
%		Either a structure or a well formed string that can be processed using
%   	the general_parse_options function that specifies what should be plotted.
%   	Please see documentation for general_plot_bold_timeseries for detailed
    	information on how to specify plot elements. The default string is::
%
%   		'type=stats|stats>type=dvarsme,img=1>type=fd,img=1;
%   		 type=image|name=V|mask=1;
%   		 type=image|name=WM|mask=1;
%   		 type=image|name=GM|mask=1;
%   		 type=image|name=V|mask=1|img=2|use=1|scale=2;
%   		 type=image|name=GM|mask=1|img=2|use=1|scale=4'
%
%   	This creates a document with a single stats plot that includes frame
%   	displacement and dvarsme statistics for the first image, ventricle,
%   	white matter, and gray matter plots for the first image, each scaled
%   	individually, and ventricle and gray matter plots for the second image,
%   	with bad frames masked and scaled to the same scale as the first image.
%
%   filename
%   	The root filename for the generated plot. The plots are saved in the
%   	sessions's images/functional/movement folder and named using the
%   	following formula::
% 
%   		<filename parameter><the filename of the first specified file>_tsplot.<fformat>
%
%   	An example with bold1.nii.gz as the first file, 'QA_' as value of the
%   	filename parameter, and 'pdf' as the value of fformat parameter would
%   	be::
%
%   		QA_bold1_tsplot.pdf
%
%   fformat
%   	File format in which the plot is to be saved. 'pdf' by default.
%
%   skip
%   	If no initial dummy scans were used during image acquisition, the number
%   	of frames to skip from the start of the bold image. 0 by default.
%
%  	verbose
%
%  		Whether to provide a report of what is being done while the function is
%   	running. False by default.
%
%   EXAMPLE USE
%	===========
%
%	::
%
%   	general_plot_bold_timeseries_list('bolds.list', [], 'QA_', 5, 'png', true);
%

%  ---- initializing

if nargin < 6 || isempty(verbose), verbose = false; end
if nargin < 5 || isempty(fformat), fformat = 'pdf'; end
if nargin < 4 || isempty(skip), skip = 0; end
if nargin < 3 || isempty(filename), filename = ''; end
if nargin < 2 || isempty(elements), elements = 'type=stats|stats>type=dvarsme,img=1>type=fd,img=1;type=image|name=V|mask=1;type=image|name=WM|mask=1;type=image|name=GM|mask=1;type=image|name=V|mask=1|img=2|use=1|scale=2;type=image|name=GM|mask=1|img=2|use=1|scale=4'; end
if nargin < 1, error('ERROR: Please specify at least file list!'); end


%  ---- Check and load list

if verbose, fprintf('\n\nChecking ...\n'); end
general_check_file(flist, 'image file list', 'error');

sessions = general_read_file_list(flist);
nsub = length(sessions);

for n = 1:nsub
	if verbose, fprintf('\n ---> processing %s', sessions(n).id); end

	[tpath tfile] = fileparts(sessions(n).files{1});
	tfile = regexp(tfile, '(^.*?)[._]', 'tokens');
	tfile = tfile{1};
	tfile = tfile{1};
	tfile = [tpath filesep 'movement' filesep filename tfile '_tsplot.' fformat];

	imgfiles = strjoin(sessions(n).files, ';');
	maskfiles = sessions(n).roi;

	general_plot_bold_timeseries(imgfiles, elements, maskfiles, tfile, skip, sessions(n).id, false);
end

if verbose, fprintf('\n ===> DONE\n'); end

function [s] = strjoin(c, d)
    s = [];
    for n = 1:length(c)
        s = [s c{n}];
        if n < length(c)
            s = [s d];
        end
    end
