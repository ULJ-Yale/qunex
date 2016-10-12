function [data] = g_ExtractROIGLMValues(flist, roif, outf, estimates, frames, values, tformat, verbose);

%function function [] = g_ExtractROIGLMValues(flist, roif, estimates, frames, values, tformat, verbose);
%
%	Extracts statistics from GLM files provided in a file list.
%
%   flist       - list of files
%   roif        - names ROI file
%   outf        - name of the output file [list + .dat]
%   estimates   - list of estimates of interest [all but trend and baseline]
%   frames      - list of frames [all]
%   values 	    - whether to work on raw beta values ('raw') or percent signal change ('psc') ['raw']
%   tformat     - what format to use: a combination of 'mat', 'wide', 'long'
%	verbose		- to report on progress or not [not]
%
% 	Created by Grega Repovš on 2015-12-09.
%
%   Changelog
%   - 2016-09-25 Grega Repovš: added option of wide and mat
%
% 	Copyright (c) 2015 Grega Repovs. All rights reserved.
%
%   ToDo
%   — selection of stats to save
%   — additional info (roi xyz, peak value ...)
%

if nargin < 8, verbose   = false; end
if nargin < 7 || isempty(tformat), tformat = 'wide,long,mat'; end
if nargin < 6 || isempty(values), values = 'raw'; end
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
    outf = [flist '_' values];
end

ltext = false;
wtext = false;

if ~isempty(strfind(tformat, 'long'))
    ltext = fopen([outf '_long.txt'], 'w');
    fprintf(ltext, 'subject\troi\troicode\tevent\tframe\tmin\tmax\tmean\tmedian\tsd\tse\tN');
end
if ~isempty(strfind(tformat, 'wide'))
    wtext = fopen([outf '_wide.txt'], 'w');
    fprintf(wtext, 'subject\tevent\tframe');
    for r = 1:nroi
        fprintf(wtext, '\t%s', roi.roi.roinames{r});
    end
end



% --------------------------------------------------------------
%                                          loop through subjects

for s = 1:nsub

    % ---> read GLM

    if verbose, fprintf('\n---> processing subject: %s', subjects(s).id); end

    % glm = gmrimage(subjects(s).glm, [], [], verbose);
    glm = gmrimage(subjects(s).glm);
    glm = glm.mri_ExtractGLMEstimates(estimates, frames);

    % ---> update ROI

    if isfield(subjects(s), 'roi') && ~isempty(subjects(s).roi)
        sroi = roi.mri_MaskROI(subjects(s).roi);
    else
        sroi = roi;
    end

    if strcmp(values, 'psc')
        glm.data = bsxfun(@rdivide, glm.data, glm.glm.gmean / 100);
    end

    stats   = glm.mri_ExtractROIStats(sroi);
    data(s).stats = stats;
    data(s).effect = glm.glm.effects(glm.glm.effect);
    data(s).frame = glm.glm.eindex;

    nframes = length(stats(1).mean);

    if ltext
        for r = 1:nroi
            for f = 1:nframes
                fprintf(ltext, '\n%s\t%s\t%d\t%s\t%d\t%.3f\t%.3f\t%.3f\t%.3f\t%.3f\t%.3f\t%d', subjects(s).id, stats(r).roiname, stats(r).roicode, glm.glm.effects{glm.glm.effect(f)}, glm.glm.frame(f), stats(r).min(f), stats(r).max(f), stats(r).mean(f), stats(r).median(f), stats(r).sd(f), stats(r).se(f), stats(r).N);
            end
        end
    end
    if wtext
        for f = 1:nframes
            fprintf(wtext, '\n%s\t%s\t%s', subjects(s).id, glm.glm.effects{glm.glm.effect(f)}, glm.glm.eindex(f));
            for r = 1:nroi
                fprintf(wtext, '\t%.3f', stats(r).mean(f));
            end
        end
    end
end

if ltext, fclose(ltext); end
if wtext, fclose(wtext); end

if ~isempty(strfind(tformat, 'mat'))
    save([outf '.mat'], 'data');
end

if verbose, fprintf('\n===> DONE\n'); end


