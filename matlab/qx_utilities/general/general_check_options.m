function [ok, bad_parameters, warnings] = general_check_options(options, check, onerror)

%``general_check_options(options, check, onerror)``
%
%   Function checks if the provided options arguments are valid.
%
%   Parameters:
%       --options (struct):
%           An options structure with the arguments to check.
%
%       --check (str|cell array):
%           A comma separated string, or a cell array of strings that lists the
%           kind of options to check. Supported checks are:
%
%           - 'fc'
%               check functional connectivity parameters
%
%           - 'eventdata'
%               check eventdata parameters that specifies how to construct an
%               eventdata matrix
%
%           - 'roimethod'
%               check the parameter that specifies how to compute the 
%               representative ROI timeseries
%
%           - 'flist'
%               check file list parameter
%
%           - 'roiinfo'
%               check parameter specifying ROI
%
%           - 'targetf'
%               check presence of target folder
%           
%           - 'all'
%               check all the above listed parameter options
%   
%           Defaults to 'all'.
%
%       --onerror (str):
%           What to do in case of an error:
%
%           - 'return'
%               returns the result of check
%
%           - 'warn'
%               prints all the warnings and returns
%
%           - 'stop'
%               prints all the errors and quits
%
%           Defaults to 'warn'.
%
%   Returns:
%       --ok (boolean):
%           Whether all the checks passed or not.
%
%       --bad_parameters (cell array):
%           A cell array listing all the bad parameters.
%
%       --warnings (cell array):
%           A cell array of all the warnings.
%

if nargin < 3 || isempty(onerror), onerror = 'warn'; end
if nargin < 2 || isempty(check), check = 'all'; end
if nargin < 1 error('ERROR: An options structure has to be provided!'); end

warnings = {};
bad_parameters = {};

if ischar(check)
    check = strtrim(regexp(check, ',', 'split'));
end

% -- Run checks for functional connectivity options

if any(ismember({'fc', 'all'}, check))
    if ~isfield(options, 'fcmeasure')
        warnings{end + 1} = 'fcmeasure option is not defined!';
        bad_parameters{end + 1} = 'fcmeasure';
elseif ismember(options.fcmeasure, {'r', 'cv', 'rho', 'cc', 'coh', 'mar'}) && isfield(options, 'fcargs') && ~isempty(options.fcargs)
        warnings{end + 1} = sprintf('FC measure %s should have no additional arguments defined!', options.fcmeasure);
        bad_parameters{end + 1} = 'fcargs';
    elseif strcmp(options.fcmeasure, 'icv') && ismember('fcargs', fieldnames(options))
        fc_args = fieldnames(options.fcargs);
        for i = 1:numel(fc_args)
            arg_val = options.fcargs.(fc_args{i});
            arg = fc_args{i};
            if ~ismember(arg, {'standardize', 'shrinkage'})
                warnings{end + 1} = sprintf('Argument %s for FC measure %s does not exist \n', arg, options.fcmeasure);
                bad_parameters{end + 1} = 'fcargs';
            elseif strcmp(arg, 'standardize')
                if ~ismember(arg_val, {'partialcorr', 'semipartialcorr', ''})
                    warnings{end + 1} = sprintf('Value of argument %s=%s for FC measure %s is not valid \n', arg, arg_val, options.fcmeasure);
                    bad_parameters{end + 1} = 'fcargs';
                end
            elseif strcmp(arg, 'shrinkage')
                if ~ismember(arg_val, {'OAS', 'LW', ''})
                    warnings{end + 1} = sprintf('Value of argument %s=%s for FC measure %s is not valid \n', arg, arg_val, options.fcmeasure);
                    bad_parameters{end + 1} = 'fcargs';
                end
            end
        end
    elseif strcmp(options.fcmeasure, 'mi') && ismember('fcargs', fieldnames(options))
        fc_args = fieldnames(options.fcargs);
        if size(options.fcargs, 1) > 1 || (size(options.fcargs, 1) == 1 && ~strcmp(fc_args{1}, 'k'))
            warnings{end + 1} = sprintf('FC measure %s should have at most one argument "k" \n', options.fcmeasure);
            bad_parameters{end + 1} = 'fcargs';
        end
        arg_val = options.fcargs.(fc_args{1});
        if ~strcmp(arg_val, '') && (~isnumeric(arg_val) || arg_val < 1)
            warnings{end + 1} = sprintf('Argument "k" for FC measure %s should be integer > 0 \n', options.fcmeasure);
            bad_parameters{end + 1} = 'fcargs';
        end
    elseif strcmp(options.fcmeasure, 'te') && ismember('fcargs', fieldnames(options))
        fc_args = fieldnames(options.fcargs);
        for i = 1:numel(fc_args)
            arg_val = options.fcargs.(fc_args{i});
            arg = fc_args{i};
            if ~ismember(arg, {'lags', 'k'})
                warnings{end + 1} = sprintf('Argument %s for FC measure %s does not exist \n', arg, options.fcmeasure);
                bad_parameters{end + 1} = 'fcargs';
            elseif ~isnumeric(arg_val) || arg_val < 1
                warnings{end + 1} = sprintf('Value of argument %s=%s for FC measure %s is not valid (arguments "lags" and "k" should be integers > 0) \n', arg, arg_val, options.fcmeasure);
                bad_parameters{end + 1} = 'fcargs';
            end
        end
    end
end

% -- Run checks for eventdata options

if any(ismember({'eventdata', 'all'}, check))
    if ~isfield(options, 'eventdata')
        warnings{end + 1} = 'eventdata option is not defined!';
        bad_parameters{end + 1} = 'eventdata';
    elseif ~ismember(options.eventdata, {'all', 'mean', 'min', 'max', 'median'})
        warnings{end + 1} = sprintf('Invalid eventdata option: %s!', options.eventdata);
        bad_parameters{end + 1} = 'eventdata';
    end
end

% -- Run checks for eventdata options

if any(ismember({'roimethod', 'all'}, check))
    if ~isfield(options, 'roimethod')
        warnings{end + 1} = 'roimethod option is not defined!';
        bad_parameters{end + 1} = 'roimethod';
    elseif ~ismember(options.roimethod, {'mean', 'pca', 'median', 'min', 'max'})
        warnings{end + 1} = sprintf('Invalid roimethod option: %s!', options.roimethod);
        bad_parameters{end + 1} = 'roimethod';
    end
end

% -- Run checks for roiinfo options

if any(ismember({'roiinfo', 'all'}, check))
    if ~isfield(options, 'roiinfo')
        warnings{end + 1} = 'roiinfo option is not defined!';
        bad_parameters{end + 1} = 'roiinfo';
    elseif ~starts_with(options.roiinfo, 'parcels:') && ~general_check_file(strtok(options.roiinfo, '|'), 'ROI definition file', 'nothing');
        warnings{end + 1} = sprintf('Could not find ROI definition file: %s!', options.roiinfo);
        bad_parameters{end + 1} = 'roiinfo';
    end
end

% -- Run checks for sroiinfo options

if any(ismember({'sroiinfo', 'all'}, check))
    if ~isfield(options, 'sroiinfo')
        warnings{end + 1} = 'sroiinfo option is not defined!';
        bad_parameters{end + 1} = 'sroiinfo';
    elseif ~starts_with(options.sroiinfo, 'parcels:') && ~general_check_file(strtok(options.sroiinfo, '|'), 'ROI definition file', 'nothing');
        warnings{end + 1} = sprintf('Could not find source ROI definition file: %s!', options.sroiinfo);
        bad_parameters{end + 1} = 'sroiinfo';
    end
end

% -- Run checks for sroiinfo options

if any(ismember({'troiinfo', 'all'}, check))
    if ~isfield(options, 'troiinfo')
        warnings{end + 1} = 'troiinfo option is not defined!';
        bad_parameters{end + 1} = 'troiinfo';
    elseif ~starts_with(options.troiinfo, 'parcels:') && ~general_check_file(strtok(options.troiinfo, '|'), 'ROI definition file', 'nothing');
        warnings{end + 1} = sprintf('Could not find target ROI definition file: %s!', options.troiinfo);
        bad_parameters{end + 1} = 'troiinfo';
    end
end

% -- Run checks for filelist options

if any(ismember({'flist', 'all'}, check))
    if ~isfield(options, 'flist')
        warnings{end + 1} = 'flist option is not defined!';
        bad_parameters{end + 1} = 'flist';
    elseif ~starts_with(options.flist, 'listname:') && ~general_check_file(options.flist, 'Image list file', 'nothing');
        warnings{end + 1} = sprintf('Could not find image list file: %s!', options.flist);
        bad_parameters{end + 1} = 'flist';
    end
end

% -- Run checks for target folder options

if any(ismember({'targetf', 'all'}, check))
    if ~isfield(options, 'targetf')
        warnings{end + 1} = 'targetf option is not defined!';
        bad_parameters{end + 1} = 'targetf';
    elseif (~strcmp(options.savegroup, 'none') && ~isempty(options.savegroup)) || (~strcmp(options.saveind, 'none') && ~isempty(options.saveind) && strcmp(options.itargetf, 'sfolder'))
        general_check_folder(options.targetf, 'results folder');
    end
end

% -- Final check

if length(warnings) > 0
    bad_parameters = unique(bad_parameters);
    if ismember(onerror, {'warn', 'stop'})
        fprintf('ERROR: Options check failed:\n');
        for n = 1:length(warnings)
            fprintf('       %s\n', warnings{n});
        end
    end

    if strcmp(onerror, 'stop')
        fprintf("       Aborting.");
        error("Stopped exectution.");
    end
end
