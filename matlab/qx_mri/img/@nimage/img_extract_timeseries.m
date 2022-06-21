function [simg] = img_extract_timeseries(obj, exmat, method, eind)

%function [simg] = img_extract_timeseries(obj, exmat, method, eind)
%
%   Creates a new timeseries based on the specified extraction matrix and
%   extraction method.
%
%   INPUT
%   =====
%
%   obj     - a nimage object
%   exmat   - an [events x frames] extraction matrix in which each line
%             codes with 1 or true frames across the timeseries that constitue a single event
%   method  - a method for extracting frames across events, one of:
%             -> all      ... use all identified frames of all events
%             -> mean     ... use the mean across frames of each identified event
%             -> min      ... use the minimum value across frames of each identified event
%             -> max      ... use the maximum value across frames of each identified event
%             -> median   ... use the median value across frames of each identified event
%             ['all']  
%   eind    - and optional vector with event indeces for each row for the extraction matrix
%
%   RESULT
%   ======
%
%   simg   - a nimage object with the new timeseries
%            simg.tevents field will list for each frame the index of the row from which the 
%                        frame was extracted. If eind was provided, that information will be
%                        used instead of the row index. 
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 4 eind = []; end
if nargin < 3 || isempty(method), method = 'all'; end
if nargin < 2 error('ERROR: An extraction matrix needs to be specified!'); end

% --- do the checks

if ~ismember(method, {'all', 'mean', 'min', 'max', 'median'})
    error('ERROR: Invalid extraction methods specified: %s', method);
end

if size(exmat, 2) ~= obj.frames
   error('ERROR: The extraction matrix length [%d] does not match the number of image frames [%d]!', size(exmat, 2), obj.frames); 
end

if sum(exmat, 2) == 0
   error('ERROR: No frames are specified to extract (exmat only holds 0s)!'); 
end


% --- prepare event indeces

nevents = size(exmat, 1);

if isempty(eind)
    eind = [1:nevents];
end

% --- run the extraction

exmat = exmat == 1;

if strcmp(method, 'all')
    nframes = sum(exmat, 2);
    simg = obj.zeroframes(sum(nframes));
    simg.tevents = zeros(1, sum(nframes));
    simg.tframes = zeros(1, sum(nframes));
    fend = 0;
    tframes = [1:obj.frames];
else    
    simg = obj.zeroframes(nevents);
    simg.tevents = eind(:)';
    simg.tframes = sum(exmat, 2);
end

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
        case 'all'
            fstart = fend + 1;
            fend = fend + nframes(n);
            simg.tevents(fstart:fend) = eind(n);
            simg.tframes(fstart:fend) = tframes(exmat(n,:));
            simg.data(:,fstart:fend) = obj.data(:,exmat(n,:));            
    end
end
