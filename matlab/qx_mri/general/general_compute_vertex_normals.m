function [normals] = general_compute_vertex_normals(surface)
%``general_compute_vertex_normals(surfaceFile)``
%
%   Function computes the vertex normals to the passed surface file (.surf.gii)
%
%   Parameters:
%       --surface: (str|gifti):
%           surface for which to compute normal vectors. It can be passed as a:
%               
%           - surface file name (.surf.gii)
%           - gifti object.
%
%   Returns:
%       normals
%           A N by 3 vector, containing the vertex normals for each vertex (N is the
%           number of vertices).
%
%   Examples:
%       To get vertex normal vectors of a surface file 'L_midthickness.surf.gii' use::
%
%           normal_vectors = general_compute_vertex_normals('L_midthickness.surf.gii');
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

% --- read the surface file
if ~isa(surface,'gifti')
    S = gifti(surface);
else
    S = surface;
end

% --- extract faces and vertices
V = double(S.vertices);
F = double(S.faces);

% --- call the triangulation function to create TR object
TR = triangulation(F,V);

% --- compute normals from the TR object
normals = vertexNormal(TR);

end

