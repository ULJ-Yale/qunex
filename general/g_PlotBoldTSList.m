function [] = g_PlotBoldTSList(flist, elements, filename, skip, fformat, verbose)

%function [] = g_PlotBoldTSList(flist, elements, filename, skip, fformat, verbose)
%
%		Creates and saves a plot of BOLD timeseries
%
%       flist       - list of files in the standard format
%		elements    - plot element specification
%       filename    - root filename to save the plot to
%       skip        - how many frames to skip at the stat of the bold run
%		fformat		- plot output format
%		verbose		- whether to be talkative
%
%   (c) Grega Repovs, 2015-10-17
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
g_CheckFile(flist, 'image file list', 'error');

subject = g_ReadFileList(flist);
nsub = length(subject);

for n = 1:nsub
	if verbose, fprintf('\n ---> processing %s', subject(n).id); end

	[tpath tfile] = fileparts(subject(n).files{1});
	tfile = regexp(tfile, '(^.*?)[._]', 'tokens');
	tfile = tfile{1};
	tfile = tfile{1};
	tfile = [tpath filesep 'movement' filesep filename tfile '_tsplot.' fformat];

	imgfiles = strjoin(subject(n).files, ';');
	maskfiles = subject(n).roi;

	g_PlotBoldTS(imgfiles, elements, maskfiles, tfile, skip, subject(n).id, false);
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