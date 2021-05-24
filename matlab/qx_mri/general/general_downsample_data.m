% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

function [rd] = general_downsample_data(input, inSurfaceProjection, inSphereSurface, targetVertices, outSurface, outSphere, wbPath)
%``function [rd] = general_downsample_data(input, inSurfaceProjection, inSphereSurface, targetVertices, outSurfaceProjection, wbPath)``
%
%   Downsample surface data and the corresponding surface file.
%
%   INPUTS
%   ======
%
%   --input                 input can be in two forms:
%                           
%                           1/ string with the CIFTI file and the surface 
%                           structure specified as:
%
%                               - CL ... cortex_left
%                               - CR ... cortex_right
%                               
%                           Form: 'img:<CIFTI FILE>|surf:<SURFACE STRUCTURE>'
%
%                           2/ data vector
%   --inSurfaceProjection   surface file to resample
%   --inSphereSurface       sphere surface file corresponding to the 
%                           inSurfaceProjection file
%   --targetVertices        target number of vertices to resample to
%   --outSurface            name of the resampled output surface file
%   --outSphere             name of the resampled sphere surface file 
%                           corresponding to the outSurface
%   --wbPath                path to wb_command (required if not stored as an 
%                           environment variable)
%
%   OUTPUT
%   ======
%   
%   rd
%       downsampled data vector
%
%   USE
%   ===
%
%   The function is used to downsample the image and surface data to a
%   desired number of vertices.
%
%   EXAMPLE USE
%   ===========
%   To downsample a surface data distribution over a midthickness layer of
%   the left cortex stored in the cifti file 'z_scores.dscalar.nii' from
%   38492 to 10000 vertices use::
%
%       rd = general_downsample_data('img:z_scores.dscalar.nii|surf:CL',...
%                'Q1-Q6_R440.L.midthickness.32k_fs_LR.surf.gii',...
%                'L.sphere.32k_fs_LR.surf.gii',...
%                10000,...
%                'downsampled_L_midthickness.surf.gii',...
%                'downsampled_L_sphere.surf.gii);
%

deleteOutSphere = false;
if nargin < 7 || isempty(wbPath),               wbPath = [];                                               end
if nargin < 6 || isempty(outSphere),            outSphere = 'tempSphere.surf.gii'; deleteOutSphere = true; end
if nargin < 5 || isempty(outSurface),           outSurface = 'resampledSurface.surf.gii';                  end

% --- Save environment variable path if passed as an argument
if ~isempty(wbPath)
    s = getenv('PATH');
    if isempty(strfind(s, wbPath))
        fprintf('\n     ... setting PATH to %s', wbPath);
        setenv('PATH', [wbPath ':' s]);
    end
end

% --- check whether the input is cifti or data vector
if ~isnumeric(input)
    input = general_parse_options([],input);
    img = nimage(input.img);
    if strcmp(input.surf,'CL')
        s = 1;
    elseif strcmp(input.surf,'CR')
        s = 2;
    end
    % --- Load CIFTI brain model data
    load('cifti_brainmodel');
    data = zeros(32492,1);
    data(cifti.(lower(img.cifti.shortnames{s})).mask) = img.data(img.cifti.start(s):img.cifti.end(s));
else
    data = input;
end

% --- save original data to temporary gifti metric
D = gifti(data);
D.cdata = data;
save(D,'temp_data.shape.gii','Base64Binary');

% --- create a new sphere with a target number of vertices
system(sprintf('wb_command -surface-create-sphere %d %s', targetVertices, outSphere));

% --- create a new projection with a target number of vertices
system(sprintf('wb_command -surface-resample %s %s %s BARYCENTRIC %s',...
    inSurfaceProjection, inSphereSurface, outSphere, outSurface));

% --- resample the data
system(sprintf('wb_command -metric-resample temp_data.shape.gii %s %s BARYCENTRIC new_data.shape.gii',...
    inSphereSurface, outSphere));

% --- save new resample data vector
rd_gifti = gifti('new_data.shape.gii');
rd = rd_gifti.cdata;

% --- delete the temporary files
delete 'temp_data.shape.gii' 'new_data.shape.gii';
if deleteOutSphere
    delete 'tempSphere.surf.gii';
end

end

