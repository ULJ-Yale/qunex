function [simg] = mri_ExtractTimeseries(obj, exmat, method)

%function [simg] = mri_ExtractTimeseries(obj, exmat, method)
%
%   Creates a new timeseries based on the specified extraction matrix and
%   extraction method.
%
%   INPUT
%   =====
%
%   obj     - a gmrimage object
%   exmat   - an [events x frames] extraction matrix in which each line
%             codes with 1 or true frames across the timeseries that constitue a single event
%   method  - a method for extracting frames across events, one of:
%             -> all      ... use all identified frames of all events
%             -> mean     ... use the mean across frames of each identified event
%             -> min      ... use the minimum value across frames of each identified event
%             -> max      ... use the maximum value across frames of each identified event
%             -> median   ... use the median value across frames of each identified event
%             ['all']  
%
%   RESULT
%   ======
%
%   simg   - a gmrimage object with the new timeseries
%
%   ---
%   Written by Grega Repovš 2020-02-01.

if nargin < 3 || isempty(method), method = 'all'; end
if nargin < 2 error('ERROR: An extraction matrix needs to be specified!'); end

% --- do the checks

if ~ismember(method, {'all', 'mean', 'min', 'max', 'median'})
    error('ERROR: Invalid extraction methods specified: %s', method);
end

if size(exmat, 2) ~= obj.frames
   error('ERROR: The extraction matrix length [%d] does not match the number of image frames [%d]!', size(exmat, 2), obj.frames); 
end

% --- run the extraction

if strcmp(method, 'all')
    exmat = sum(exmat) > 0;
    simg = obj.sliceframes(exmat);
else
    nevents = size(exmat, 1);
    simg = obj.zeroframes(nevents);
    exmat = exmat == 1;
    
    for n = 1:nevents
        switch method
            case 'mean'
                simg.data(:,n) = mean(obj.data(:,exmat(n,:)), 2);
            case 'min'
                simg.data(:,n) = min(obj.data(:,exmat(n,:)), [], 2);
            case 'max'
                simg.data(:,n) = max(obj.data(:,exmat(n,:)), [], 2);
            case 'median'
                simg.data(:,n) = median(obj.data(:,exmat(n,:)), 2);
        end
    end
end
