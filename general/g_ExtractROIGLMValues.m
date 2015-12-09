function [report] = g_ExtractROIGLMValues(flist, roif, outf, estimates, frames, verbose);

%function function [report] = g_ExtractROIGLMValues(flist, roif, estimates, frames, verbose);
%
%	Extracts statistics from GLM files provided in a file list.
%
%   flist       - list of files
%   roif        - names ROI file
%   outf        - name of the output file [list + .dat]
%   estimates 	- list of estimates of interest [all but trend and baseline]
%   frames      - list of frames [all]
%
%	verbose		- to report on progress or not [not]
%
% 	Created by Grega Repovš on 2015-12-09.
%
% 	Copyright (c) 2015 Grega Repovs. All rights reserved.
%
%   ToDo
%   — selection of stats to save
%   — additional info (roi xyz, peak value ...)
%

if nargin < 6, verbose   = false; end
if nargin < 5, frames    = [];    end
if nargin < 4, estimates = [];    end
if nargin < 3, outf      = [];    end

if nargin < 2, error('ERROR: No ROI provided for value extraction!');          end
if nargin < 1, error('ERROR: No files to extract the values from provided!');  end

% --------------------------------------------------------------
%                                                    check files

g_CheckFile(flist, 'file list', 'errorstop');
g_CheckFile(roif, 'ROI image', 'errorstop');

% --------------------------------------------------------------
%                                                  read filelist

subjects = g_ReadFileList(flist);
nsub = length(subjects);

% --------------------------------------------------------------
%                                                       read roi

roi = gmrimage.mri_ReadROI(roif);
roi.data = roi.image2D;
nroi = length(roi.roi.roinames);

% --------------------------------------------------------------
%                                             create output file

if isempty(outf)
    outf = [flist '.dat'];
end

rfile = fopen(outf, 'w');
fprintf(rfile, 'subject\troi\troicode\tevent\tframe\tmin\tmax\tmean\tmedian\tsd\tse\tN');


% --------------------------------------------------------------
%                                          loop through subjects

for s = 1:nsub

    % ---> read GLM

    if verbose, fprintf('\n---> processing subject: %s', subjects(s).id); end

    glm = gmrimage(subjects(s).glm);
    glm = glm.mri_ExtractGLMEstimates(estimates, frames);

    % ---> update ROI

    if isfield(subjects(s), 'roi') && ~isempty(subjects(s).roi)
        sroi = roi.mri_MaskROI(subjects(s).roi);
    else
        sroi = roi;
    end

    stats   = glm.mri_ExtractROIStats(sroi);
    nframes = length(stats(1).mean);

    for r = 1:nroi
        for f = 1:nframes
            fprintf(rfile, '\n%s\t%s\t%d\t%s\t%d\t%.3f\t%.3f\t%.3f\t%.3f\t%.3f\t%.3f\t%d', subjects(s).id, stats(r).roiname, stats(r).roicode, glm.glm.effects{glm.glm.effect(f)}, glm.glm.eindex(f), stats(r).min(f), stats(r).max(f), stats(r).mean(f), stats(r).median(f), stats(r).sd(f), stats(r).se(f), stats(r).N);
        end
    end
end

fclose(rfile)

if verbose, fprintf('\n===> DONE\n'); end

report = [];

