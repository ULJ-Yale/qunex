function F = g_CreateGLMHipassFilter(nframes,levels)

%``function F = g_CreateGLMHipassFilter(nframes,levels)`
%
%   Creates a high-pass filtering matrix by creating a pair of regressors with
%   0.25 phase difference for 1:levels number of full cycles over nframes.
%
%	INPUTS
%	======
%
%	--nframes
%	--levels
%
%	OUTPUT
%	======
%
%	F
%

%   ~~~~~~~~~~~~~~~~~~
%
%   Written by Grega Repovš

F = zeros(nframes, levels);

base = (0:nframes-1)'/(nframes-1);

F = [];
for n = 1:levels
    F = [F sin(base*2*pi*n)];
    F = [F sin(base*2*pi*n+0.25*2*pi)];
end


