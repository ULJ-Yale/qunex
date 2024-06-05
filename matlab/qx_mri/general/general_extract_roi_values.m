function [report] = general_extract_roi_values(roif, mfs, sefs, vnames, output, stats, verbose)

%``general_extract_roi_values(roif, mfs, sefs, vnames, output, stats, verbose)``
%
%   Extracts desired statistics from provided files for each ROI.
%
%   Parameters:
%       --roif (str):
%           ROI file, either a names file or a mask file.
%
%       --mfs (str):
%           Comma separated list of files to extract values from.
%
%       --sefs (str, default ''):
%           Optional list of comma separate files that hold SE for value files.
%
%       --vnames (str, default ''):
%           Optional comma separated list of value names to use for each of the
%           files.
%
%       --output (str, default ''):
%           Comma separated list of files to save to. If a file contains the
%           word long, it will save the data in a long format. By default it
%           saves the data in a wide format.
%
%       --stats (str, default 'rsize, rmean, mean'):
%           A comma separated list of the statistics to save:
%
%           - 'rsize'   ... size of ROI in voxels
%           - 'rmean'   ... location of the geometric mean of the ROI
%           - 'rpeak'   ... location of the peak value of the ROI
%           - 'rmin'    ... location of the minimum value in the ROI
%           - 'rmax'    ... location of the maxumal value in the ROI
%           - 'mean'    ... mean of values across ROI
%           - 'median'  ... median value across ROI
%           - 'min'     ... minimum value across ROI
%           - 'max'     ... mamimum value across ROI
%           - 'peak'    ... peak value in the ROI (largest absolute value).
%
%       --verbose (bool, default false):
%           To report on progress or not.
%
%   Returns:
%       report
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 7, verbose = false; end
if nargin < 6 || isempty(stats),  stats   = 'rsize, rmean, mean';    end
if nargin < 5, output  = [];    end
if nargin < 4, vnames  = [];    end
if nargin < 3, sefs    = [];    end

if nargin < 2, error('ERROR: No files to extract the values from provided!');  end
if nargin < 1, error('ERROR: No ROI provided for value extraction!');          end



% --------------------------------------------------------------
%                                                       read roi

roi = nimage.img_prep_roi(roif);


% --------------------------------------------------------------
%                                                   set up stats

nroi     = length(roi.roi);

stats    = regexp(stats, ',', 'split');
nstats   = length(stats);

for n = 1:length(stats)
    stats{n} = strtrim(stats{n});
end

if length(roi.dim) == 1
    if length(intersect(stats, {'rpeak', 'rmin', 'rmax', 'rsize', 'rmean'})) > 1
        error('ERROR: Statistics related to ROI geometry are only supported for volume images!');
    end
end

vstats   = intersect(stats, {'mean', 'median', 'min', 'max', 'peak'});
vstatsn  = length(vstats);

vlstats  = intersect(stats, {'rpeak', 'rmin', 'rmax'});
vlstatsn = length(vlstats);

rstats   = intersect(stats, {'rsize', 'rmean'});
rstatsn  = length(rstats);

if ismember('rsize', stats)
    rsize = zeros(nroi, 1);
else
    rsize = [];
end

if ismember('rmean', stats)
    rmean = zeros(nroi, 3);
else
    rmean = [];
end


% --------------------------------------------------------------
%                                                     read files

mfs    = regexp(mfs, ',', 'split');
nfiles = length(mfs);
seimg  = [];
frames = [];

if ~isempty(sefs)
    sefs  = regexp(sefs, ',', 'split');
    if nfiles ~= length(sefs);
        error('\nERROR: Number of SE files does not match number of value files!');
    end
end

if ~isempty(vnames)
    vnames = regexp(vnames, ',', 'split');
    if nfiles ~= length(vnames);
        error('\nERROR: Number of variable names does not match number of value files!');
    end
    createnames = false;
else
    vnames = {};
    createnames = true;
end

for n = 1:nfiles
    mfs{n}    = strtrim(mfs{n});
    mimg(n)   = nimage(mfs{n});
    mimg(n).data = mimg(n).image2D;
    frames(n) = mimg(n).frames;
    if vstatsn, vdata{n}  = zeros([nroi, frames(n), vstatsn]); end
    if vlstatsn, vldata{n} = zeros([nroi, frames(n), vstatsn, 3]); end
    if ~isempty(sefs)
        sefs{n}  = strtrim(sefs{n});
        seimg(n) = nimage(sefs{n});
        seimg(n).data = seimg(n).image2D;
        if vstatsn, sedata{n} = zeros([nroi, frames(n), vstatsn]); end
        if frames(n) ~= seimg(n).frames
            error('\nERROR: Number of frames in %s does not match number of frames in %s!', sefs{n}, mfs{n});
        end
    end
    if createnames
        vnames{n} = ['V' num2str(n)];
    else
        vnames{n} = strtrim(vnames{n});
    end
end



% --------------------------------------------------------------
%                                                       the loop

for roin = 1:nroi
    roicode = roi.roi(roin).roicode;
    rids    = roi.roi(roin).indeces;

    for rstat = 1:rstatsn
        switch rstats{rstat}
            case 'rsize'
                rsize(roin) = length(rids);
            case 'rmean'
                rmean(roin, :) = mean(getXYZ(rids, roi.dim));
        end
    end

    for filen = 1:nfiles
        for framen = 1:frames(filen)
            for vstat = 1:vstatsn

                tvdata = mimg(filen).data(rids, framen);
                if ~isempty(sefs)
                    tsedata = seimg(filen).data(rids, framen);
                end

                switch vstats{vstat}

                    case 'mean'
                        vdata{filen}(roin, framen, vstat) = mean(tvdata);
                        if ~isempty(sefs)
                            sedata{filen}(roin, framen, vstat) = mean(tsedata);
                        end

                    case 'median'
                        vdata{filen}(roin, framen, vstat) = median(tvdata);
                        if ~isempty(sefs)
                            sedata{filen}(roin, framen, vstat) = median(tsedata);
                        end

                    case 'min'
                        vdata{filen}(roin, framen, vstat) = min(tvdata);
                        if ~isempty(sefs)
                            sedata{filen}(roin, framen, vstat) = tsedata(find(tvdata==vdata{filen}(roin, framen, vstat), 'first'));
                        end

                    case 'max'
                        vdata{filen}(roin, framen, vstat) = max(tvdata);
                        if ~isempty(sefs)
                            sedata{filen}(roin, framen, vstat) = tsedata(find(tvdata==vdata{filen}(roin, framen, vstat), 'first'));
                        end

                    case 'peak'
                        tmin = min(tvdata);
                        tmax = max(tvdata);
                        if abs(tmax) > abs(tmin)
                            vdata{filen}(roin, framen, vstat) = tmax;
                        else
                            vdata{filen}(roin, framen, vstat) = tmin;
                        end
                        if ~isempty(sefs)
                            sedata{filen}(roin, framen, vstat) = tsedata(find(tvdata==vdata{filen}(roin, framen, vstat), 'first'));
                        end

                    case 'rmin'
                        vldata{filen}(roin, framen, vstat,:) = getXYZ(rids(find(tvdata==min(tvdata), 'first')), dim);

                    case 'rmax'
                        vldata{filen}(roin, framen, vstat,:) = getXYZ(rids(find(tvdata==max(tvdata), 'first')), dim);

                    case 'rpeak'
                        tmin = min(tvdata);
                        tmax = max(tvdata);
                        if abs(tmax) > abs(tmin)
                            tpeak = tmax;
                        else
                            tpeak = tmin;
                        end
                        vldata{filen}(roin, framen, vstat,:) = getXYZ(rids(find(tvdata==tpeak, 'first')), dim);
                end
            end
        end
    end
end



% --------------------------------------------------------------
%                                                       printout

outputs = regexp(output, ',', 'split');
for output = outputs
    output = strtrim(output{1});

    fout = fopen(output, 'w');

    if strfind(output, 'long')

        % --- print header
        %
        % roi, variable, frame, [roi_size], [roi_xyz], [vlstats ...], vstats, [vstats_se]


        fprintf(fout, 'roi');
        if ~isempty(rsize), fprintf(fout, '\troi_size'); end
        if ~isempty(rmean), fprintf(fout, '\troi_xyz'); end

        fprintf(fout, '\tvariable\tframe\tvar_frame');
        if ~isempty(vlstats), for vlstat = vlstats, fprintf(fout, '\t%s', vlstat{1}); end; end
        for vstat = vstats, fprintf(fout, '\t%s', vstat{1}); end
        if ~isempty(sefs), for vstat = vstats, fprintf(fout, '\t%s_se', vstat{1}); end; end

        % --- print values

        for r = 1:nroi
            sroidata = sprintf('\n%s', roi.roi(r).roiname);
            if ~isempty(rsize), sroidata = [sroidata sprintf('\t%d', rsize(r))]; end
            if ~isempty(rmean), sroidata = [sroidata sprintf('\t(%.1f, %.1f, %.1f)', rmean(r,:))]; end

            for filen = 1:nfiles
                for framen = 1:frames(filen)
                    fprintf(fout, '%s\t%s\t%d\t%s_%d', sroidata, vnames{filen}, framen, vnames{filen}, framen);

                    for vlstat = 1:vlstatsn
                        fprintf(fout, '\t(%d, %d, %d)', vldata{filen}(r, framen, vlstat, :));
                    end

                    for vstat = 1:vstatsn
                        fprintf(fout, '\t%f', vdata{filen}(r, framen, vstat));
                    end
                    if ~isempty(sefs)
                        for vstat = 1:vstatsn
                            fprintf(fout, '\t%f', sedata{filen}(r, framen, vstat));
                        end
                    end
                end
            end
        end


    else

        % --- print header

        fprintf(fout, 'roi');
        if ~isempty(rsize), fprintf(fout, '\troi_size'); end
        if ~isempty(rmean), fprintf(fout, '\troi_xyz'); end
        for filen = 1:nfiles
            for vstat = vstats
                if frames(filen) == 1
                    fprintf(fout, '\t%s_%s', vnames{filen}, vstat{1});
                else
                    for framen = 1:frames(filen)
                        fprintf(fout, '\t%s_f%d_%s', vnames{filen}, framen, vstat{1});
                    end
                end
            end
            if ~isempty(sefs)
                for vstat = vstats
                    if frames(filen) == 1
                        fprintf(fout, '\tse_%s_%s', vnames{filen}, vstat{1});
                    else
                        for framen = 1:frames(filen)
                            fprintf(fout, '\tse_%s_f%d_%s', vnames{filen}, framen, vstat{1});
                        end
                    end
                end
            end
            for vlstat = vlstats
                if frames(filen) == 1
                    fprintf(fout, '\t%s_%s', vnames{filen}, vlstat{1});
                else
                    for framen = 1:frames(filen)
                        fprintf(fout, '\t%s_f%d_%s', vnames{filen}, framen, vlstat{1});
                    end
                end
            end
        end

        % --- print values

        for r = 1:nroi

            fprintf(fout, '\n%s', roi.roi(r).roiname);
            if ~isempty(rsize), fprintf(fout, '\t%d', rsize(r)); end
            if ~isempty(rmean), fprintf(fout, '\t(%.1f, %.1f, %.1f)', rmean(r,:)); end
            for filen = 1:nfiles
                for vstat = 1:vstatsn
                    for framen = 1:frames(filen)
                        fprintf(fout, '\t%f', vdata{filen}(r, framen, vstat));
                    end
                end
                if ~isempty(sefs)
                    for vstat = 1:vstatsn
                        for framen = 1:frames(filen)
                            fprintf(fout, '\t%f', sedata{filen}(r, framen, vstat));
                        end
                    end
                end
                for vlstat = 1:vlstatsn
                    for framen = 1:frames(filen)
                        fprintf(fout, '\t(%d, %d, %d)', vldata{filen}(r, framen, vlstat, :));
                    end
                end
            end
        end
    end

    fclose(fout);
end



% ======================================================
%   ---> get XYZ voxel indices
%

function [xyz] = getXYZ(id, dim)

    z  = floor(id / prod(dim(1:2))) + 1;
    id = mod(id, prod(dim(1:2)));
    y  = floor(id / dim(1)) + 1;
    x  = mod(id, dim(1));

    xyz = [x y z];
