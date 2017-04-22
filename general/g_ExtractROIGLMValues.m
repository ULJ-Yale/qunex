function [data] = g_ExtractROIGLMValues(flist, roif, outf, effects, frames, values, tformat, verbose);

%function function [] = g_ExtractROIGLMValues(flist, roif, effects, frames, values, tformat, verbose);
%
%	Extracts per ROI estimates of specified effects from a volume or cifti GLM
%   files as specified in the file list.
%
%   INPUT
%       flist       - List of subjects and files to process.
%       roif        - .names ROI file descriptor.
%       outf        - Name of the output file. If left empty the it is set to
%                     flist root with '.dat' extension. []
%       effects     - List of effects of interest. If none specified, all but
%                     trend and baseline are exported. []
%       frames      - List of frames to extract from all effects. All if empty
%                     or not specified. []
%       values 	    - In what form to extract the estimates. Possibilities are
%                     raw beta values ('raw') or percent signal change ('psc')
%                     values. ['raw']
%       tformat     - A comma separated string specifying in what format the
%                     data is to be extracted. It can be a combination of:
%                     'mat'  -> a matlab file,
%                     'wide' -> wide format txt file with one line per subject
%                               and each ROI and estimate in a separate column,
%                     'long' -> long format txt file with one line per estimate
%                               extracted with columns describing the subject,
%                               ROI, effect and frame that it belongs to.
%                               The minimum, maximum, median, standard
%                               deviation, and standard error of the values
%                               within the ROI are reported, as well as the
%                               number of effective voxelx within the ROI.
%	    verbose		- Whether to report on progress or not. [not]
%
%   OUTPUT
%   The results are saved in the specified file but also returned in a
%   datastructure.
%
%   USE
%   The function is used to extract per ROI estimates of the effects of interest
%   for each of the ROI and subjects to enable second level analysis and
%   visualization of the data. In the background the function first extracts the
%   relevant volumes using the mri_ExtractGLMEstimates. It then defines the ROI
%   and uses mri_ExtractROIStats method to get per ROI statistics.
%
%   EXAMPLE USE
%   >>> g_ExtractROIGLMValues('wm-glm.list', 'CCN.names', [], 'encoding, delay', [], 'psc', 'long');
%
%   ---
% 	Written by Grega Repovš on 2015-12-09.
%
%   Changelog
%   2016-09-25 Grega Repovš - Added option of wide and mat target format.
%   2017-03-04 Grega Repovš - Updated documentation.
%
%   ToDo
%   — selection of stats to save
%   — additional info (roi xyz, peak value ...)
%

if nargin < 8, verbose = false; end
if nargin < 7 || isempty(tformat), tformat = 'wide,long,mat'; end
if nargin < 6 || isempty(values), values = 'raw'; end
if nargin < 5, frames  = [];    end
if nargin < 4, effects = [];    end
if nargin < 3, outf    = [];    end

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
    glm = glm.mri_ExtractGLMEstimates(effects, frames);

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


