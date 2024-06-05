function [res] = ends_with(s, t)
    % ``ends_with(s, t)``
    %
    %   Checks whether string ends with the test string t.
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

    if lt > length(s)
        res = false;
        return;
    end

    res = strcmp(s(end - lt+1:end), t);
    
