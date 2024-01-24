function [fcmats] = fc_compute_roifc(flist, roiinfo, frames, targetf, options)

%``fc_compute_roifc(flist, roiinfo, frames, targetf, options)``
%
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 5 || isempty(options), options = '';  end
if nargin < 4 || isempty(targetf), targetf = '.'; end
if nargin < 3 frames  = []; end
if nargin < 2 error('ERROR: At least file list and ROI .names file have to be specified!'); end

% --------------------------------------------------------------
%                                              parcel processing

parcels = {};

if startsWith(roiinfo, 'parcels:')
    parcels = strtrim(regexp(roiinfo(9:end), ',', 'split'));
end

% ----- parse options

default = 'sessions=all|roimethod=mean|eventdata=all|ignore=use,fidl|badevents=use|fcmeasure=r|savegroup=none|saveind=none|savesessionid=true|itargetf=gfolder|verbose=false|debug=false|fcname=|verbose=true|debug=false';
options = general_parse_options([], options, default);

verbose     = strcmp(options.verbose, 'true');
printdebug  = strcmp(options.debug, 'true');
addidtofile = strcmp(options.savesessionid, 'true') || strcmp(options.itargetf, 'gfolder');
gem_options = sprintf('ignore:%s|badevents:%s|verbose:%s|debug:%s', options.ignore, options.badevents, options.verbose, options.debug);
fcmeasure   = options.fcmeasure;

if ~general_check_fcargs(options)
    error('ERROR: Invalid arguments for the fc measure: %s: ', fcmeasure);
end

if options.fcname, fcname = [options.fcname, '_']; else fcname = ''; end

if printdebug
    general_print_struct(options, 'fc_compute_roifc_options used');
end

if ~ismember(options.eventdata, {'all', 'mean', 'min', 'max', 'median'})
    error('ERROR: Invalid eventdata option: %s', options.eventdata);
end

if ~ismember(options.roimethod, {'mean', 'pca', 'median', 'min', 'max'})
    error('ERROR: Invalid roi extraction method: %s', options.roimethod);
end

if ~ismember(options.fcmeasure, {'r', 'cv', 'rho', 'cc', 'icv', 'mi', 'mar', 'coh'})
    error('ERROR: Invalid functional connectivity computation method: %s', options.fcmeasure);
end

% ----- What should be saved

% --> individual data

options.saveind = strtrim(regexp(options.saveind, ',', 'split'));
if ismember({'none'}, options.saveind)
    options.saveind = {};
end
sdiff = setdiff(options.saveind, {'mat', 'long', 'wide_single', 'wide_separate', ''});
if ~isempty(sdiff)
    error('ERROR: Invalid individual save format specified: %s', strjoin(sdiff,","));
end

% --> group data

options.savegroup = strtrim(regexp(options.savegroup, ',', 'split'));
if ismember({'none'}, options.savegroup)
    options.savegroup = {};
end
sdiff = setdiff(options.savegroup, {'mat', 'all_long', 'all_wide_single', 'all_wide_separate', 'mean_long', 'mean_wide_single', 'mean_wide_separate', ''});
if ~isempty(sdiff)
    error('ERROR: Invalid group save format specified: %s', strjoin(sdiff,","));
end

% ----- Check if the files are there!

go = true;
if verbose; fprintf('\nChecking ...\n'); end

% - check for presence of listfile unless the list is provided as a string
if ~startsWith(flist, 'listname:')    
    go = go & general_check_file(flist, 'image file list', 'error');
end

% - check for presence of ROI specification file if we are not using parcells
if isempty(parcels)
    go = go & general_check_file(roiinfo, 'ROI definition file', 'error');
end

% - check for presence of target folder no data needs to be saved there
if ~isempty(options.savegroup) || (~isempty(options.saveind) && strcmp(options.itargetf, 'sfolder'))
    general_check_folder(targetf, 'results folder');
end

if ~go
    error('ERROR: Some files were not found. Please check the paths and start again!\n\n');
end


%   ------------------------------------------------------------------------------------------
%                                                      make a list of all the files to process

fprintf(' ... listing files to process');

list = general_read_file_list(flist, options.sessions, [], verbose);

lname = strrep(list.listname, '.list', '');
lname = strrep(lname, '.conc', '');
lname = strrep(lname, '.4dfp', '');
lname = strrep(lname, '.img', '');

fprintf(' ... done.\n');


%   ------------------------------------------------------------------------------------------
%                                                The main loop ... go through all the sessions

first_subject = true;
oksub         = zeros(1, length(list.session));
embed_data    = nargout > 0 || ~isempty(options.savegroup);

for s = 1:list.nsessions

    go = true;

    if verbose; fprintf('\n---------------------------------\nProcessing session %s', list.session(s).id); end
    
    % ---> check roi files

    if isfield(list.session(s), 'roi')
        go = go & general_check_file(list.session(s).roi, [list.session(s).id ' individual ROI file'], 'error');
        sroifile = list.session(s).roi;
    else
        sroifile = [];
    end

    % ---> check bold files

    if isfield(list.session(s), 'conc') && ~isempty(list.session(s).conc)
        go = go & general_check_file(list.session(s).conc, 'conc file', 'error');
        bolds = general_read_concfile(list.session(s).conc);
    elseif isfield(list.session(s), 'files') && ~isempty(list.session(s).files) 
        bolds = list.session(s).files;
    else
        fprintf(' ... ERROR: %s missing bold or conc file specification!\n', list.session(s).id);
        go = false;
    end    

    for bold = bolds
        go = go & general_check_file(bold{1}, 'bold file', 'error');
    end

    reference_file = bolds{1};

    % ---> setting up frames parameter

    if isempty(frames)
        frames = 0;
    elseif isa(frames, 'char')
        frames = str2num(frames);        
        if isempty(frames) 
            if isfield(list.session(s), 'fidl')
                go = go & general_check_file(list.session(s).fidl, [list.session(s).id ' fidl file'], 'error');
            else
                go = false;
                fprintf(' ... ERROR: %s missing fidl file specification!\n', list.session(s).id);
            end
        end
    end

    if ~go, continue; end

    % ---> setting up target folder and name for individual data

    if strcmp(options.itargetf, 'sfolder')
        stargetf = fileparts(reference_file);
        if endsWith(stargetf, '/concs')
            stargetf = strrep(stargetf, '/concs', '');
        end
    else
        stargetf = targetf;
    end
    subjectid = list.session(s).id;

    % ---> reading image files

    if verbose; fprintf('     ... reading image file(s)'); end
    if iscell(bolds)
        bolds = strjoin(bolds, '|');
    end
    y = nimage(bolds);
    y.data = y.image2D;
    if verbose; fprintf(' ... %d frames read, done.\n', y.frames); end

    % ---> processing roi/parcels info

    if isempty(parcels)
        if verbose; fprintf('     ... creating ROI mask\n'); end
        roi = nimage.img_read_roi(roiinfo, sroifile);
        roi.data = roi.image2D;    
    else
        if ~isfield(y.cifti, 'parcels') || isempty(y.cifti.parcels)
            error('ERROR: The bold file lacks parcel specification! [%s]', list.session(s).id);
        end
        if length(parcels) == 1 && strcmp(parcels{1}, 'all')        
            parcels = y.cifti.parcels;
        end
        roi.roi.roinames = parcels;
        [x, roi.roi.roicodes] = ismember(parcels, y.cifti.parcels);
    end

    roinames = roi.roi.roinames;
    roicodes = roi.roi.roicodes;
    nroi = length(roi.roi.roinames);
    nparcels = length(parcels);

    % ---> create extraction sets

    if verbose; fprintf('     ... generating extraction sets\n'); end
    exsets = y.img_get_extraction_matrices(frames, gem_options);
    for n = 1:length(exsets)
        if verbose; fprintf('         -> %s: %d good events, %d good frames\n', exsets(n).title, size(exsets(n).exmat, 1), sum(exsets(n).estat)); end
    end

    % ---> loop through extraction sets

    if verbose; fprintf('     ... computing fc matrices\n'); end

    nsets = length(exsets);
    for n = 1:nsets        
        if verbose; fprintf('         ... set %s', exsets(n).title); end
        
        % --> get the extracted timeseries
    
        ts = y.img_extract_timeseries(exsets(n).exmat, options.eventdata);
    
        if verbose; fprintf(' ... extracted ts'); end
        
        % --> generate fc matrice
        
        if isempty(parcels)
            rs = ts.img_extract_roi(roi, [], options.roimethod);
        else
            rs = ts.img_extract_roi(roiinfo, [], options.roimethod); 
        end
    
        options
        fc = fc_compute(rs, [], fcmeasure, false, options);
        
        if verbose; fprintf(' ... computed fc matrix'); end
    
        % ------> store 
        
        if first_subject
            fcmat(n).title     = exsets(n).title;
            fcmat(n).roi       = roi.roi.roinames;
            fcmat(n).subjects = {};
        end

        fcmat(n).subjects = {subjectid};
        fcmat(n).fc.(fcmeasure) = fc;
        fcmat(n).fc.N = ts.frames;

        if ismember(fcmeasure, {'r', 'rho', 'coh'})
            fcmat(n).fc.fz = fc_fisher(fc);
            fcmat(n).fc.z  = fcmat(n).fc.fz/(1/sqrt(fcmat(n).fc.N - 3));
            fcmat(n).fc.p  = (1 - normcdf(abs(fcmat(n).fc.z), 0, 1)) * 2 .* sign(fcmat(n).fc.fz);
        end

        if embed_data
            if first_subject
                fcmats(n).title     = exsets(n).title;
                fcmats(n).roi       = roi.roi.roinames;
                fcmats(n).subjects = {};
            end
            fcmats(n).subjects(s) = {subjectid};
            fcmats(n).fc(s).(fcmeasure) = fc;
            fcmats(n).fc(s).N = ts.frames;
            if ismember(fcmeasure, {'r', 'rho', 'coh'})
                fcmats(n).fc(s).fz = fcmat(n).fc.fz;
                fcmats(n).fc(s).z  = fcmat(n).fc.z;
                fcmats(n).fc(s).p  = fcmat(n).fc.p;
            end
        end 
    end
    
    % ===================================================================================================
    %                                                                             save individual results

    if ~any(ismember({'mat', 'long', 'wide_single', 'wide_separate'}, options.saveind))
        if verbose; fprintf(' ... done\n'); end
        continue; 
    end

    if verbose; fprintf('     ... saving results\n'); end

    % set subjectname

    if addidtofile
        subjectname = [list.session(s).id, '_'];
    else
        subjectname = '';
    end

    basefilename = fullfile(stargetf, sprintf('roifc_%s_%s%s%s', lname, fcname, subjectname, fcmeasure));

    for save_format = options.saveind
        switch save_format{1}
            case 'mat'
                if verbose; fprintf('         ... saving mat file'); end
                save(basefilename, 'fcmat');
                if verbose; fprintf(' ... done\n'); end
            case 'long'
                save_long(fcmat, fcmeasure, lname, basefilename, verbose, printdebug);
            case 'wide_separate'
                save_wide(fcmat, fcmeasure, lname, basefilename, true, verbose, printdebug);
            case 'wide_single'
                save_wide(fcmat, fcmeasure, lname, basefilename, false, verbose, printdebug);
        end
    end        

    first_subject = false;
end


% ===================================================================================================
%                                                                                  save group results

% --> save results

if ~isempty(options.savegroup)
    if verbose; fprintf('\n---------------------------------\nProcessing group data\n'); end
end

basefilename = fullfile(targetf, sprintf('roifc_%s_%s%s', lname, fcname, fcmeasure));

for save_format = options.savegroup
    switch save_format{1}
        case 'mat'
            if verbose; fprintf('         ... saving mat file'); end
            fcmat = fcmats;
            save(basefilename, 'fcmat');
            if verbose; fprintf(' ... done\n'); end
        case 'all_long'
            save_long(fcmats, fcmeasure, lname, basefilename, verbose, printdebug);
        case 'all_wide_separate'
            save_wide(fcmats, fcmeasure, lname, basefilename, true, verbose, printdebug);
        case 'all_wide_single'
            save_wide(fcmats, fcmeasure, lname, basefilename, false, verbose, printdebug);
    end
end  


% -------------------------------------------------------------------------------------------
%                                                  support function for saving in long format 

function [] = save_long(fcmat, fcmeasure, lname, basefilename, verbose, printdebug)

    if verbose; fprintf('         ... saving long tsv file'); end
    if printdebug; fprintf([' ' basefilename '_long.tsv']); end

    fout = fopen([basefilename '_long.tsv'], 'w');

    if ismember(fcmeasure, {'cv', 'icv', 'mi', 'mar', 'cc'})
        fprintf(fout, 'name\ttitle\tsubject\troi1_name\troi2_name\t%s\n', fcmeasure);
    else
        fprintf(fout, 'name\ttitle\tsubject\troi1_name\troi2_name\t%s\tFz\tZ\tp\n', fcmeasure);
    end

    for n = 1:length(fcmat)
        if fcmat(n).title, settitle = fcmat(n).title; else settitle = 'ts'; end

        % --- set ROI names

        nroi = length(fcmat(n).roi);

        idx1 = repmat([1:nroi], nroi, 1);
        idx1 = tril(idx1, -1);
        idx1 = idx1(idx1 > 0);

        idx2 = repmat([1:nroi]', 1, nroi);
        idx2 = tril(idx2, -1);
        idx2 = idx2(idx2 > 0);

        roi1name = fcmat(n).roi(idx1);
        roi2name = fcmat(n).roi(idx2);

        idx  = reshape([1:nroi*nroi], nroi, nroi);
        idx  = tril(idx, -1);
        idx  = idx(idx > 0);        

        nfc  = length(idx);

        % --- write up
        
        for s = 1:length(fcmat(n).subjects)
            if ismember(fcmeasure, {'cv', 'icv', 'mi', 'mar', 'cc'})
                fc = fcmat(n).fc(s).(fcmeasure)(idx);
                for c = 1:nfc
                    fprintf(fout, '%s\t%s\t%s\t%s\t%s\t%.5f\n', lname, settitle, fcmat(n).subjects{s}, roi1name{c}, roi2name{c}, fc(c));
                end
            elseif ismember(fcmeasure, {'r', 'rho', 'coh'})
                fc = fcmat(n).fc(s).(fcmeasure)(idx);
                fz = fcmat(n).fc(s).fz(idx);
                z  = fcmat(n).fc(s).z(idx);
                p  = fcmat(n).fc(s).p(idx);
                for c = 1:nfc
                    fprintf(fout, '%s\t%s\t%s\t%s\t%s\t%.5f\t%.5f\t%.5f\t%.7f\n', lname, settitle, fcmat(n).subjects{s}, roi1name{c}, roi2name{c}, fc(c), fz(c), z(c), p(c));
                end
            end
        end
    end
    fclose(fout);
    if verbose; fprintf(' ... done\n'); end

% -------------------------------------------------------------------------------------------
%                                                        support function for printing header 

function [] = printHeader(fout, roinames)
    fprintf(fout, 'name\ttitle\tsubject\tmeasure\troiname');
    nroi = length(roinames);
    for r = 1:nroi
        fprintf(fout, '\t%s', roinames{r});
    end


% -------------------------------------------------------------------------------------------
%                                                  support function for saving in wide format 
function [] = save_wide(fcmat, fcmeasure, lname, basefilename, separate, verbose, printdebug);

    if verbose; fprintf('         ... saving wide tsv file'); end

    nroi = length(fcmat(1).roi);
    roi  = fcmat(1).roi;
    
    if printdebug; fprintf([' ' basefilename '_wide.tsv']); end
    fout_fc = fopen([basefilename '_wide.tsv'], 'w');
    printHeader(fout_fc, roi);
    toclose = [fout_fc];

    if separate && ismember(fcmeasure, {'r', 'rho', 'coh'}) 
        if printdebug; fprintf([' ' basefilename '_Fz_wide.tsv']); end
        fout_Fz = fopen([basefilename '_Fz_wide.tsv'], 'w');
        printHeader(fout_Fz, roi);
        toclose = [toclose fout_Fz];
    else
        fout_Fz = fout_fc;
    end

    for n = 1:length(fcmat)
        if fcmat(n).title, settitle = fcmat(n).title; else settitle = 'ts'; end
        for s = 1:length(fcmat.subjects)
            for r = 1:nroi
                fprintf(fout_fc,'\n%s\t%s\t%s\t%s\t%s\t%d', lname, settitle, fcmat(n).subjects{s}, fcmeasure, roi{r});
                fprintf(fout_fc, '\t%.7f', fcmat(n).fc(s).(fcmeasure)(r, :));
            end
            if ismember(fcmeasure, {'r', 'rho', 'coh'})
                for r = 1:nroi
                    fprintf(fout_Fz, '\n%s\t%s\t%s\t%s\t%s\t%d', lname, settitle, fcmat(n).subjects{s}, 'fz', roi{r});
                    fprintf(fout_Fz, '\t%.7f', fcmat(n).fc(s).fz(r, :));
                end
            end
        end
    end

    for f = toclose
        fclose(f);
    end
    
    if verbose; fprintf(' ... done\n'); end        
