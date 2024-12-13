function [] = fc_compute_gbcd(flist, command, roi, rcodes, nbands, mask, verbose, target, targetf, rsmooth, rdilate, ignore, time, method, weights, criterium)

%``fc_compute_gbcd(flist, command, roi, rcodes, nbands, mask, verbose, target, targetf, rsmooth, rdilate, ignore, time, method, weights, criterium)``
%
%   Computes GBC averages for each specified ROI for n bands defined as distance
%   from ROI.
%
%   NOTE: Please, note that fc_compute_gbc3 function is being deprecated.
%         The function will no longer be developed and will be removed in future
%         releases of QuNex. The functionality may be included in fc_compute_gbc,
%         which offers additional functionality, instead.
%
%   Parameters:
%       --flist (str):
%           A conc-like style list of session image files or conc files:
%
%           - session id:<session_id>
%           - roi:<path to the individual's ROI file>
%           - file:<path to bold files - one per line>
%
%           or a well strucutured string (see general_read_file_list).
%
%       --command (str):
%           The type of gbc to run: mFz, aFz, pFz, nFz, aD, pD, nD, mFzp,
%           aFzp, ...
%
%           ``<type of gbc>:<parameter>|<type of gbc>:<parameter> ...``
%
%           Following options are available:
%
%           - mFz:t
%               computes mean Fz value across all voxels (over threshold t)
%           - aFz:t
%               computes mean absolute Fz value across all voxels (over
%               threshold t)
%           - pFz:t
%               computes mean positive Fz value across all voxels (over
%               threshold t)
%           - nFz:t
%               computes mean positive Fz value across all voxels (below
%               threshold t)
%           - aD:t
%               computes proportion of voxels with absolute r over t
%           - pD:t
%               computes proportion of voxels with positive r over t
%           - nD:t
%               computes proportion of voxels with negative r below t.
%
%       --roi (str):
%           The roi names file.
%
%       --rcodes (vector, default ''):
%           Codes of regions from roi file to compute GBC for (all if not
%           provided or left empty).
%
%       --nbands (int, default ''):
%           Number of distance bands to compute GBC for.
%
%       --mask (int | logical | vector, default ''):
%           An array mask defining which frames to use (1) and which not (0).
%           All if empty.
%
%       --verbose (bool, default false):
%           Report what is going on.
%
%       --target (vector, default FreeSurfer scortex codes):
%           Array of ROI codes that define target ROI.
%
%       --targetf (str, default ''):
%           Target folder for results.
%
%       --rsmooth (int, default ''):
%           Radius for smoothing (no smoothing if empty).
%
%       --rdilate (int, default ''):
%           Radius for dilating mask (no dilation if empty).
%
%       --ignore (str, default 'usevec'):
%           The column in `*_scrub.txt` file that matches bold file to be
%           used for ignore mask.
%
%       --time (bool, default true):
%           Whether to time the processing.
%
%   Notes:
%       This is a wrapper function for computing GBC for specified ROI across
%       the specified number of distance bands. The function goes through a list
%       of sessions specified by flist file and runs `img_compute_gbcd` method
%       on bold files listed for each session. ROI to compute GBC for are
%       specified in roi and rcodes parameters, whereas the mask of what voxels
%       to compute GBC over is specified by target parameter. The values should
%       match rcodes used in session specific roi file. Usually this would be a
%       freesurfer segmentation image and if no target values are specified all
%       the gray matter related values present in aseg files are used.
%
%       The results are aggregated and stored in a matlab data file which holds
%       a data structure with the following fields:
%
%       - data.gbcd(s).gbc
%           resulting GBC matrix for each session
%
%       - data.gbcd(s).roiinfo
%           names of ROI for which the GBC was computed for
%
%       - data.gbcd(s).rdata
%           information on center mass and distance bands for each of the ROI
%
%       - data.roifile
%           the file used to defined ROI
%
%       - data.rcodes
%           codes used to identify ROI
%
%       - data.sessions
%           cell array of session ids
%
%       targetf specifies the folder in which the results will be saved. The
%       file will be named using the root of the flist with '_GBCd.mat' added to
%       it.
%
%       For more specific information on what is computed, see help for nimage
%       method img_compute_gbcd.
%
%   Examples:
%       ::
%
%           qunex fc_compute_gbcd \
%               --flist='scz.list' \
%               --command='mFz:0.1|pFz:0.1' \
%               --roi='dlpfc.names' \
%               --rcodes='[]' \
%               --nbands=10 \
%               --mask=0 \
%               --verbose=true \
%               --target='gray' \
%               --targetf='dGBC' \
%               --rsmooth=2 \
%               --rdilate=2 \
%               --ignore='udvarsme' \
%               --time=false
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

fprintf('\n\nStarting ...');

if nargin < 16, criterium = []; end
if nargin < 15, weights = true; end
if nargin < 14, method = true;  end
if nargin < 13, time = true;    end
if nargin < 12, ignore = [];    end
if nargin < 11, rdilate = [];   end
if nargin < 10, rsmooth = [];   end
if nargin < 9, targetf = '';    end
if nargin < 8, target = [];     end
if nargin < 7, verbose = false; end
if nargin < 6, mask = [];       end
if nargin < 5, nbands = [];     end
if nargin < 4, rcodes = [];     end
if nargin < 3, error('\nERROR: At east first three arguments need to be provided to run fc_compute_gbcd!\n'), end

if isempty(ignore)
    ignore = 'usevec';
end
if isempty(target)
    target = [3 8 9 10 11 12 13 16 17 18 19 20 26 27 28 42 47 48 49 50 51 52 53 54 55 56 58 59 60 96 97];
end

commands = regexp(command, '\|', 'split');

%   ------------------------------------------------------------------------------------------
%   -------------------------------------------------- make a list of all the files to process

fprintf('\n ... listing files to process');

list = general_read_file_list(flist, 'all', [], verbose);

fprintf(' ... done.');


%   ------------------------------------------------------------------------------------------
%   -------------------------------------------- The main loop ... go through all the sessions

fout = fopen([targetf '/' list.listname '_GBCd.tab'], 'w');
fprintf(fout, 'session\tcommand\troi\tband\tvalue');

%   --- Get variables ready first

for s = 1:list.nsessions

    %   --- reading in image files
    tic;
    fprintf('\n ... processing %s', list.session(s).id);
    fprintf('\n     ... reading image file(s) ');

    y = [];

    nfiles = length(list.session(s).files);

    img = nimage(list.session(s).files{1});

    fprintf('1');
    if ~isempty(mask),   img = img.sliceframes(mask); end
    if ~isempty(ignore), img = img.img_scrub(ignore); end

    if nfiles > 1
        for n = 2:nfiles
            new = nimage(list.session(s).files{n});
            fprintf(', %d', n);
            if ~isempty(mask),   new = new.sliceframes(mask); end
            if ~isempty(ignore), new = new.img_scrub(ignore); end
            img = [img new];
        end
    end

    imask = nimage(list.session(s).roi);
    imask = imask.ismember(target);

    if rsmooth
        limit = isempty(rdilate);
        img = img.img_smooth_3d_masked(imask, rsmooth, limit, verbose);
    end

    if rdilate
        imask = imask.img_grow_roi(rdilate);
    end

    roiimg = nimage.img_read_roi(roi, list.session(s).roi);

    [res, roiinfo, rdata] = img.img_compute_gbcd(command, roiimg, rcodes, nbands, [], imask);

    data.gbcd(s).gbc = res;
    data.gbcd(s).roiinfo = roiinfo;
    data.gbcd(s).rdata = rdata;

    %  'session\tcommand\troi\tband\tvalue'

    for nc = 1:size(res,3)
        for nr = 1:size(res,2)
            for nb = 1:size(res,1)
                fprintf(fout, '\n%s\t%s\t%s\t%d\t%.6f', list.session(s).id, commands{nc}, roiinfo.roinames{nr}, nb, res(nb, nr, nc));
            end
        end
    end

    fprintf(' [%.1fs]\n', toc);
end

data.roifile  = roi;
data.rcodes   = rcodes;
data.sessions = list.session;

fclose(fout);
save([targetf '/' list.listname '_GBCd'], data);




%
%   ---- Auxilary functions
%

%   ---- Parse the command

function [ext] = parseCommand(s)

    ext = {};

    a = splitby(s,'|');
    for n = 1:length(a)
        b = splitby(a{n}, ':');

        com = b{1};
        par = str2num(b{2});

        pre = com(1);
        pos = com(end);

        if ismember(pos, 'ps')
            if pos == 'p'
                sstep = 100 / par;
                parameter = floor([[1:sstep:100]', [1:sstep:100]'+(sstep-1)]);
                for p = 1:par
                    ext{end+1} = [com '_' num2str(parameter(p,1)) '_' num2str(parameter(p,2))];
                end
            else
                if ismember(pre, 'ap')
                    sv = 0;
                    ev = 1;
                    al = 1;
                elseif pre == 'm'
                    sv = -1;
                    ev = 1;
                    al = 1;
                else
                    sv = -1;
                    ev = 0;
                    al = 0;
                end
                sstep = (ev-sv) / par;
                parameter = [sv:sstep:ev];
                for p = 1:par
                    ext(end+1) = [com '_' num2str(parameter(p)) '_' num2str(parameter(p+1))];
                end

            end
        else
            ext{end+1} = [com '_' num2str(par)];
        end
    end


function [out] = splitby(s, d)
    c = 0;
    while length(s) >=1
        c = c+1;
        [t, s] = strtok(s, d);
        if length(s) > 1, s = s(2:end); end
        out{c} = t;
    end

