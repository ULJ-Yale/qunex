function [img] = g_Parcellated2Dense(inimg, outimg, verbose)

%function [img] = g_Parcellated2Dense(inimg, outimg, verbose)
%
%	Expands the parcelated file to a dense file
%
%   INPUT
%       - inimg   : a path to the image to expand
%       - outimg  : a path where the expanded image is to be saved
%       - verbose : should it report the details
%
%   OUTPUT
%       - img : a dense cifti gmrimage image object
%
%   USE
%   This method is used to expand a parcellated cifti data file to a cifti 
%   dense data file based on the information stored in cifti metatada.
%
%   ---
%   Written by Grega Repovs, 2019-06-29
%

% --> process variables

if nargin < 3 || isempty(verbose),  verbose  = false; end
if nargin < 2,                      outimg   = []; end

% --> check that input is present

g_CheckFile(inimg, 'input file');

if isempty(outimg)
    [filepath, filename, ext] = fileparts(inimg);
else
    [filepath, filename, ext] = fileparts(outimg);
    g_CheckFile(filepath, 'output folder');
end


if verbose, fprintf('\n===> Loading %s', inimg), end
img = gmrimage(inimg);
img = img.mri_Parcellated2Dense(verbose);

% --> save
if isempty(outimg)
    outimg = [img.rootfilename img.filetype '.nii'];
end

if verbose, fprintf('\n===> saving %s', outimg), end
img.mri_saveimage(outimg);

if verbose, fprintf('\n===> done\n'), end

