function [param] = g_SetParam(param, comm)

%function [param] = g_SetParam(param, comm)
%
%   A general function for changing / setting parameters into a structure.
%
%   Input
%       param   - a structure
%       comm    - a string specifying the parameters to be set as 'key:value|key:value' pairs
%
%   Grega Repovs, 2014-01-01
%

comm = regexp(comm, ',|;|:|\|', 'split');
if length(comm)>=2
    comm = reshape(comm, 2, [])';
    for p = 1:size(comm, 1)
        val = str2num(comm{p,2});
        if isempty(val), val = comm{p,2}; end
        if ~isstruct(param)
            param = struct(comm{p,1}, val);
        else
            param = setfield(param, comm{p,1}, val);
        end
    end
end