function [] = general_compute_bold_stats(img, mask, target, store, scrub, verbose)

%``general_compute_bold_stats(img, mask, target, store, scrub, verbose)``
%
%   Computes BOLD run per frame statistics and scrubbing information.
%
%   Parameters:
%       --img (str | matrix | cell | nimage):
%           An nimage object or a path to a BOLD file to process.
%
%       --mask (str | matrix | cell | nimage):
%           An nimage object or a path to a mask file to use.
%
%       --target (str, default ''):
%           A folder to save results into:
%
%           - []: where bold image is,
%           - 'none': do not save results in an external file.
%
%       --store (str, default ''):
%           Whether to store the data in the image file:
%
%           - 'same': in the same file,
%           - '<ext>': in a new file with extension <ext>,
%           - []: do not save information in an image file.
%
%       --scrub (str, default 'none'):
%           A string describing whether and how to compute scrubbing
%           information, e.g. 'pre:1|post:1|fd:4|ignore:udvarsme' or 'none' for
%           no scrubbing (see img_compute_scrub_nimage method for more
%           information).
%
%       --verbose (bool, default false):
%            To report the progress or not.
%
%   Notes:
%       The function is used to compute and save per frame statistics to be used
%       for bad frames scrubbing. It also initiates computation of scrubbing
%       information if a scrubbing string is present.
%
%       The function identifies relevant brain voxels in two manners. First, it
%       identifies voxels with intensity higher than 300 on the first BOLD
%       frame. If there are more than 20000 valid voxels, it then select those
%       for which the intensity is always above the specified threshold and
%       selects those for computation of image statistics.
%
%       Second, if the first method fails (e.g. in the case when images were
%       demeaned), it identifies all the voxels for which the variance across
%       the frames is more than 0.
%
%       After the voxels were identified, the image is additionally masked if a
%       mask was specified, and the statistics are computed using img_stats_time
%       nimage method.
%
%       If scrub is not set to 'none', scrubbing information is also computed by
%       calling img_compute_scrub nimage method.
%
%       The results can then be saved either by embedding them into the volume
%       image (specified in the store parameter) or by saving them in separate
%       files in the specified target folder using .bstats extension for bold
%       statistics, .scrub extension for scrubbing information and .use
%       extension for information, which frame to use.
%
%   Warning:
%       Saving data by embedding in a volume file is currently disabled.
%
%   Examples:
%       ::
%
%           general_compute_bold_stats \
%               --img='bold1.nii.gz' \
%               --mask='' \
%               --target='movement' \
%               --store='' \
%               --scrub='' \
%               --verbose='true'
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 6, verbose = false;  end
if nargin < 5, scrub   = 'none'; end
if nargin < 4, store   = [];     end
if nargin < 3, target  = [];     end
if nargin < 2, mask    = [];     end

brainthreshold = 300;
minbrainvoxels = 20000;

% ======= Run main

if verbose,
    if verbose, fprintf('\nRunning general_compute_bold_stats\n--------------------------\n'); end
    fprintf('\nParameters:\n-----------');
    fprintf('\n        img: %s', img);
    fprintf('\n       mask: %s', mask);
    fprintf('\n     target: %s', target);
    fprintf('\n      store: %s', store);
    fprintf('\n      scrub: %s\n', scrub);
end

% --- check mask

if ~isempty(mask)
    if ~isa(mask, 'nimage')
        if verbose, fprintf('\n---> Reading mask [%s]', mask); end
        mask = nimage(mask);
    end
end

% --- check bold

if ~isa(img, 'nimage')
    if verbose, fprintf('\n---> Reading bold [%s]', img); end
    img = nimage(img);
end

% --- find all below threshold voxels

img.data = img.image2D;
img.data(isnan(img.data)) = 0;

% - check whether the image is demeaned

bmask = img.zeroframes(1);
bmask.data = img.data(:,1);
bmask.data = bmask.data > brainthreshold;

if mean(mean(img.data(bmask.data,:),2)) < brainthreshold
    bmask.data = var(img.data, 0, 2);
    bmask.data = bmask.data > 0;
else
    img.data(img.data < brainthreshold) = 0;
    bmask.data = min(img.data, [], 2) > 0;
end

% --- apply also subject roi mask

if mask
    bmask.data(mask.data == 0) = 0;
end

% --- compute stats

if verbose, fprintf('\n ... computing stats '); end
stats = img.img_stats_time([], bmask);

% --------------------------------------------------------------
%                                       save in an external file

ext = true;
if target
    if strcmp(target, 'none')
        ext = false;
    end
end
if isempty(target)
    target = img.img_path();
end

fname = img.basename();

% --------------------------------------------------------------
%                                                  prepare stats

img.fstats_hdr  = {'frame', 'n', 'm', 'var', 'sd', 'dvars', 'dvarsm', 'dvarsme', 'fd'};
img.fstats      = zeros(img.frames, 9);
img.fstats(:,1) = 1:img.frames;
img.fstats(:,2) = stats.n;
img.fstats(:,3) = stats.mean;
img.fstats(:,4) = stats.var;
img.fstats(:,5) = stats.sd;
img.fstats(:,6) = stats.dvars;
img.fstats(:,7) = stats.dvarsm;
img.fstats(:,8) = stats.dvarsme;


% --------------------------------------------------------------
%                                              compute scrubbing

if ~strcmp(scrub, 'none')
    if verbose, fprintf('\n ... scrubbing '); end
    [img, parameters] = img.img_compute_scrub(scrub);
end


% --------------------------------------------------------------
%                                                 embed and save

% --- embedding turned off temporariliy

% if ~isempty(store)
%     if strcmp(store, 'same')
%         img.img_saveimage();
%     else
%         tname = [img.img_basenamepath() '_' store]);
%         img.img_saveimage(tname);
%     end
% end


% --------------------------------------------------------------
%                                                  save external

if ext

    % --- save stats

    if verbose, fprintf('\n ... saving stats '); end

    % if ismember('fd', img.fstats_hdr)
    %     stats.fd = img.fstats(:, ismember(img.fstats_hdr, {'fd'}));
    % else
    %     stats.fd = zeros(1, img.frames);
    % end

    % generate header
    version = general_get_qunex_version();
    header = sprintf('# Generated by QuNex %s on %s\n#', version, datestr(now,'YYYY-mm-dd_HH.MM.SS'));

    general_write_table(fullfile(target, [fname '.bstats']), img.fstats, img.fstats_hdr, 'max|mean|sd', '%-10s|%-10d|%-10g|%-9s', ' ', header);   % '%s|%d|%.3f|%s'

    % --- save scrub

    if ~strcmp(scrub, 'none')
        if verbose, fprintf('\n ... saving scrubbing data '); end

        pre = sprintf('%s# Parameters used\n# radius:   %d\n# fdt:      %.2f\n# dvarsmt:  %.2f\n# dvarsmet: %.2f\n# after:    %d\n# before:   %d\n# reject:   %s', header, parameters.radius, parameters.fdt, parameters.dvarsmt, parameters.dvarsmet, parameters.after, parameters.before, parameters.reject);
        general_write_table(fullfile(target, [fname '.scrub']), [img.scrub img.use'], [img.scrub_hdr, 'use'], 'sum|%', '%-8s|%-8d|%-8d|%-7s', ' ', pre);

        scr = fopen(fullfile(target, [fname '.use']), 'w');
        fprintf(scr, '%d\n', img.use);
        fclose(scr);

    end
end

if verbose, fprintf('\n ... done!'); end
if verbose, fprintf('\n---> Finished!\n'); end
