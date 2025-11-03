function out = glm_perf_log(cmd, label, t0)
%``function out = glm_perf_log(cmd, label, t0)``
%
%   Lightweight timing / iteration logging utilities for the GLM prewhitening
%   pipeline. Pure MATLAB/Octave; no toolboxes.
%
%   Inputs:
%       cmd (char)
%           'begin' | 'mark' | 'end'
%
%       label (char, optional)
%           Label to print with the timing mark
%
%       t0 (clock vector)
%           Required for 'mark'/'end'; value returned by 'begin'
%
%   Outputs:
%       out
%           For 'begin': t0 (clock vector);
%           For 'mark'/'end': elapsed seconds (double)
%
%   Notes:
%       - When debug_mode is false, you may wrap calls under a condition.
%       - Uses CLOCK/ETIME for Octave compatibility.
%

% SPDX-FileCopyrightText: 2025 QuNex development team
%
% SPDX-License-Identifier: GPL-3.0-or-later

    if nargin < 1, error('glm_perf_log: missing command'); end
    if nargin < 2 || isempty(label), label = ''; end

    switch lower(cmd)
        case 'begin'
            t0 = clock;
            fprintf('[GLM timing] %-24s: START\n', truncate_label(label));
            out = t0;

        case 'mark'

            if nargin < 3 || isempty(t0)
                warning('glm_perf_log: "mark" called without t0; ignoring.');
                out = [];
                return;
            end

            dt = etime(clock, t0);
            fprintf('[GLM timing] %-24s: %.3f sec\n', truncate_label(label), dt);
            out = dt;

        case 'end'

            if nargin < 3 || isempty(t0)
                warning('glm_perf_log: "end" called without t0; ignoring.');
                out = [];
                return;
            end

            dt = etime(clock, t0);
            fprintf('[GLM timing] %-24s: %.3f sec  (END)\n', truncate_label(label), dt);
            out = dt;

        otherwise
            error('glm_perf_log: unknown command "%s". Use "begin"|"mark"|"end".', cmd);
    end

end

% -------------------------
% Helpers
% -------------------------
function s = truncate_label(s)
    MAXLEN = 24;

    if numel(s) > MAXLEN
        s = [s(1:MAXLEN - 3), '...'];
    end

end
