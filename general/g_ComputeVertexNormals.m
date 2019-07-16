function [normals] = g_ComputeVertexNormals(surface)
%function [normals] = g_ComputeVertexNormals(surfaceFile)
%
%	Function computes the vertex normals to the passed surface file (.surf.gii)
%
%   INPUT
%       surface     - surface for which to compute normal vectors.
%                     It can be passed as a:
%                         a) surface file name (.surf.gii)
%                         b) gifti object
%
%   RESULTS
%       normals     - a N by 3 vector, containing the vertex normals for
%                        each vertex (N is the number of vertices).
%
%   EXAMPLE USE
%   To get vertex normal vectors of a surface file 'L_midthickness.surf.gii' use:
%
%   normal_vectors = g_ComputeVertexNormals('L_midthickness.surf.gii')
%
%   ---
%   Written by Aleksij Kraljic, 27 July, 2017
%

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

