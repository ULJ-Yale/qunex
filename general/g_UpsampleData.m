function [ud] = g_UpsampleData(oldData, oldSphere, newSphere, newData)
%function [ud] = g_UpsampleData(data, oldSphere, newSphere)
%
%       Upsample surface data and the corresponding surface file.
%
%   INPUT
%       oldData          - input can be in two forms:
%                               a) a metric file containing the data (.shape.gii)
%                               b) data vector
%       oldSurface       - sphere surface file corresponding to oldData
%       newSphere        - sphere surface to fit (upsample) oldData to
%       newData          - a metric file containing the upsampled data (.shape.gii) []
%
%   OUTPUT
%       ud               - upsampled data vector
%
%   USE
%   The function is used to upsample the data to fit the passed input 
%   sphere surface. The newData can then be analyzed on surfaces derived
%   from the passed newSphere surface data.
%
%   EXAMPLE USE
%   To upsample a surface data distribution from 10000 to 38492 vertices use:
%
%   rd = g_UpsampleData('oldData.surf.gii',...
%                'L.sphere.10k_fs_LR.surf.gii',...
%                'L.sphere.32k_fs_LR.surf.gii',...
%                'newData.shape.gii);
%
%   ---
%   Written by Aleksij Kraljic, June 26, 2017
%
deleteOutData = false;
if nargin < 4 || isempty(newData),           newData = 'temp_new_data.shape.gii'; deleteOutData = true; end

% --- check whether the input data is a metric or data array
if isnumeric(oldData)
    % --- save downsampled data to temporary gifti metric
    Dt = gifti(oldData);
    Dt.cdata = oldData;
    save(Dt,'temp_data.shape.gii','Base64Binary');
    % --- resample the data
    system(sprintf('wb_command -metric-resample temp_data.shape.gii %s %s BARYCENTRIC %s',...
        oldSphere, newSphere, newData));
else
    system(sprintf('wb_command -metric-resample %s %s %s BARYCENTRIC %s',...
        oldData, oldSphere, newSphere, newData));
end

% --- save new resample data vector
ud_gifti = gifti(newData);
ud = ud_gifti.cdata;

if deleteOutData
    delete 'temp_new_data.shape.gii';
end

end

