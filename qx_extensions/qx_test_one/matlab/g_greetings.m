function [] = g_greetings(name)

%``function [s] = g_greetings(name)``
%
%   If a name is provided, it greets nicely, otherwise it asks for your name
%
%   INPUTS
%	======
%
%   --name  	your name
%
%


%   ~~~~~~~~~~~~~~~~~~
%
%   Changelog
%   2020-11-14 Grega Repovs
%			   First version

if nargin < 1 , name = ''; end

if name
    fprintf('Hi %s! It is very nice to meet you. Have a beautiful day!\n', name)
else
    fprintf('May I ask for your name?\n')
end
