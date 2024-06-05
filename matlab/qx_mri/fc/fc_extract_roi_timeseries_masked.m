function [data] = fc_extract_roi_timeseries_masked(flist, roiinfo, inmask, targetf, options, method, ignore, rcodes, mcodes, bmask)

%``fc_extract_roi_timeseries_masked(flist, roiinfo, inmask, targetf, options, method, ignore, rcodes, mcodes, bmask)``
%
%   Extracts and saves region timeseries defined by provided roiinfo file
%
%   NOTE: Please, note that fc_extract_roi_timeseries_masked function is being 
%         deprecated. The function will no longer be developed and will be 
%         removed in future releases of QuNex. Consider using 
%         fc_extract_roi_timeseries, which offers additional functionality, instead.
%
%   Parameters:
%       --flist (str):
%           A .list file, or a well strucutured string (see
%           general_read_file_list).
%
%       --roiinfo (str):
%           A .names ROI definition file.
%
%       --inmask (str, default ''):
%           Per run mask information:
%
%           - number of frames to skip or
%           - a vector of frames to keep (1) and reject (0) or
%           - a string describing which events to extract timeseries for and the
%             frame offset at start and end in format:
%             ``('title1:event1,event2:2:2|title2:event3,event4:1:2')``.
%
%       --targetf (str):
%           The name for the file to save timeseries in.
%
%       --options (str, default 'm'):
%           A string defining which outputs to create:
%
%           - t - create a tab delimited text file,
%           - m - create a matlab file.
%
%       --method (str, default 'mean'):
%           Method for extracting timeseries - 'mean', 'median', 'pca' or 'all'.
%
%       --ignore (str, default 'no'):
%           Do we omit frames to be ignored:
%
%           - no     - do not ignore any additional frames
%           - event  - ignore frames as marked in .fidl file
%           - other  - the column in ∗_scrub.txt file that matches bold file
%             to be used for ignore mask
%           - usevec - as specified in the use vector.
%
%       --rcodes (str | vector | cell array, default ''):
%           A list of region codes for which to extract the time-series.
%
%       --mcodes (str | vector | cell array, default specification from roiinfo):
%           A list of region codes from session's roi file to use for masking if
%           empty the specification from roiinfo will be used.
%
%       --bmask (bool, default false):
%           Should a BOLD brain mask be used to further mask the regions used.
%
%   Notes:
%       The function is used to extract ROI timeseries. What frames are
%       extracted can be specified using an event string. If specified, it uses
%       each session's .fidl file to extract only the specified event related
%       frames.
%
%       The string format is::
%
%           <title>:<eventlist>:<frame offset1>:<frame offset2>
%
%       and multiple extractions can be specified by separating them using the
%       pipe '|' separator. Specifically, for each extraction, all the events
%       listed in a comma-separated eventlist will be considered (e.g.
%       'task1,task2') and for each event all the frames starting from event
%       start + offset1 to event end + offset2 will be extracted and
%       concatenated into a single timeseries. Do note that the extracted frames
%       depend on the length of the event specified in the .fidl file!
%
%       The extracted timeseries can be saved either in a matlab file with
%       structure:
%
%       data.roinames
%           cell array of ROI names
%
%       data.roicodes1
%           array of group ROI codes
%
%       data.roicodes2
%           array of session specific ROI codes
%
%       data.sessions
%           cell array of session codes
%
%       data.n_roi_vox
%           cell array of number voxels for each ROI
%
%       data.datasets
%           cell array of titles for each of the dataset
%
%       data.<title>.timeseries
%           cell array of extracted timeseries
%
%       data.<title>.usevec
%           cell array of vectors of frames to use (i.e. not discarded after
%           movement scrubbing)
%
%       data.<title>.runframes
%           cell array of vectors with number of frames for each concatenated run
%
%       or in a tab separated text file in which data for each frame of each
%       session is in its own line, the first column is the session code, the
%       second the dataset title, the third the frame number and the following
%       columns are for each of the specified ROI. The ROI are listed in the
%       header.
%
%       ROI definition:
%           The basic definition of ROI to use is taken from roiinfo. Additional
%           masking is done using session specific ROI files as listed in the
%           .list file. With large number of regions, masking can time
%           consuming. If the same mask is used for all the ROI specified in the
%           roiinfo file (e.g. gray matter) then it is possible to specify the
%           relevant session specific mask codes using the mcodes paramater. In
%           this case the session specific part of the roiinfo will be ignored
%           and replaced by mcodes.
%
%   Examples:
%       Resting state data::
%
%           qunex fc_extract_roi_timeseries_masked \
%               --flist='con.list' \
%               --roiinfo='CCNet.names' \
%               --inmask=0 \
%               --targetf='con-ccnet' \
%               --options='mt' \
%               --method='mean' \
%               --ignore='udvarsme'
%
%       Event data::
%
%           qunex fc_extract_roi_timeseries_masked \
%               --flist='con.list' \
%               --roiinfo='CCNet.names' \
%               --inmask='inc:3:4' \
%               --targetf='con-ccnet-inc' \
%               --options='m' \
%               --method='pca' \
%               --ignore='event'
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 10 || isempty(bmask),  bmask   = false;  end
if nargin < 9, mcodes = []; end;
if nargin < 8, rcodes = []; end;
if nargin < 7 || isempty(ignore),  ignore  = 'no';   end
if nargin < 6 || isempty(method),  method  = 'mean'; end
if nargin < 5 || isempty(options), options = 'm';    end

verbose = true;  % ---> to be set by options in the future

fprintf('\nWARNING: Please, note that fc_extract_roi_timeseries_masked function is being deprecated.\n         The function will no longer be developed and will be removed in future releases of QuNex. \n         Consider using fc_extract_roi_timeseries, which offers additional functionality, instead');

if ~ischar(ignore)
    error('ERROR: Argument ignore has to be a string specifying whether and what to ignore!');
end


% ---> setting up inmask parameter

fignore = 'ignore';
eventbased = false;

if isa(inmask, 'char')
    inmask = str2num(inmask);
    if isempty(inmask)
        eventbased = true;
        if strcmp(ignore, 'fidl')
            fignore = 'ignore';
        else
            fignore = 'no';
        end
    end
end

%   ---- Named region codes

aparc.lcgray = [3 415 417 419 421:422 424 427 429 431 433 435 438 1000:1035 1100:1104 1200:1202 1205:1207 1210:1212 1105:1181 9000:9006 11100:11175];
aparc.rcgray = [42 416 418 420 423 425:426 428 430 432 434 436 439 2000:2035 2100:2104 2105:2181 2200:2202 2205:2207 2210:2212 9500:9506 12100:12175 ];
aparc.cgray  = [aparc.lcgray aparc.rcgray 220 222 225 226 400:414 437 ];

aparc.lsubc  = [9:13 17:20 26:28 96 136 163 169 193:196 550 552:557];
aparc.rsubc  = [48:56 58:60 97 137 164 176 197:200 500 502:507];
aparc.subc   = [aparc.lsubc aparc.rsubc 16 170:175 203:209 212 214:218 226 7001:7020 7100:7101 8001:8014 ];

aparc.lcerc  = [8 601 603 605 608 611 614 617 620 623 626 660:679];
aparc.rcerc  = [47 602 604 607 610 613 616 619 622 625 628 640:659];
aparc.cerc   = [aparc.lcerc aparc.rcerc 606 609 612 615 618 621 624 627];

aparc.lgray  = [aparc.lcgray aparc.lsubc aparc.lcerc];
aparc.rgray  = [aparc.rcgray aparc.rsubc aparc.rcerc];
aparc.gray   = [aparc.cgray aparc.subc aparc.cerc 702];

if isa(mcodes, 'char')  && ~isempty(mcodes)
    mcodes = aparc.(mcodes);
end

fprintf('\n\nStarting ...');

%   ------------------------------------------------------------------------------------------
%                                                      make a list of all the files to process

fprintf('\n ... listing files to process');

list = general_read_file_list(flist, 'all', [], verbose);

fprintf(' ... done.');

%   ------------------------------------------------------------------------------------------
%                                                                      parse events if present

if eventbased
    [ana fstring] = parseEvent(inmask);
    inmask   = [];
else
    ana.name = 'data';
    fstring  = '';
end
nana = length(ana);


%   ------------------------------------------------------------------------------------------
%                                                The main loop ... go through all the sessions

groi = nimage.img_read_roi(roiinfo);

for n = 1:list.nsessions

    fprintf('\n ... processing %s', list.session(n).id);

    % ---> reading image files

    fprintf('\n     ... reading image file(s)');

    y = nimage(list.session(n).files{1});
    for f = 2:length(list.session(n).files)
        y = [y nimage(list.session(n).files{f})];
    end

    fprintf(' ... %d frames read, done.', y.frames);




    % ---> creating per session ROI mask

    roi = groi;

    % -- mask with session's ROI file

    imask = ones(roi.voxels, 1);

    if isfield(list.session(n), 'roi')
        if isempty(mcodes)
            roi  = nimage.img_read_roi(roiinfo, list.session(n).roi);
        else
            sroi = nimage(list.session(n).roi);
            imask = imask & ismember(sroi.data, mcodes);
        end
    end

    % -- exclude voxels outside the BOLD brain mask

    if bmask
        imask = imask & img_BOLDBrainMask(list.session(n).files);
    end

    % -- exclude voxels with 0 variance

    istat = y.img_stats('var');
    imask = imask & istat.data;

    % -- apply mask

    if min(imask) == 0
        roi.data(imask == 0,:) = 0;
        for r = 1:length(roi.roi.roicodes)
            roi.roi.nvox(r) = sum(sum(roi.data==roi.roi.roicodes(r)));
        end
    end






    % ---> creating task mask

    if eventbased
        finfo = general_create_task_regressors(list.session(n).fidl, y.runframes, fstring, fignore);
        finfo = finfo.run;
        matrix = [];
        for r = 1:length(finfo)
            matrix = [matrix; finfo(r).matrix];
        end
    else
        matrix = inmask(:);
    end

    fprintf('\n     ... extracting timeseries [');

    for a = 1:nana

        % ---> slicing image

        fmask = matrix(:, a)';

        if length(fmask) == 1
            t = y.sliceframes(fmask, 'perrun');
        else
            t = y.sliceframes(fmask);                % this might need to be changed to allow for per run timeseries masks
        end

        % ---> remove additional frames to be ignored

        if ~ismember(ignore, {'no', 'fidl'})
            t = t.img_scrub(ignore);
        end

        % ---> extracting timeseries

        fprintf('%d ', t.frames);
        data.(ana(a).name).timeseries{n} = t.img_extract_roi(roi, rcodes, method);
        data.(ana(a).name).runframes{n}  = t.runframes;
        data.(ana(a).name).usevec{n}     = t.use;

    end

    fprintf('frames]');

    data.sessions{n}     = list.session(n).id;
    data.n_roi_vox(n, :) = roi.roi.nvox;

end

data.datasets  = {ana.name};
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
    fprintf(fout, 'session\tevent\tframe\tuse');
    for ir = 1:length(data.roinames)
        fprintf(fout, '\t%s', data.roinames{ir});
    end

    % ---> print data

    if strcmp(method, 'all')
        fprintf('WARNING: Export of textual data for all voxels in ROI not yet supported!');
    else
        for a = 1:nana
            for is = 1:list.nsessions
                ts = data.(ana(a).name).timeseries{is};
                usevec = data.(ana(a).name).usevec{is};
                tslen = size(ts, 2);
                for it = 1:tslen
                    fprintf(fout, '\n%s\t%s\t%d\t%d', data.sessions{is}, ana(a).name, it, usevec(it));
                    fprintf(fout, '\t%.5f', ts(:,it));
                end
            end
        end
    end

    % -- close file

    fclose(fout);
end

fprintf('\n\n FINISHED!\n\n');



%   ------------------------------------------------------------------------------------------
%                                                                 masking with BOLD brain mask

function [bmask] = img_BOLDBrainMask(fnames)

    bmasks = [];
    for fname = fnames
        fname = fname{1};
        if ~isempty(strfind(fname, '.conc'))
            [files boldn sfolder] = nimage.img_read_concfile(fname);

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
                bmask = [bmask nimage(sprintf('%s/segmentation/boldmasks/bold%d_frame1_brain_mask.nii.gz', sfolder{n}, boldn(n)))];
            end
            bmask = min(bmask.image2D, [], 2) > 0;
        else
            [pathstr name ext] = fileparts(fname);
            boldn = regexp(name, '^.*?([0-9]+).*', 'tokens');
            pathstr = strrep(pathstr, 'functional', '');
            bmask = nimage(sprintf('%ssegmentation/boldmasks/bold%s_frame1_brain_mask.nii.gz', pathstr, boldn{1}{1}));
            bmask = bmask.image2D > 0;
        end
        bmasks = [bmasks bmask];
    end
    bmask = min(bmasks, [], 2) > 0;

%   ------------------------------------------------------------------------------------------
%                                                                         event string parsing

function [ana, fstring] = parseEvent(event)

    smaps   = regexp(event, '\|', 'split');
    nsmaps  = length(smaps);
    fstring = '';
    for m = 1:nsmaps
        fields = regexp(smaps{m}, ':', 'split');
        ana(m).name = fields{1};
        fstring     = [fstring fields{2} ':block:' fields{3} ':' fields{4}];
        if m < nsmaps, fstring = [fstring '|']; end
    end


