function [data] = fc_ExtractROITimeseriesMasked(flist, roiinfo, inmask, targetf, options, method, ignore, rcodes, mcodes, bmask)

%function [data] = fc_ExtractROITimeseriesMasked(flist, roiinfo, inmask, targetf, options, method, ignore, rcodes, mcodes, bmask)
%
%	Extracts and saves region timeseries defined by provided roiinfo file
%
%   INPUTS
%	    flist   	- A .list file.
%	    roiinfo	    - A .names ROI definition file.
%       inmask      - Per run mask information, number of frames to skip or a vector of frames to keep (1) and reject (0),
%                     or a string with definition used to extract event-defined timepoints only
%	    tagetf		- The name for the file to save timeseries in.
%       options     - A string defining which outputs to create ['m']:
%                     -> t - create a tab delimited text file,
%                     -> m - create a matlab file
%       method      - Method for extracting timeseries - 'mean', 'pca' ['mean'].
%       ignore      - do we omit frames to be ignored ['no']:
%                     -> no:     do not ignore any additional frames
%                     -> event:  ignore frames as marked in .fidl file
%                     -> other:  the column in *_scrub.txt file that matches bold file to be used for ignore mask
%                     -> usevec: as specified in the use vector
%       rcodes      - A list of region codes for which to extract the time-series [].
%       mcodes      - A list of region codes from subject's roi file to use for masking if empty the specification from
%                     roiinfo will be used.
%       bmask       - Should a BOLD brain mask be used to further mask the regions used [false].
%
%   USE
%   The function is used to extract ROI timeseries. What frames are extracted
%   can be further limited by providing an event string that is tham parsed
%   using g_CreateTaskRegressors and all frames with regressors that have
%   values above 0 are extracted. The extracted timeseries can be saved either
%   in a matlab file with structure:
%
%   data.roinames   ... cell array of ROI names
%   data.roicodes1  ... array of group ROI codes
%   data.roicodes2  ... arrau of subject specific ROI codes
%   data.subjects   ... cell array of subject codes
%   data.timeseries ... cell array of extracted timeseries
%   data.n_roi_vox  ... cell array of number voxels for each ROI
%
%   or in a tab separated text file in which data for each frame of each subject
%   is in its own line, the first column is the subject code and the following
%   columns are for each of the specified ROI. The ROI are listed in the header.
%
%   *ROI definition*
%   The basic definition of ROI to use is taken from roiinfo. Additional masking
%   is done using subject specific ROI files as listed in the .list file. With
%   large number of regions, masking can time consuming. If the same mask is
%   used for all the ROI specified in the roiinfo file (e.g. gray matter) then
%   it is possible to specify the relevant subject specific mask codes using
%   the mcodes paramater. In this case the subject specific part of the roiinfo
%   will be ignored and replaced by mcodes.
%
%   It is also possible to use
%
%
%   EXAMPLE USE
%   Resting state data:
%   >>>fc_ExtractROITimeseriesMasked('con.list', 'CCNet.names', 0, 'con-ccnet', 'mt', 'mean', 'udvarsme');
%
%   Event data:
%   >>>fc_ExtractROITimeseriesMasked('con.list', 'CCNet.names', 'inc:3:4', 'con-ccnet-inc', 'm', 'pca', 'event');
%
%
%   ---
% 	Written by Grega Repovš, 2009-06-25.
%   2008-01-23 Grega Repovs
%            - Adjusted for a different file list format and an additional ROI mask
%   2011-02-11 Grega Repovs
%            - Rewritten to use gmrimage objects and ability for event defined masks
%   2012-07-30 Grega Repovs
%            - Added option to omit frames specified to be ignored in the fidl file
%   2013-12-11 Grega Repovs
%            - Added ignore as specified in use vector and rcodes to specify ROI.
%   2017-03-19 Grega Repovs
%            - Updated documentation
%   2017-03-21 Grega Repovs
%            - Optimized per subject masking of ROI.
%

if nargin < 10 || isempty(bmask),  bmask   = false;  end
if nargin < 9, mcodes = []; end;
if nargin < 8, rcodes = []; end;
if nargin < 7 || isempty(ignore),  ignore  = 'no';   end
if nargin < 6 || isempty(method),  method  = 'mean'; end
if nargin < 5 || isempty(options), options = 'm';    end

if ~ischar(ignore)
    error('ERROR: Argument ignore has to be a string specifying whether and what to ignore!');
end

eventbased = false;
if isa(inmask, 'char')
    eventbased = true;
    if strcmp(ignore, 'fidl')
        fignore = 'ignore';
    else
        fignore = 'no';
    end
end

%   ---- Named region codes

aparc.lcgray = [3 415 417 419 421:422 424 427 429 431 433 435 438 11100:11175 1000:1035 1100:1104 1200:1202 1205:1207 1210:1212 1105:1181];
aparc.rcgray = [42 416 418 420 423 425:426 428 430 432 434 436 439 12100:12175 2000:2035 2100:2104 2105:2181 2200:2202 2205:2207 2210:2212];
aparc.cgray  = [aparc.lcgray aparc.rcgray 220 222 225 400:414 437];

aparc.lsubc  = [9:13 17:20 26 27 96 193 195:196 9000:9006 550 552:557];
aparc.rsubc  = [48:56 58:59 97 197 199:200 9500:9506 500 502:507];
aparc.subc   = [aparc.lsubc aparc.rsubc 16 170:175 203:209 212 214:218 226 7001:7020 7100:7101 8001:8014];

aparc.lcerc  = [8 601 603 605 608 611 614 617 620 623 626 660:679];
aparc.rcerc  = [47 602 604 607 610 613 616 619 622 625 628 640:659];
aparc.cerc   = [aparc.lcerc aparc.rcerc 606 609 612 615 618 621 624 627];

aparc.lgray  = [aparc.lcgray aparc.lsubc aparc.lcerc];
aparc.rgray  = [aparc.rcgray aparc.rsubc aparc.rcerc];
aparc.gray   = [aparc.cgray aparc.subc aparc.cerc];

if isa(mcodes, 'char')
    mcodes = aparc.(mcodes);
end

fprintf('\n\nStarting ...');

%   ------------------------------------------------------------------------------------------
%                                                      make a list of all the files to process

fprintf('\n ... listing files to process');

subject = g_ReadFileList(flist);
nsub = length(subject);

fprintf(' ... done.');

%   ------------------------------------------------------------------------------------------
%                                                         set up datastructure to save results

for n = 1:nsub
    data.subjects{n} = subject(n).id;
    data.timeseries{n} = [];
end


%   ------------------------------------------------------------------------------------------
%                                                The main loop ... go through all the subjects

groi = gmrimage.mri_ReadROI(roiinfo);

for n = 1:nsub

    fprintf('\n ... processing %s', subject(n).id);

    % ---> reading image files

    fprintf('\n     ... reading image file(s)');

    y = gmrimage(subject(n).files{1});
    for f = 2:length(subject(n).files)
        y = [y gmrimage(subject(n).files{f})];
    end

    fprintf(' ... %d frames read, done.', y.frames);

	% ---> creating timeseries mask

	if eventbased
	    mask = [];
	    if isfield(subject(n), 'fidl')
            if subject(n).fidl
                mask = g_CreateTaskRegressors(subject(n).fidl, y.runframes, inmask, fignore);
                mask = mask.run;
    	        nmask = [];
                for r = 1:length(mask)
                    nmask = [nmask; sum(mask(r).matrix,2) > 0];
                end
                mask = nmask;
            end
        end
    else
        mask = inmask;
    end

    % ---> slicing image

    if length(mask) == 1
        y = y.sliceframes(mask, 'perrun');
    else
        y = y.sliceframes(mask);                % this might need to be changed to allow for per run timeseries masks
    end

    % ---> remove additional frames to be ignored

    if ~ismember(ignore, {'no', 'fidl'})
        y = y.mri_Scrub(ignore);
    end

    % ---> creating ROI mask

    fprintf('\n     ... creating ROI mask');

    roi = groi;

    mask = ones(roi.voxels, 1);

    % -- mask with subject's ROI file

    if isfield(subject(n), 'roi')
        if isempty(mcodes)
            roi  = gmrimage.mri_ReadROI(roiinfo, subject(n).roi);
        else
            sroi = gmrimage.mri_ReadROI(subject(n).roi);
            mask = mask & sroi.mri_ROIMask(mcodes);
        end
    end

    % -- exclude voxels with 0 variance

    istat = y.mri_Stats('var');
    mask = mask & istat.data;

    % -- exclude voxels outside the BOLD brain mask

    if bmask
        mask = mask & mri_BOLDBrainMask(subject(n).files);
    end

    % -- apply mask

    if min(mask) == 0
        roi.data(mask == 0,:) = 0;
        for r = 1:length(roi.roi.roicodes)
            roi.roi.nvox(r) = sum(sum(roi.data==roi.roi.roicodes(r)));
        end
    end


	% ---> extracting timeseries

	fprintf('\n     ... extracting timeseries [%d frames]', y.frames);

    data.subjects{n}     = subject(n).id;
    data.timeseries{n}   = y.mri_ExtractROI(roi, rcodes, method);
    data.n_roi_vox(n, :) = roi.roi.nvox;

    fprintf(' ... done!');

end

data.roinames  = roi.roi.roinames;
data.roicodes1 = roi.roi.roicodes1;
data.roicodes2 = roi.roi.roicodes2;



%   -------------------------------------------------------------
%                                                       save data

fprintf('... saving ...');

if ismember('m', options)
    save(targetf, 'data');
end

if ismember('t', options)

    % ---> open file and print header

    [fout message] = fopen([targetf '.txt'],'w');
    fprintf(fout, 'subject');
    for ir = 1:length(data.roinames)
        fprintf(fout, '\t%s', data.roinames{ir});
    end

    % ---> print data

    for is = 1:nsub
        ts = data.timeseries{is};
        tslen = size(ts, 2);
        for it = 1:tslen
            fprintf(fout, '\n%s', data.subjects{is});
            fprintf(fout, '\t%.5f', ts(:,it));
        end
    end

    % -- close file

    fclose(fout);
end

fprintf('\n\n FINISHED!\n\n');




function [bmask] = mri_BOLDBrainMask(conc)

    [files boldn sfolder] = gmrimage.mri_ReadConcFile(conc);

    mask = boldn > 0;
    for n = 1:length(boldn)
        if isempty(sfolder{n})
            mask(n) = false;
        end
    end

    boldn   = boldn(mask);
    sfolder = sfolder(mask);
    nfiles  = length(boldn);

    bmask = [];
    for n = 1:nfiles
        bmask = [bmask gmrimage(sprintf('%s/segmentation/boldmasks/bold%d_frame1_brain_mask.nii.gz', sfolder{n}, boldn(n)))];
    end
    bmask = min(bmask.image2D, [], 2) > 0;

