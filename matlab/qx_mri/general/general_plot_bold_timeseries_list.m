function [] = general_plot_bold_timeseries_list(flist, elements, filename, skip, fformat, verbose)

%``general_plot_bold_timeseries_list(flist, elements, filename, skip, fformat, verbose)``
%
%   Creates and saves a plot of BOLD timeseries for a list of sessions.
%
%   Parameters:
%       --flist (str):
%           List of files in the standard format.
%
%       --elements (struct | str, default 'type=stats|stats>type=dvarsme,img=1>type=fd,img=1;type=image|name=V|mask=1;type=image|name=WM|mask=1;type=image|name=GM|mask=1;type=image|name=V|mask=1|img=2|use=1|scale=2;type=image|name=GM|mask=1|img=2|use=1|scale=4'):
%           Plot element specification.
%
%       --filename (str, default ''):
%           Prefix of root filename to save the plot to.
%
%       --skip (int, default 0):
%           How many frames to skip at the stat of the bold run.
%
%       --fformat (str, default 'pdf'):
%           Plot output format.
%
%       --verbose (bool, default false):
%           Whether to be talkative.
%
%   Notes:
%       This function runs general_plot_bold_timeseries function on a list of
%       sessions making it simpler to generate BOLD timeseries plots for a set
%       of sessions. For more information on generation of plots, please see
%       documentation for general_plot_bold_timeseries.
%
%       Parameter details:
%           flist
%               A path to the standard list file. The list has to provide for
%               each sessions as many 'file:' entries as there are images
%               refered to by the element specification, and one 'roi:' entry to
%               be used as a mask. For typical use the first file would be a raw
%               bold image, the second file a preprocessed bold image, and roi
%               file an aparc or aparc+aseg segmentation in the same resolution
%               as the bold files. Do note that these should be NIfTI files as
%               most often signal from ventricles and white matter is plotted
%               and this information is not present in cifti files. If these
%               signals are not required, the function can work with cifti files
%               as well.
%
%           elements
%               Either a structure or a well formed string that can be processed
%               using the general_parse_options function that specifies wha
%               should be plotted. Please see documentation for
%               general_plot_bold_timeseries for detailed information on how to
%               specify plot elements. The default string is::
%
%                   'type=stats|stats>type=dvarsme,img=1>type=fd,img=1;
%                   type=image|name=V|mask=1;
%                   type=image|name=WM|mask=1;
%                   type=image|name=GM|mask=1;
%                   type=image|name=V|mask=1|img=2|use=1|scale=2;
%                   type=image|name=GM|mask=1|img=2|use=1|scale=4'
%
%               This creates a document with a single stats plot that includes
%               frame displacement and dvarsme statistics for the first image,
%               ventricle, white matter, and gray matter plots for the first
%               image, each scaled individually, and ventricle and gray matter
%               plots for the second image, with bad frames masked and scaled to
%               the same scale as the first image.
%
%           filename
%               The root filename for the generated plot. The plots are saved in
%               the sessions's images/functional/movement folder and named using
%               the following formula::
% 
%                   <filename parameter><the filename of the first specified file>_tsplot.<fformat>
%
%               An example with bold1.nii.gz as the first file, QA as value
%               of the filename parameter, and `pdf` as the value of fformat
%               parameter would be::
%
%                   QAbold1_tsplot.pdf
%
%           fformat
%               File format in which the plot is to be saved, 'pdf' by default.
%
%           skip
%               If no initial dummy scans were used during image acquisition,
%               the number of frames to skip from the start of the bold image.
%               0 by default.
%
%           verbose
%               Whether to provide a report of what is being done while the
%               function is running. False by default.
%
%   Examples:
%       ::
%
%           qunex general_plot_bold_timeseries_list \
%               --flist=bolds.list \
%               --elements=[] \
%               --filename=QA \
%               --skip=5 \
%               --fformat=png \
%               --verbose=true
%


% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

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

list = general_read_file_list(flist);

for n = 1:list.nsessions
    if verbose, fprintf('\n ---> processing %s', list.session(n).id); end

    [tpath tfile] = fileparts(list.session(n).files{1});
    tfile = regexp(tfile, '(^.*?)[._]', 'tokens');
    tfile = tfile{1};
    tfile = tfile{1};
    tfile = [tpath filesep 'movement' filesep filename tfile '_tsplot.' fformat];

    imgfiles = strjoin(list.session(n).files, ';');
    maskfiles = list.session(n).roi;

    general_plot_bold_timeseries(imgfiles, elements, maskfiles, tfile, skip, list.session(n).id, false);
end

if verbose, fprintf('\n ---> DONE\n'); end

function [s] = strjoin(c, d)
    s = [];
    for n = 1:length(c)
        s = [s c{n}];
        if n < length(c)
            s = [s d];
        end
    end
