% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

function [ud] = general_upsample_data(oldData, oldSphere, newSphere, newData)
%``function [ud] = general_upsample_data(data, oldSphere, newSphere, newData)``
%
%   Upsample surface data and the corresponding surface file.
%
%   INPUTS
%   ======
%
%   --oldData        input can be in two forms:
%
%                    - a metric file containing the data (.shape.gii)
%                    - data vector
%
%   --oldSurface     sphere surface file corresponding to oldData
%   --newSphere      sphere surface to fit (upsample) oldData to
%   --newData        a metric file containing the upsampled data (.shape.gii) []
%
%   OUTPUT
%   ======
%   
%   ud 
%       upsampled data vector
%
%   USE
%   ===
%
%   The function is used to upsample the data to fit the passed input sphere
%   surface. The newData can then be analyzed on surfaces derived from the
%   passed newSphere surface data.
%
%   EXAMPLE USE
%   ===========
%
%   To upsample a surface data distribution from 10000 to 38492 vertices use::
%
%       rd = general_upsample_data('oldData.surf.gii',...
%                'L.sphere.10k_fs_LR.surf.gii',...
%                'L.sphere.32k_fs_LR.surf.gii',...
%                'newData.shape.gii);
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

