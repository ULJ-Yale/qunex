function [fcmat] = fc_ComputeROICorrelations(bolds, roidef, frames, targetf, options)

%function [fcmat] = fc_ComputeROICorrelations(bolds, roidef, frames, targetf, options)
%
%   Computes seed based functional connectivity maps for individual subject / session.
%
%   INPUT
%   =====
%
%   bolds     - A string with a pipe separated list of paths to .conc or bold files. 
%               The first element has to be the name of the file or group to be used when saving the data. 
%               E.g.: 'rest|<path to rest file 1>|<path to rest file 2>'
%   roidef    - A path to the names file specifying group based seeds. Additionaly, separated by a pipe '|'
%               symbol, a path to an image file holding subject/session specific ROI definition.
%   frames    - The definition of which frames to extract, specifically:
%               ->  a numeric array mask defining which frames to use (1) and which not (0), or 
%               ->  a single number, specifying the number of frames to skip at the start of each bold, or
%               ->  a string describing which events to extract timeseries for, and the frame offset from 
%                   the start and end of the event in format: 
%                   '<fidlfile>|<extraction name>:<event list>:<extraction start>:<extraction end>') 
%                   where:
%                   -> fidlfile         ... is a path to the fidle file that defines the events    
%                   -> extraction name  ... is the name for the specific extraction definition    
%                   -> event list       ... is a comma separated list of events for which data is to be extracted    
%                   -> extraction start ... is a frame number relative to event start or end when the extraction should start    
%                   -> extraction end   ... is a frame number relative to event start or end when the extraction should start    
%                      the extraction start and end should be given as '<s|e><frame number>'. E.g.:
%                       s0  ... the frame of the event onset 
%                       s2  ... the second frame from the event onset 
%                       e1  ... the first frame from the event end 
%                       e0  ... the last frame of the event 
%                       e-2 ... the two frames before the event end
%                      example:
%                       '<fidlfile>|encoding:e-color,e-shape:s2:s2|delay:d-color,d-shape:s2:e0'
%   tagetf    - The folder to save images in ['.'].
%   options   - A string specifying additional analysis options formated as pipe separated pairs of colon separated
%               key, value pairs: "<key>:<value>|<key>:<value>"
%               It takes the following keys and values:
%               -> roimethod  ... what method to use to compute ROI signal, 'mean', 'median', or 'pca' ['mean']
%               -> eventdata  ... what data to use from each event:
%                                 -> all      ... use all identified frames of all events
%                                 -> mean     ... use the mean across frames of each identified event
%                                 -> min      ... use the minimum value across frames of each identified event
%                                 -> max      ... use the maximum value across frames of each identified event
%                                 -> median   ... use the median value across frames of each identified event
%                                 ['all']
%               -> ignore     ... a comma separated list of information to identify frames to ignore, options are:
%                                 -> use      ... ignore frames as marked in the use field of the bold file
%                                 -> fidl     ... ignore frames as marked in .fidl file (only available with event extraction)
%                                 -> <column> ... the column name in *_scrub.txt file that matches bold file to be used for ignore mask
%                                 ['use,fidl']
%               -> badevents  ... what to do with events that have frames marked as bad, options are:
%                                 -> use      ... use any frames that are not marked as bad
%                                 -> <number> ... use the frames that are not marked as bad if at least <number> ok frames exist
%                                 -> ignore   ... if any frame is marked as bad, ignore the full event
%                                 ['use']
%               -> fcmeasure  ... which functional connectivity measure to compute, the options are:
%                                 -> r        ... pearson's r value
%                                 -> cv       ... covariance estimate
%                                 ['r']
%               -> saveind    ... a comma separted list of formats to use to save the data
%                                 -> txt      ... save the resulting data in a long format txt file
%                                 -> mat      ... save the resulting data in a matlab .mat file
%                                 ['']
%               -> verbose    ... Whether to be verbose 'true' or not 'false', when running the analysis ['false']
%
%   RESULTS
%   =======
%
%   The method returns a structure array with the following fields for each specified
%   data extraction:
%
%   fcmat
%        -> title ... the title of the extraction as specifed in the frames string, 
%                     empty if extraction was specified using a numeric value 
%        -> fc    ... functional connectivity matrix
%        -> roi   ... a cell array with the names of the ROI used in the order 
%                     of columns & rows in the functional connectivity matrix
%        -> N     ... number of frames over which the matrix was computed
%
%   Based on saveind option specification a file may be saved with the functional connectivity
%   data saved in a matlab.mat file and/or in a text long format:
%
%   <targetf>/<name>_<cor|cov>.<txt|mat>
%
%   <name> is the provided name of the bold(s).
%
%   The text file will have the following columns (depending on the fcmethod):
%   
%   -> name
%   -> title
%   -> roi1
%   -> roi2
%   -> cv
%   -> r
%   -> Fz
%   -> Z
%   -> p
%   
%
%   USE
%   ===
% 
%   The function computes functional connectivity matrices for the specified ROI. 
%   If an event string is provided, it has to start with a path to the .fidl file 
%   to be used to extract the events, following by a pipe separated list of event 
%   extraction definitions:
%
%   <title>:<eventlist>:<frame offset1>:<frame offset2>
%
%   multiple extractions can be specified by separating them using the pipe '|' 
%   separator. Specifically, for each extraction, all the events listed in a
%   comma-separated eventlist will be considered (e.g. 'congruent,incongruent'). 
%   For each event all the frames starting from the specified beginning and ending
%   offset will be extracted. If options eventdata is specified as 'all', all the
%   specified frames will be concatenated in a single timeseries, otherwise, each
%   event will be summrised by a single frame in a newly generated events series image.
%   
%   From the resulting image, ROI series will be extracted for each specified ROI as 
%   specified by the roimethod option. A functional connectivity matrix between ROI
%   will be computed.
%
%   The results will be returned in a fcmat structure and, if so specified, saved.
%   
%
%   EXAMPLE USE
%   ===========
%
%
%   ---
%   Written by Grega Repovš 2020-02-03.
%
%   Changelog
%

if nargin < 5 || isempty(options), options = '';  end
if nargin < 4 || isempty(targetf), targetf = '.'; end
if nargin < 3 frames  = []; end
if nargin < 2 error('ERROR: At least boldlist and ROI .names file have to be specified!'); end

% ----- parse options

default = 'roimethod=mean|eventdata=all|ignore=use,fidl|badevents=use|fcmeasure=r|saveind=none|verbose=false|debug=false';
options = g_ParseOptions([], options, default);

verbose = strcmp(options.verbose, 'true');
printdebug = strcmp(options.debug, 'true');

if printdebug
    g_PrintStruct(options, 'Options used');
end

if ~ismember(options.eventdata, {'all', 'mean', 'min', 'max', 'median'})
    error('ERROR: Invalid eventdata option: %s', options.eventdata);
end

if ~ismember(options.roimethod, {'mean', 'pca', 'median'})
    error('ERROR: Invalid roi extraction method: %s', options.roimethod);
end

if ~ismember(options.fcmeasure, {'r', 'cv'})
    error('ERROR: Invalid functional connectivity computation method: %s', options.fcmeasure);
end

% ----- What should be saved

options.saveind = strtrim(regexp(options.saveind, ',', 'split'));
sdiff = setdiff(options.saveind, {'mat', 'txt', ''});
if ~isempty(sdiff)
    error('ERROR: Invalid save format specified: %s', strjoin(sdiff,","));
end

% ----- Get the list of files

[name, bolds] = strtok(bolds, '|');
bolds = bolds(2:end);
boldlist = strtrim(regexp(bolds, '\|', 'split'));

[roiinfo, sroifile] = strtok(roidef, '|');
if sroifile
    sroifile = sroifile(2:end);
else
    sroifile = [];
end


% ----- Check if the files are there!

go = true;
if verbose; fprintf('\nChecking ...\n'); end

for bold = boldlist
    go = go & g_CheckFile(bold{1}, bold{1}, 'error');
end
go = go & g_CheckFile(roiinfo, 'ROI definition file', 'error');
if sroifile
    go = go & g_CheckFile(sroifile, 'individual ROI file', 'error');
end
if any(ismember({'txt', 'mat'}, options.saveind))
    g_CheckFolder(targetf, 'results folder', true, verbose);
end

if ~go
    error('ERROR: Some files were not found. Please check the paths and start again!\n\n');
end


%   ------------------------------------------------------------------------------------------
%                                                                            do the processing

if verbose; fprintf('     ... creating ROI mask\n'); end

roi  = nimage.img_ReadROI(roiinfo, sroifile);
nroi = length(roi.roi.roinames);


% ---> reading image files

if verbose; fprintf('     ... reading image file(s)'); end
y = nimage(bolds);
if verbose; fprintf(' ... %d frames read, done.\n', y.frames); end


% ---> create extraction sets

if verbose; fprintf('     ... generating extraction sets ...'); end
exsets = y.img_GetExtractionMatrices(frames, options);
if verbose; fprintf(' done.\n'); end

% ---> loop through extraction sets

if verbose; fprintf('     ... computing fc matrices\n'); end

nsets = length(exsets);
for n = 1:nsets

    if verbose; fprintf('         ... set %s', exsets(n).title); end
    
    % --> get the extracted timeseries

    ts = y.img_ExtractTimeseries(exsets(n).exmat, options.eventdata);

    if verbose; fprintf(' ... extracted ts'); end
    
    % --> generate fc matrice

    rs = ts.img_ExtractROI(roi, [], options.roimethod);

    if strcmp(options.fcmeasure, 'cv')
        fc = rs';
        fc = bsxfun(@minus, fc', mean(fc)) ./ sqrt(ts.voxels-1);
        fc = fc' * fc;
    else
        fc = zscore(rs', 0, 1);
        fc = fc ./ sqrt(ts.frames -1);
        fc = fc' * fc;
    end
    
    if verbose; fprintf(' ... computed fc matrix'); end

    % ------> Embedd results

    fcmat(n).title = exsets(n).title;
    fcmat(n).roi   = roi.roi.roinames;
    fcmat(n).N     = ts.frames;

    if strcmp(options.fcmeasure, 'cv')
        fcmat(n).cv = fc;
    else
        fcmat(n).r  = fc;
        fcmat(n).fz = fc_Fisher(fc);
        fcmat(n).z  = fcmat(n).fz/(1/sqrt(fcmat(n).N-3));
        fcmat(n).p  = (1 - normcdf(abs(fcmat(n).z), 0, 1)) * 2 .* sign(fcmat(n).fz);
    end

    if verbose; fprintf(' ... embedded\n'); end
end


% ---> save results

if ~any(ismember({'mat', 'txt'}, options.saveind))
    if verbose; fprintf(' ... done\n'); end
    return; 
end

if verbose; fprintf('     ... saving results\n'); end

ftail = {'cor', 'cov'};
ftail = ftail{ismember({'r', 'cv'}, options.fcmeasure)};

basefilename = fullfile(targetf, sprintf('%s_%s', name, ftail));

if ismember({'mat'}, options.saveind)
    if verbose; fprintf('         ... saving mat file'); end
    save(basefilename, 'fcmat');
    if verbose; fprintf(' ... done\n'); end
end

if ismember({'txt'}, options.saveind)
    
    if verbose; fprintf('         ... saving txt file'); end

    fout = fopen([basefilename '.txt'], 'w');

    if strcmp(options.fcmeasure, 'cv')
        fprintf(fout, 'name\ttitle\troi1\troi2\tcv\n');
    else
        fprintf(fout, 'name\ttitle\troi1\troi2\tr\tFz\tZ\tp\n');
    end

    for n = 1:nsets
        if fcmat(n).title, settitle = fcmat(n).title; else settitle = 'ts'; end

        % --- set ROI names

        nroi = length(fcmat(n).roi);

        idx1 = repmat([1:nroi], nroi, 1);
        idx1 = tril(idx1, -1);
        idx1 = idx1(idx1 > 0);

        idx2 = repmat([1:nroi]', 1, nroi);
        idx2 = tril(idx2, -1);
        idx2 = idx2(idx2 > 0);

        roi1 = fcmat(n).roi(idx1);
        roi2 = fcmat(n).roi(idx2);

        idx  = reshape([1:nroi*nroi], nroi, nroi);
        idx  = tril(idx, -1);
        idx  = idx(idx > 0);        

        nfc  = length(idx);

        % --- write up

        if strcmp(options.fcmeasure, 'cv')
            cv = fcmat(n).cv(idx);
            for c = 1:nfc
                fprintf(fout, '%s\t%s\t%s\t%s\t%.5f\n', name, settitle, roi1{c}, roi2{c}, cv(c));
            end
        else
            r  = fcmat(n).r(idx);
            fz = fcmat(n).fz(idx);
            z  = fcmat(n).z(idx);
            p  = fcmat(n).p(idx);
            for c = 1:nfc
                fprintf(fout, '%s\t%s\t%s\t%s\t%.5f\t%.5f\t%.5f\t%.7f\n', name, settitle, roi1{c}, roi2{c}, r(c), fz(c), z(c), p(c));
            end
        end
    end
    fclose(fout);
    if verbose; fprintf(' ... done\n'); end
end

if verbose; fprintf(' ... done\n'); end
