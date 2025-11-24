function nobj = img_select_roi(obj, roi)
%function nobj = img_select_roi(obj, roi)
%
%   Returns an roi image with only indicated roi remaining
%
%   Parameters:
%       --roi (cell array, numeric):
%           Either a cell array with ROI names or a numeric vector with roi 
%           codes to retain in the roi image.
%
%   Output:
%       obj
%           The nimage object with retained masks and roi structure
%
%   Note:
%       The order of the retained ROI will be the same as they were listed in
%       the 'roi' parameter

if nargin < 2, error('ERROR: please provide codes or names of the ROI to retain!'); end

% --- Check whether we have ROI names or ROI codes
if iscell(roi) && all(cellfun(@ischar, roi))
    [~, retain] = ismember(roi, {obj.roi.roiname});
elseif isnumeric(roi)
    [~, retain] = ismember(roi, [obj.roi.roicode]);
else
    error('ERROR (img_select_roi) invalid specification of roi to retain!');
end

% --- Select volumes
if obj.frames > 1
    nobj = obj.selectframes(retain);
else
    nobj = obj;
end

% --- Select ROI structure
nobj.roi = obj.roi(retain);
