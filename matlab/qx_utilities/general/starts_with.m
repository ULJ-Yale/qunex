function [res] = starts_with(s, t)
% ``starts_with(s, t)``
%
%   Checks whether string s start with the test string t.
%
%   Parameters:
%       --s (str):
%           String to be tested.
%
%       --t (str):
%           String to test with.
%
%   Returns:
%       res (boolean):
%           The results of the test
%           
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

    lt = length(t);

    if lt == 0 
        res = true;
        return
    end

    res = strncmp(s, t, lt);

