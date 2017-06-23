function [vol_img] = mri_ExtractCIFTIVolume(img)

%function [vol_img] = mri_CIFTI2volume(img)
%
%   Transforms a CIFTI gmrimage into a NIfTI volume gmrimage in order to
%   allow the usage of the existing methods for volume model analysis.
%
%   OUTPUT
%       vol_img  - gmrimage in a NIfTI format.
%
%   USE EXAMPLE
%   >>> image_NIfTI = img.mri_CIFTI2volume();
%
%   ---
%   Written by Aleksij Kraljic, 23-06-2017

% import CIFTI-2 components from the .mat file
load('CIFTI_BrainModel.mat');

% create an empty NIfTI file
vol_img = gmrimage(zeros(91,109,91));

% create a NIfTI header for the new file and add imageformat
vol_img.imageformat='NIfTI';
vol_img.hdrnifti = struct('swap', 0,'swapped', 0, 'data_type', blanks(10),...
    'db_name', blanks(18), 'extents', 0, 'session_error', 0,...
    'regular', 'r', 'dim_info', ' ', 'dim', [3;91;109;91;1;1;1;1], 'intent_p1', 0,...
    'intent_p2', 0, 'intent_p3', 0, 'intent_code', 0,'datatype', 16,...
    'bitpix', 32, 'slice_start', 0, 'pixdim', [-1;2;2;2;0;0;0;0], 'vox_offset', 2736,...
    'scl_slope', 0, 'scl_inter', 0, 'slice_end', 0, 'slice_code', ' ',...
    'xyzt_units', '', 'cal_max', 0, 'cal_min', 0, 'slice_duration', 0,...
    'toffset', 0, 'glmax', 0, 'glmin', 0, 'descrip', blanks(80),...
    'aux_file', blanks(24), 'qform_code', 1, 'sform_code', 1, 'quatern_b', 0,...
    'quatern_c', 1, 'quatern_d', 0, 'qoffset_x', 90, 'qoffset_y', -126,...
    'qoffset_z', -72, 'srow_x', [-2;0;0;90], 'srow_y', [0;2;0;-126],...
    'srow_z', [0;0;2;-72], 'intent_name', blanks(16), 'magic', 'n+1 ',...
    'version', 1, 'unused_str', blanks(24));

% remap the values from the imported CIFTI to the new NIfTI file
for i = 1:1:numel(img.cifti.shortnames)
    if strcmp(cifti.(lower(img.cifti.shortnames{i})).type, 'Volume')
        A = cifti.(lower(img.cifti.shortnames{i})).indices;
        j=1;
        for k = img.cifti.start(i):1:img.cifti.end(i)
            vol_img.data(A(j,1)+1,A(j,2)+1,A(j,3)+1)=img.data(k);
            j=j+1;
        end
    end
end

end

