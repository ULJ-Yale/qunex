function [results, roiinfo, rdata] = img_compute_gbcd(obj, command, roi, rcodes, nbands, fmask, mask, verbose, rmax, time, method, weights, criterium)

%``img_compute_gbcd(obj, command, roi, rcodes, nbands, fmask, mask, verbose, rmax, time, method, weights, criterium)``
%
%    Computes GBC averages for each specified ROI for n bands defined as distance
%   from ROI.
%
%   INPUTS
%   ======
%
%    --obj         image
%   --command     string describing GBC to compute (pipe separated)
%
%                 mFz:t
%                     computes mean Fz value across all voxels (over threshold t)
%                 aFz:t
%                     computes mean absolute Fz value across all voxels (over 
%                     threshold t)
%                 pFz:t
%                     computes mean positive Fz value across all voxels (over 
%                     threshold t)
%                 nFz:t
%                     computes mean positive Fz value across all voxels (below 
%                     threshold t)
%                 aD:t
%                     computes proportion of voxels with absolute r over t
%                 pD:t
%                     computes proportion of voxels with positive r over t
%                 nD:t
%                     computes proportion of voxels with negative r below t
%
%   --roi         Roi names file, image name or a vector the size of image.
%   --rcodes      Codes of regions from roi file to compute GBC for (all if not 
%                 provided or left empty).
%   --nbands      Number of distance bands to compute GBC for. [10]
%   --fmask       Vector specifying what frames to use (nonzero, true) and which 
%                 not (zero, false). If empty, all are used.
%   --mask        Mask to define what voxels to include in GBC.
%   --verbose     Should it talk a lot [no]
%   --rmax        The r value above which the correlations are considered to be 
%                 of the same functional ROI. []
%   --time        Whether to print timing information. [false]
%   --method      Name of the method ename. [mean]
%
%                 - 'mean'       ... Average value of the ROI.
%                 - 'pca'        ... First eigenvariate of the ROI.
%                 - 'threshold'  ... Average of all voxels above threshold.
%                 - 'maxn'       ... Average of highest n voxels.
%                 - 'weighted'   ... Weighted average across ROI voxels.
%
%   --weights     Image file with weights to use in ROI time series extraction. []
%   --criterium   Threshold or number of voxels to extract []
%
%   USE
%   ===
%
%   The method takes each specified ROI—specified with roi and rcodes
%   parameters. It extracts its representative timecourse using the specified
%   method (mean / pca / threshold / maxn / weighted), and then computes its GBC
%   (using the specified GBC method) with each of the bands of voxels specified
%   by distance from the ROI center mass.
%
%   For instance the following call::
%
%       [results, roiinfo, rdata] = img.img_ComputeCBCd('mFz:0.1|pFz:0.1', ...
%       'dlpfc.names', [1, 2, 3], 10, [], 'graymatter.names', false, [], ...
%       false, 'pca');
%
%   Would for each of the three dlpfc regions defined in the dlpfc.names file
%   extract the first eigenvariate of its timeseries. It would sparate voxels
%   specified in graymatter.names file into 10 bands defined by their distance
%   from the roi center mass, compute correlation with all the voxels in the
%   band, ignore those with correlation less than ansolute 0.1 and compute mean
%   Fz across all of them them as well as the mean across only voxels with
%   positive correlations.
%
%   The resuls woud be returned in a 3D results matrix, the rows being each of
%   the 10 bands, the columns each of the ROI and the depth (3rd dimension) each
%   of the GBC commands. roiinfo would hold the names of the ROI used in cell
%   matrix of strings. rdata is a list of fields holding x, y and z coordinates
%   of center mass (.rx, .ry, and .rz fields respectively), and a vector the
%   specifies the membership of the distance bands for all the voxels GBC was
%   computed on (.d field).
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 13, criterium = []; end
if nargin < 12, weights = [];   end
if nargin < 11, method = [];    end
if nargin < 10, time = [];      end
if nargin < 9, rmax = [];       end
if nargin < 8, verbose = false; end
if nargin < 7, mask = [];       end
if nargin < 6, fmask = [];      end
if nargin < 5, nbands = [];     end
if nargin < 4, rcodes = [];     end
if nargin < 3, error('ERROR: Missing ROI to compute GBC for!'); end
if nargin < 2, error('ERROR: No command given to compute GBC!'); end


if ~isempty(fmask)
    obj = obj.sliceframes(fmask);
end
if isempty(rmax),   rmax = false; end
if isempty(time),   time = false; end
if isempty(nbands), nbands = 10;  end


% ---- check ROI data

if isa(roi, 'nimage')
    if ~obj.issize(roi);
        error('ERROR: ROI image does not match target in dimensions!');
    end
elseif isa(roi, 'char')
    roi = nimage.img_read_roi(roi);
elseif isa(roi, 'numeric')
    roi = reshape(roi, [], 1);
    if size(roi, 1) ~= obj.voxels
        error('ERROR: ROI mask does not match target in size!');
    end
else
    error('ERROR: Please provide a valid ROI image, filename or matrix!');
end
roi.data = roi.image4D;

if isempty (rcodes)
    rcodes = unique(roi.data);
    rcodes = rcodes(rcodes ~= 0);
end
nroi = length(rcodes);

if ~isempty(mask)
    mask.data = mask.image4D;
end

% ---- prepare banding

if isempty(mask)
    nt = prod(obj.dim);
else
    nt = sum(sum(mask.image2D > 0));
end

md = zeros(nt, nroi);

if nbands > 1
    sstep  = nt / nbands;
    limits = floor([[1:sstep:nt]'+(sstep-1)]);

    % -> get ROI center of mass

    x = reshape([1:roi.dim(1)], [roi.dim(1) 1 1]);
    x = repmat(x, [1 roi.dim(2) roi.dim(3)]);

    y = reshape([1:roi.dim(2)], [1 roi.dim(2), 1]);
    y = repmat(y, [roi.dim(1) 1 roi.dim(3)]);

    z = reshape([1:roi.dim(3)], [1 1 roi.dim(3)]);
    z = repmat(z, [roi.dim(1) roi.dim(2) 1]);


    for r = 1:nroi
        rx = mean(x(roi.data==rcodes(r)));
        ry = mean(y(roi.data==rcodes(r)));
        rz = mean(z(roi.data==rcodes(r)));

        rdata(r).rx = rx;
        rdata(r).ry = ry;
        rdata(r).rz = rz;

        d = sqrt((x-rx).^2+(y-ry).^2+(z-rz).^2);

        if ~isempty(mask)
            d = d(mask.data>0);
        end

        t  = reshape(d, [], 1);
        t  = sort(t);
        t = t(limits);

        for b = 1:nbands
            d(d <= t(b)) = 1000+b;
        end
        d = d-1000;
        d = reshape(d,[], 1);
        rdata(r).d = d;
        md(:,r) = d;
    end

else
    limits = [];
end

% ---- prepare data

if verbose, fprintf('\n... setting up data'), end


% ---- extract ROI ts

ts = obj.img_extract_roi(roi, rcodes, method, weights, criterium);

if ~obj.correlized
    ts = zscore(ts, 0, 2);
    ts = ts ./ sqrt(size(ts, 2) -1);
end

% ---- mask and prepare data

if ~obj.masked
    if ~isempty(mask)
        obj = obj.maskimg(mask);
    end
end

if ~obj.correlized
    obj = obj.correlize;
end

data = obj.image2D;
nvox = size(obj.image2D, 1);


% ---- parse command

if verbose, fprintf('\n\nStarting GBC on %s', obj.filename); stime = tic; end
commands = parseCommand(command, nvox);
ncommands = length(commands);


% ---- compute correlations

if time, fprintf(' r, Fz'); tic; end
r = data * ts';
Fz = fc_fisher(r);
if ~isreal(Fz)
    fprintf(' c>r')
    Fz = real(Fz);
end
if time fprintf(' [%.3f s]', toc); end

% ---- set up results

results = zeros(nbands, nroi, ncommands);


% ---- set up for running the commands

rmax   = fc_fisher(rmax);
aFz    = false;

if verbose
    fprintf('\n... computing GBC for %d ROI in %d bands', nroi, nbands);
end

coms = {commands.command};

% -- do we need absolute values?

if strfind(strjoin(coms), 'aFz')
    if time, fprintf(' aFz'); tic; end
    aFz = abs(Fz);
    if time fprintf(' [%.3f s]', toc); end
end

if time, fprintf(' clip'); tic; end
evoxels = nvox;
if rmax
    clip = Fz < rmax;
    Fz = Fz.*clip;
    evoxels = sum(clip,1);
    clipped = nvox - evoxels;
    if verbose == 3, fprintf(' cliped: %d ', sum(sum(clip))); end;
else
    clipped = 0;
    evoxels = nvox;
end
if time fprintf(' [%.3f s]', toc); end


% -------- Run the command loop ---------

for c = 1:ncommands
    tcommand   = commands(c).command;
    tparameter = commands(c).parameter;

    if time, fprintf(' %s', tcommand); tic; end

    for b = 1:nbands

        switch tcommand

            % .... recompute evoxels to reflect n for each roi ??????

            % ---> compute mFz

            case 'mFz'
                results(b,:,c) = rmean(Fz, md == b, 1);

            % ---> compute aFz

            case 'aFz'
                if tparameter == 0
                    results(b,:,c) = rmean(aFz, md == b, 1);
                else
                    results(b,:,c) = rmean(aFz, (aFz > tparameter & md == b), 1);
                end

            % ---> compute pFz

            case 'pFz'
                results(b,:,c) = rmean(r, (r >= tparameter & md == b), 1);


            % ---> compute pFz

            case 'nFz'
                results(b,:,c) = rmean(r, (r <= tparameter & md == b), 1);

            % ---> compute pD

            case 'pD'
                results(b,:,c) = rmean(r >= tparameter, md == b, 1);


            % ---> compute nD

            case 'nD'
                results(b,:,c) = rmean(r <= tparameter, md == b, 1);

            % ---> compute aD

            case 'aD'
                results(b,:,c) = rmean(aFz >= tparameter, md == b, 1);

        end

    end

    if time fprintf(' [%.3f s]', toc); end

end


if verbose, fprintf('\n... done! [%.3f s]', toc(stime)), end

roiinfo = roi.roi;

end

% ----------  helper functions
%
%   Input
%       - s   : string specifying the types of GBC to be done
%               individual types of GBC are to be pipe delimited, parmeters colon separated
%               format:
%               * GBC type - mFz, aFz, pFz, nFz, mD, aD, pD, nD
%                 ... to each of these either p or s can be added at the end, for
%                     computing results for proportion or strength bands respectively
%               * threshold to be used for the GBC
%                 ... or number of bins for proportion or strength range bands
%
%       - nvox : the number of voxels in the mask (necessary to compute bands for prange)
%
%   Output
%       - out  : vector of structure with fields
%                - command      ... type of GBC to run
%                - parameter    ... threshold or limits to be used
%                - volumes      ... how many volumes the results will span


function [out] = parseCommand(s, nvox)

    sortit = false;
    a = splitby(s,'|');
    for n = 1:length(a)
        b = splitby(a{n}, ':');
        com = b{1};
        par = str2num(b{2});
        out(n).command = com;
        out(n).parameter = fc_fisher(par);
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
end


function [matrix] = rmean(matrix, mask, dim)
    if nargin < 3, dim = 1; end
    matrix = matrix .* mask;
    matrix = sum(matrix, dim) ./ sum(mask, dim);
end

function [matrix] = rsum(matrix, mask, dim)
    if nargin < 3, dim = 1; end
    matrix = matrix .* mask;
    matrix = sum(matrix, dim);
end

function [s] = strjoin(c)
    s = '';
    for n = 1:length(c)
        s = [s c{n}];
    end
end
