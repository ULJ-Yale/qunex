function [] = general_get_roi_parcels(fin, fout, atlas)

%``function [] = general_get_roi_parcels(fin, fout, atlas)``
%
%   Returns a report showing the composition of regions of interest (ROI)
%   in the input image (fin) across CIFTI-2 volume structures and/or the
%   composition across parcels in the input atlas file.
%
%   INPUTS
%   ======
%
%   --fin          ROI input image file name
%   --fout         output file name ['<fin>_parcels.txt']
%   --atlas        atlas image (image values represent parcels)
%                  [if empty, the function returns the composition of ROIs
%                  volume structures as defined in the CIFTI-2 format]
%
%   EXAMPLE USE
%   ===========
%
%   An example without a specific atlas (only CIFTI-2 volume composition)::
%
%       general_get_roi_parcels('ROI_dtseries.nii',...
%       'ROI_composition.txt');
%
%   An example with an atlas::
%
%       general_get_roi_parcels('ROI_dtseries.nii',...
%       'ROI_composition.txt',
%       'my_atlas.dscalar.nii');
%

if nargin < 3 || isempty(atlas), atlas = []; end
if nargin < 2 || isempty(fout), fout = []; end

% --- load CIFTI brain model data
load('cifti_brainmodel');

% --- load the ROI input image
roi = nimage(fin);

num_frames = size(roi,2);

% ===== compute ROI composition across CIFTI-2 volume structure =====

% --- create an empty table with CIFTI-2 structures
T_vol = array2table(zeros(0,5));
T_vol.Properties.VariableNames = {'frame','ROI','volume_str','num_vox','perc_vox'};

% --- extract ROI volume
roi_vol = roi.img_extract_cifti_volume();

for fr=1:num_frames
    % --- extract data in the current frame
    D = roi_vol.data(:,fr);
    
    % --- get a list of ROI indices in the volume structures
    all_rois = unique(D);
    all_rois = all_rois(all_rois > 0);
    
    % --- generate the table with volume ROI structure
    for r=1:length(all_rois)
        current_roi = all_rois(r);
        
        roi_voxels = find(D == current_roi);
        
        roi_comp = components.indexMask(roi_voxels);
        roi_struct = unique(roi_comp);
        
        for s=1:length(roi_struct)
            num_vox = numel(roi_comp(roi_comp==roi_struct(s)));
            T_vol = [T_vol; {fr, current_roi, cifti.shortnames{roi_struct(s)},...
                num_vox, num_vox/length(roi_voxels)*100}];
        end
    end
end

if ~isempty(atlas)
    % ===== compute ROI composition across the input atlas =====
    
    atl = nimage(atlas);
    
    % --- create an empty table with CIFTI-2 structures
    T_atl = array2table(zeros(0,5));
    T_atl.Properties.VariableNames = {'frame','ROI','atlas_val','num_vox','perc_vox'};
    
    for fr=1:num_frames
        % --- extract data in the current frame
        D = roi.data(:,fr);
        
        % --- get a list of ROI indices in the volume structures
        all_rois = unique(D);
        all_rois = all_rois(all_rois > 0);
        
        % --- generate the table with volume ROI structure
        for r=1:length(all_rois)
            current_roi = all_rois(r);
            
            roi_voxels = find(D == current_roi);
            
            roi_comp = atl.data(roi_voxels);
            roi_struct = unique(roi_comp);
            
            for s=1:length(roi_struct)
                num_vox = numel(roi_comp(roi_comp==roi_struct(s)));
                T_atl = [T_atl; {fr, current_roi, roi_struct(s),...
                    num_vox, num_vox/length(roi_voxels)*100}];
            end
        end
    end
end

% --- print report
if isempty(fout)
    rep = strrep(fin, '.4dfp', '');
    rep = strrep(rep, '.ifh', '');
    rep = strrep(rep, '.img', '');
    rep = strrep(rep, '.nii', '');
    rep = strrep(rep, '.gz', '');
    rep = [rep '_parcels.txt'];
else
    rep = fout;
end

repf = fopen(rep, 'w');
fprintf(repf, '#source: %s', fin);

fprintf(repf,'\n\nframe\tROI\tvolume_structure\tnum_vox\tperc_vox');
for row=1:size(T_vol,1)
    fprintf(repf,'\n%d\t%d\t%s\t%d\t%0.1f',T_vol{row,1},T_vol{row,2},T_vol{row,3}{1},T_vol{row,4},T_vol{row,5});
end

if ~isempty(atlas)
    fprintf(repf,'\n\n');
    
    fprintf(repf,'\nframe\tROI\tatl_val\tnum_vox\tperc_vox');
    for row=1:size(T_atl,1)
        fprintf(repf,'\n%d\t%d\t%s\t%d\t%0.1f',T_atl{row,1},T_atl{row,2},num2str(T_atl{row,3}),T_atl{row,4},T_atl{row,5});
    end
end

fclose(repf);

end

