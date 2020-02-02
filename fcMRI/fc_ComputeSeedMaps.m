function [fcmaps] = fc_ComputeSeedMaps(bolds, roidef, frames, targetf, options)

%function [fcmaps] = fc_ComputeSeedMaps(bolds, roidef, frames, targetf, options)
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
%               -> roimethod ... what method to use to compute ROI signal, 'mean', 'median', or 'pca' ['mean']
%               -> eventdata ... what data to use from each event:
%                                -> all      ... use all identified frames of all events
%                                -> mean     ... use the mean across frames of each identified event
%                                -> min      ... use the minimum value across frames of each identified event
%                                -> max      ... use the maximum value across frames of each identified event
%                                -> median   ... use the median value across frames of each identified event
%                                ['all']
%               -> ignore    ... a comma separated list of information to identify frames to ignore, options are:
%                                -> use      ... ignore frames as marked in the use field of the bold file
%                                -> fidl     ... ignore frames as marked in .fidl file (only available with event extraction)
%                                -> <column> ... the column name in *_scrub.txt file that matches bold file to be used for ignore mask
%                                ['use,fidl']
%               -> badevents ... what to do with events that have frames marked as bad, options are:
%                                -> use      ... use any frames that are not marked as bad
%                                -> <number> ... use the frames that are not marked as bad if at least <number> ok frames exist
%                                -> ignore   ... if any frame is marked as bad, ignore the full event
%                                ['use']
%               -> fcmeasure ... which functional connectivity measure to compute, the options are:
%                                -> r        ... pearson's r value
%                                -> cv       ... covariance estimate
%                                ['r']
%               -> saveind   ... a comma separted list of individual session / subject files to save
%                                -> r        ... save Pearson correlation coefficients (r only)
%                                -> fz       ... save Fisher Z values (r only)
%                                -> z        ... save Z statistic (r only)
%                                -> p        ... save p value (r only)
%                                -> cv       ... save covariances (cv only)
%                                -> all      ... save all relevant values
%                                -> none     ... do not save any individual level results
%                                ['none']
%                                Default is 'none'. Any invalid options will be ignored without a warning.
%               -> verbose   ... Whether to be verbose 'true' or not 'false', when running the analysis ['false']
%
%   RESULTS
%   =======
%
%   The method returns a structure array with the following fields for each specified
%   data extraction:
%
%   fcmaps
%        -> title ... the title of the extraction as specifed in the frames string, 
%                     empty if extraction was specified using a numeric value 
%        -> fc    ... the functional connectivity map, with one seed-map per frame
%        -> roi   ... a cell array with the names of the ROI used in the order 
%                     of their seed-maps in the fc image
%        -> N     ... number of frames over which the map was computed
%
%   Based on saveind option specification the following files may be saved:
%
%   <targetf>/<name>[_<title>]_<roi>_r  ... Pearson correlations
%   <targetf>/<name>[_<title>]_<roi>_Fz ... Fisher Z values
%   <targetf>/<name>[_<title>]_<roi>_Z  ... Z converted p values testing difference from 0.
%   <targetf>/<name>[_<title>]_<roi>_p  ... p values testing difference from 0.
%
%   <targetf>/<name>[_<title>]_<roi>_cv ... covariance
%
%   <roi> is the name of the ROI for which the seed map was computed for.
%   <name> is the provided name of the bold(s).
%   <title> is the title of the extraction event(s), if event string was
%   specified.
%
%   USE
%   ===
% 
%   The function computes seed maps for the specified ROI. If an event string is
%   provided, it has to start with a path to the .fidl file to be used to extract 
%   the events, following by a pipe separated list of event extraction definitions:
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
%   specified by the roimethod option. A seed-map will be computed for each ROI where
%   for each voxel or grayordinate, a correlation or covariance of its dataseries with 
%   the ROI will be entered.
%
%   The results will be returned in a fcmaps structure and, if so specified, saved.
%   
%
%   EXAMPLE USE
%   ===========
%
%
%   ---
%   Written by Grega Repovš 2020-02-02.
%
%   Changelog
%

if nargin < 5 || isempty(options), options = '';  end
if nargin < 4 || isempty(targetf), targetf = '.'; end
if nargin < 3 frames  = []; end
if nargin < 2 error('ERROR: At least boldlist and ROI .names file have to be specified!'); end

% ----- parse options

default = 'roimethod=mean|eventdata=all|ignore=use,fidl|badevents=use|fcmeasure=r|saveind=none|verbose=false';
options = g_ParseOptions([], options, default);

verbose = strcmp(options.verbose, 'true')

% g_PrintStruct(options, 'Options used');

if ~ismember(options.eventdata, {'all', 'mean', 'min', 'max', 'median'})
    error('ERROR: Invalid eventdata option: %s', options.eventdata);
end

if ~ismember(options.roimethod, {'mean', 'pca', 'median'})
    error('ERROR: Invalid roi extraction method: %s', options.roimethod);
end

if ~ismember(options.fcmethod, {'r', 'cv'})
    error('ERROR: Invalid functional connectivity computation method: %s', options.fcmethod);
end

% ----- What should be saved

options.saveind = strtrim(regexp(options.saveind, ',', 'split'));

if ismember({'none'}, options.saveind)
    options.saveind = '';
elseif ismember({'all'}, options.saveind)
    options.saveind = {'r', 'fz', 'z', 'p', 'cv'};
end

if options.saveind 
    if strcmp(options.fcmethod, 'r')
        options.saveind = intersect(options.saveind, {'r', 'fz', 'z', 'p'})
    else
        options.saveind = intersect(options.saveind, {'cv'})
    end
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
if verbose; fprintf('\n\nChecking ...\n'); end

for bold = boldlist
    go = go & g_CheckFile(bold{1}, bold{1}, 'error');
end
go = go & g_CheckFile(roiinfo, 'ROI definition file', 'error');
if sroifile
    go = go & g_CheckFile(sroifile, 'individual ROI file', 'error');
end
g_CheckFolder(targetf, 'results folder');

if ~go
    error('ERROR: Some files were not found. Please check the paths and start again!\n\n');
end


%   ------------------------------------------------------------------------------------------
%                                                                            do the processing

if verbose; fprintf('\n     ... creating ROI mask'); end

roi  = gmrimage.mri_ReadROI(roiinfo, sroifile);
nroi = length(roi.roi.roinames);


% ---> reading image files

if verbose; fprintf('\n     ... reading image file(s)'); end
y = gmrimage(bolds);
if verbose; fprintf(' ... %d frames read, done.', y.frames); end


% ---> create extraction sets

exsets = y.mri_GetExtractionMatrices(frames, options);

% ---> loop through extraction sets

nsets = length(exsets);
for n = 1:nsets

    % --> get the extracted timeseries

    ts = y.mri_ExtractTimeseries(exmat, options.eventdata);
    
    % --> generate seedmaps

    rs = ts.mri_ExtractROI(roi, [], options.roimethod);
    fc = t.mri_ComputeCorrelations(rs', [], strcmp(options.fcmethod, 'cv'));

    % ------> Embedd results

    fcmaps(n).title = exsets(n).title;
    fcmaps(n).fc    = fc;
    fcmaps(n).roi   = roi.roi.roinames;
    fcmaps(n).N     = ts.frames;

end


% ---> save individual results

if options.saveind

    % --- loop through sets

    for n = 1:nsets
        if fcmaps(n).title, settitle = ['_' fcmaps(n).title]; else settitle = ''; end

        % --- loop through roi

        for r = 1:nroi

            % --- prepare basename

            basefilename = sprintf('seed_%s%s_%s', name, settitle, fcmaps(n).roi{r});

            % --- prepare computed data
            
            if any(ismember(options.saveind, {'fz', 'p', 'Z'}))
                fz = fcmaps(n).fc;
                fz.data = fc_Fisher(fz.data);
            end

            if any(ismember(options.saveind, {'p', 'Z'}))
                Z = fcmaps(n).fc;
                Z.data = fz.data/(1/sqrt(fcmaps(n).N-3));
            end

            if ismember('p', options.saveind)
                p = fcmaps(n).fc;
                p.data = (1 - normcdf(abs(Z.data), 0, 1)) * 2 .* sign(fz.data);
            end

            % --- save images

            for sn = 1:length(options.saveind)
                switch options.saveind{sn}
                    case 'r'
                        fcmaps(n).fc.mri_saveimage([basefilename '_r']);
                    case 'fz'
                        fz.mri_saveimage([basefilename '_Fz']);
                    case 'z'
                        Z.mri_saveimage([basefilename '_Z']);
                    case 'p'
                        p.mri_saveimage([basefilename '_p']);
                    case 'fz'
                        fcmaps(n).fc.mri_saveimage([basefilename '_cov']);                    
                end
            end
        end
    end
end
