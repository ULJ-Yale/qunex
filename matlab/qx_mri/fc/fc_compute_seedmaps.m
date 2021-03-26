function [fcmaps] = fc_compute_seedmaps(bolds, roiinfo, frames, targetf, options)

%``function [fcmaps] = fc_compute_seedmaps(bolds, roiinfo, frames, targetf, options)``
%
%   Computes seed based functional connectivity maps for individual subject / 
%   session.
%
%   INPUTS
%   ======
%
%   --bolds     A string with a pipe separated list of paths to .conc or bold 
%               files. The first element has to be the name of the file or group 
%               to be used when saving the data. E.g.::
%
%                   'rest|<path to rest file 1>|<path to rest file 2>'
%
%   --roiinfo   A path to the names file specifying group based seeds. Additionally, 
%               separated by a pipe '|' symbol, a path to an image file holding 
%               subject/session specific ROI definition.
%   --frames    The definition of which frames to extract, specifically:
%
%               - a numeric array mask defining which frames to use (1) and 
%                 which not (0), or 
%               - a single number, specifying the number of frames to skip at 
%                 the start of each bold, or
%               - a string describing which events to extract timeseries for, 
%                 and the frame offset from the start and end of the event in 
%                 format::
% 
%                     '<fidlfile>|<extraction name>:<event list>:<extraction start>:<extraction end>') 
%
%                 where:
%
%                 fidlfile         
%                     is a path to the fidle file that defines the events    
%                 extraction name  
%                     is the name for the specific extraction definition    
%                 event list       
%                     is a comma separated list of events for which data is to 
%                     be extracted    
%                 extraction start 
%                     is a frame number relative to event start or end when the 
%                     extraction should start    
%                 extraction end   
%                     is a frame number relative to event start or end when the 
%                     extraction should start the extraction start and end 
%                     should be given as '<s|e><frame number>'. E.g.:
%
%                      - s0  ... the frame of the event onset 
%                      - s2  ... the second frame from the event onset 
%                      - e1  ... the first frame from the event end 
%                      - e0  ... the last frame of the event 
%                      - e-2 ... the two frames before the event end
%
%                      Example::
%
%                      '<fidlfile>|encoding:e-color,e-shape:s2:s2|delay:d-color,d-shape:s2:e0'
%
%   --targetf   The folder to save images in ['.'].
%   --options   A string specifying additional analysis options formated as pipe 
%               separated pairs of colon separated key, value pairs: 
%               "<key>:<value>|<key>:<value>".
%
%               It takes the following keys and values:
%
%               roimethod
%                   what method to use to compute ROI signal, 'mean', 'median', 
%                   or 'pca' ['mean']
%
%               eventdata
%                   what data to use from each event:
%
%                   all      
%                       use all identified frames of all events
%                   mean     
%                       use the mean across frames of each identified event
%                   min      
%                       use the minimum value across frames of each identified 
%                       event
%                   max      
%                       use the maximum value across frames of each identified 
%                       event
%                   median   
%                       use the median value across frames of each identified 
%                       event
%                   
%                   ['all']
%
%               ignore   
%                   a comma separated list of information to identify frames to 
%                   ignore, options are:
%
%                   use      
%                       ignore frames as marked in the use field of the bold file
%                   fidl     
%                       ignore frames as marked in .fidl file (only available 
%                       with event extraction)
%                   <column> 
%                       the column name in *_scrub.txt file that matches bold 
%                       file to be used for ignore mask
%
%                   ['use,fidl']
%
%               badevents
%                   what to do with events that have frames marked as bad, 
%                   options are:
%
%                   use      
%                       use any frames that are not marked as bad
%                   <number> 
%                       use the frames that are not marked as bad if at least 
%                       <number> ok frames exist
%                   ignore   
%                       if any frame is marked as bad, ignore the full event
%                   
%                   ['use']
%
%               fcmeasure
%                   which functional connectivity measure to compute, the 
%                   options are:
%
%                   - r  ... pearson's r value
%                   - cv ... covariance estimate
%
%                   ['r']
%
%               saveind  
%                   a comma separted list of individual session / subject files 
%                   to save
%
%                   r        
%                       save Pearson correlation coefficients (r only) 
%                       separately for each roi
%                   fz       
%                       save Fisher Z values (r only) separately for each roi
%                   z        
%                       save Z statistic (r only) separately for each roi
%                   p        
%                       save p value (r only) separately for each roi
%                   cv       
%                       save covariances (cv only) separately for each roi
%                   allbyroi 
%                       save all relevant values by roi
%                   jr       
%                       save Pearson correlation coefficients (r only) in a 
%                       single file for all roi
%                   jfz      
%                       save Fisher Z values (r only) in a single file for all roi
%                   jz       
%                       save Z statistic (r only) in a single file for all roi
%                   jp       
%                       save p value (r only) in a single file for all roi
%                   jcv      
%                       save covariances (cv only) in a single file for all roi
%                   alljoint 
%                       save all relevant values in a joint file
%                   none     
%                       do not save any individual level results
%
%                   ['none']
%
%                   Default is 'none'. Any invalid options will be ignored 
%                   without a warning.
%
%               subjectname
%                   an optional name to add to the output files, if empty, it 
%                   won't be used ['']
%
%               verbose
%                   Whether to be verbose 'true' or not 'false', when running 
%                   the analysis ['false']
%
%   RESULTS
%   =======
%
%   The method returns a structure array with the following fields for each specified
%   data extraction:
%
%   fcmaps
%       title
%           the title of the extraction as specifed in the frames string, empty 
%           if extraction was specified using a numeric value 
%       fc
%           the functional connectivity map, with one seed-map per frame
%       roi
%           a cell array with the names of the ROI used in the order of their 
%           seed-maps in the fc image
%       N
%           number of frames over which the map was computed
%
%   Based on saveind option specification the following files may be saved:
%
%   `<targetf>/<name>[_<subjectname>][_<title>]_<roi>_r`
%       Pearson correlations
%
%   `<targetf>/<name>[_<subjectname>][_<title>]_<roi>_Fz`
%       Fisher Z values
%
%   `<targetf>/<name>[_<subjectname>][_<title>]_<roi>_Z`
%       Z converted p values testing difference from 0.
%
%   `<targetf>/<name>[_<subjectname>][_<title>]_<roi>_p`
%       p values testing difference from 0.
%
%   `<targetf>/<name>[_<subjectname>][_<title>]_<roi>_cv`
%       covariance
%
%   - `<roi>` is the name of the ROI for which the seed map was computed for.
%   - `<name>` is the provided name of the bold(s).
%   - `<subjectname>` is the provided name of the subject, if it was specified.
%   - `<title>` is the title of the extraction event(s), if event string was
%     specified.
%
%   USE
%   ===
% 
%   The function computes seed maps for the specified ROI. If an event string is
%   provided, it has to start with a path to the .fidl file to be used to extract 
%   the events, following by a pipe separated list of event extraction definitions::
%
%       <title>:<eventlist>:<frame offset1>:<frame offset2>
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

if nargin < 5 || isempty(options), options = '';  end
if nargin < 4 || isempty(targetf), targetf = '.'; end
if nargin < 3 frames  = []; end
if nargin < 2 error('ERROR: At least boldlist and ROI .names file have to be specified!'); end

% ----- parse options

default = 'roimethod=mean|eventdata=all|ignore=use,fidl|badevents=use|fcmeasure=r|saveind=none|subjectname=|verbose=false|debug=false';
options = general_parse_options([], options, default);

verbose = strcmp(options.verbose, 'true');
printdebug = strcmp(options.debug, 'true');

if printdebug
    general_print_struct(options, 'Options used');
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

if ismember({'allbyroi'}, options.saveind)    
    options.saveind = options.saveind(~ismember(options.saveind, {'allbyroi', 'r', 'fz', 'z', 'p', 'cv'}));
    options.saveind = [options.saveind, 'r', 'fz', 'z', 'p', 'cv'];
end
if ismember({'alljoint'}, options.saveind)
    options.saveind = options.saveind(~ismember(options.saveind, {'alljoint', 'jr', 'jfz', 'jz', 'jp', 'jcv'}));
    options.saveind = [options.saveind, 'jr', 'jfz', 'jz', 'jp', 'jcv'];
end
if ismember({'none'}, options.saveind)
    options.saveind = [];
end

if length(options.saveind) 
    if strcmp(options.fcmeasure, 'r')
        options.saveind = intersect(options.saveind, {'r', 'fz', 'z', 'p', 'jr', 'jfz', 'jz', 'jp'});
    else
        options.saveind = intersect(options.saveind, {'cv', 'jcv'});
    end
end

% ----- Get the list of files

[name, bolds] = strtok(bolds, '|');
bolds = bolds(2:end);
boldlist = strtrim(regexp(bolds, '\|', 'split'));

[roideffile, sroifile] = strtok(roiinfo, '|');
if sroifile
    sroifile = sroifile(2:end);
else
    sroifile = [];
end


% ----- Check if the files are there!

go = true;
if verbose; fprintf('\n\nChecking ...\n'); end

for bold = boldlist
    go = go & general_check_file(bold{1}, bold{1}, 'error');
end
go = go & general_check_file(roideffile, 'ROI definition file', 'error');
if sroifile
    go = go & general_check_file(sroifile, 'individual ROI file', 'error');
end
general_check_folder(targetf, 'results folder', true, verbose);

if ~go
    error('ERROR: Some files were not found. Please check the paths and start again!\n\n');
end


%   ------------------------------------------------------------------------------------------
%                                                                            do the processing

if verbose; fprintf('     ... creating ROI mask'); end

roi  = nimage.img_read_roi(roideffile, sroifile);
nroi = length(roi.roi.roinames);

if verbose; fprintf(' ... read %d ROI\n', nroi); end

% ---> reading image files

if verbose; fprintf('     ... reading image file(s)'); end
y = nimage(bolds);
if verbose; fprintf(' ... %d frames read, done.\n', y.frames); end


% ---> create extraction sets

if verbose; fprintf('     ... generating extraction sets ...'); end
exsets = y.img_get_extraction_matrices(frames, options);
if verbose; fprintf(' done.\n'); end

% ---> loop through extraction sets

if verbose; fprintf('     ... computing seedmaps\n'); end

nsets = length(exsets);
for n = 1:nsets

    if verbose; fprintf('         ... set %s', exsets(n).title); end
    
    % --> get the extracted timeseries

    ts = y.img_extract_timeseries(exsets(n).exmat, options.eventdata);

    if verbose; fprintf(' ... extracted ts'); end
    
    % --> generate seedmaps

    rs = ts.img_extract_roi(roi, [], options.roimethod);
    fc = ts.img_compute_correlations(rs', [], strcmp(options.fcmeasure, 'cv'));

    if verbose; fprintf(' ... computed seedmap'); end

    % ------> Embedd results

    fcmaps(n).title = exsets(n).title;
    fcmaps(n).fc    = fc;
    fcmaps(n).roi   = roi.roi.roinames;
    fcmaps(n).N     = ts.frames;

    if verbose; fprintf(' ... embedded\n'); end

end


% ---> save individual results

if ~isempty(options.saveind)

    if verbose; fprintf('     ... saving seedmaps\n'); end

    % set subjectname

    if options.subjectname
        subjectname = [options.subjectname, '_'];
    else
        subjectname = '';
    end

    % set up filetype for single images

    if strcmp(y.filetype, '.dtseries')
        tfiletype = '.dscalar';
    else
        tfiletype = y.filetype;
    end

    % --- loop through sets

    for n = 1:nsets
        if fcmaps(n).title, settitle = ['_' fcmaps(n).title]; else settitle = ''; end

        % --- prepare computed data

        if verbose; fprintf('         ... preparing data'); end
            
        if any(ismember(options.saveind, {'fz', 'p', 'z', 'jfz', 'jp', ',z'}))
            fz = fcmaps(n).fc;
            fz.data = fc_fisher(fz.data);
        end

        if any(ismember(options.saveind, {'p', 'z', 'jp', 'jz'}))
            Z = fcmaps(n).fc;
            Z.data = fz.data/(1/sqrt(fcmaps(n).N-3));
        end

        if any(ismember(options.saveind, {'p', 'jp'}))
            p = fcmaps(n).fc;
            p.data = (1 - normcdf(abs(Z.data), 0, 1)) * 2 .* sign(fz.data);
        end

        if verbose; fprintf(' ... done\n'); end

        % --- loop through roi

        if verbose; fprintf('         ... saving set %s, roi:', fcmaps(n).title); end

        % --- print for each ROI separately
        
        if any(ismember(options.saveind, {'r', 'fz', 'z', 'p', 'cv'}));

            for r = 1:nroi

                if verbose; fprintf(' %s', fcmaps(n).roi{r}); end

                % --- prepare basename

                basefilename = sprintf('seed_%s%s%s_%s', subjectname, name, settitle, fcmaps(n).roi{r});

                % --- save images

                for sn = 1:length(options.saveind)
                    switch options.saveind{sn}
                        case 'r'
                            t = fcmaps(n).fc.sliceframes([1:nroi] == r);                                              
                            t.filetype = tfiletype;
                            t.img_saveimage(fullfile(targetf, [basefilename '_r']));
                        case 'fz'
                            t = fz.sliceframes([1:nroi] == r);
                            t.filetype = tfiletype;
                            t.img_saveimage(fullfile(targetf, [basefilename '_Fz']));
                        case 'z'
                            t = Z.sliceframes([1:nroi] == r);
                            t.filetype = tfiletype;
                            t.img_saveimage(fullfile(targetf, [basefilename '_Z']));
                        case 'p'
                            t = p.sliceframes([1:nroi] == r);
                            t.filetype = tfiletype;
                            t.img_saveimage(fullfile(targetf, [basefilename '_p']));
                        case 'cv'
                            t = fcmaps(n).fc.sliceframes([1:nroi] == r);
                            t.filetype = tfiletype;
                            t.img_saveimage(fullfile(targetf, [basefilename '_cov']));
                    end
                end
            end
        end

        % --- print for all ROI jointly

        if any(ismember(options.saveind, {'jr', 'jfz', 'jz', 'jp', 'jcv'}));

            allroi = strjoin(fcmaps(n).roi, '-');
            basefilename = sprintf('seed_%s%s%s_%s', subjectname, name, settitle, allroi);

            if verbose; fprintf(' %s', allroi); end

            % --- save images

            for sn = 1:length(options.saveind)
                switch options.saveind{sn}
                    case 'jr'
                        t = fcmaps(n).fc;  
                        t.filetype = tfiletype;
                        t.img_saveimage(fullfile(targetf, [basefilename '_r']));
                    case 'fz'
                        t = fz;
                        t.filetype = tfiletype;
                        t.img_saveimage(fullfile(targetf, [basefilename '_Fz']));
                    case 'z'
                        t = Z;
                        t.filetype = tfiletype;
                        t.img_saveimage(fullfile(targetf, [basefilename '_Z']));
                    case 'p'
                        t = p;
                        t.filetype = tfiletype;
                        t.img_saveimage(fullfile(targetf, [basefilename '_p']));
                    case 'cv'
                        t = fcmaps(n).fc;
                        t.filetype = tfiletype;
                        t.img_saveimage(fullfile(targetf, [basefilename '_cov']));
                end
            end
        end

        if verbose; fprintf(' done.\n'); end
    end
end
