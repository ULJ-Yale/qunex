function [img] = img_ReadNIfTIMetaData(img, fid, meta)

%function [img] = img_ReadNIfTIMetaData(img, fid, meta)
%
%		Reads NIfTI meta data, processes and stores it.
%
%       required:
%		    img       - mrimage object
%           fid       - file id of an open file handle
%           meta      - the length of the metadata
%
%       Grega Repovs - 2013-09-06
%

if nargin < 3
	error('\n\nERROR: Not enough parameters for the img_ReadNIfTIMetaData() method!\n\n');
end


% --- jump to metadata

img.xml = fread(fid, meta, '*char');






