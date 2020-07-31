function [ts] = g_HRF(dt, hrf, len, p)

%``function [ts] = g_HRF(dt, hrf, len, p)``
%
%   INPUTS
%   ======
%
%   --dt    Timing resolution in seconds. [.01]
%   --hrf   HRF function to use, one of 'boynton', 'spm', 'gamma'. ['boynton']
%   --len   Duration of the HRF in seconds [32]
%   --p     Additional parameters. If not provided, set to HRF defaults
%
%   OUTPUT
%   ======
%
%   ts
%       HRF timeseries at the provided resolution
%
%   USE
%   ===
%
%   Use the function to generate an HRF timeseries to convolve with design
%   regressors or for other purposes. It makes sense to use a small timimg
%   resolution, as that will provide a sensible estimate of HRF maximum and
%   will ensure the right scaling. All the HRF functions are allways scaled
%   so that the peak equals 1. The descriptions of specific HRF follow.
%
%   boynton
%   -------
%
%   Boynton HRF is defined by the formula from Dale and Buckner, 1997::
%
%       h(t>delta)  = ((t-delta)/tau)^alpha * exp(-(t-delta)/tau)
%       h(t<=delta) = 0;
%
%   The parameters to provide are:
%
%   - delta ... time in seconds [2.25]
%   - tau   ... time in seconds [1.25]
%   - alpha ... the exponent [2]
%
%   gamma
%   -----
%
%   Gamma HRF is defined as gamma distribution with parameters:
%
%   - rlag   ... response lag (peak) [6.3]
%   - rdisp  ... reponse dispersion  [0.9]
%   - olag   ... time lag of the response onset [0]
%
%   and is computed as::
%
%       ts = pdf('Gamma', x, rlag, rdisp);
%
%   Do note that changing the dispersion value will also change the location
%   of the peak of the generated HRF.
%
%   spm
%   ---
%
%   SPM HRF is computed as a combination of two gamma distributions, the firts
%   describing the peak of the reponse, the other the undershoot. The parameters
%   are:
%
%   - rlag   ... response lag [6]
%   - rdisp  ... response dispersion [1]
%   - ulag   ... undershoot lag [16]
%   - udisp  ... undershoot dispersion [1]
%   - rurat  ... response / undershoot ratio [6]
%   - olag   ... time lag of the response onset [0]
%
%   HRF is computed as::
%
%       ts = pdf('Gamma', x, rlag, rdisp) - pdf('Gamma', x, ulag, udisp) / rurat;
%
%   Do note that values are interdependant. Changing ulag or rdisp will both
%   change the time of the peak as well as the rest of the HRF shape.
%
%   EXAMPLE USE
%   ===========
%
%   ::
%   
%       hrf = g_HRF(0.1, 'boynton');
%       hrf = g_HRF(0.1, 'spm', [6 0.9 12 0.9 3 0]);
%
%   ~~~~~~~~~~~~~~~~~~
%
%   Changelog
%   
%   2017-02-11 Grega Repovš
%              Initial version.
%


if nargin < 4,                 p   = [];        end
if nargin < 3 || isempty(len), len = 32;        end
if nargin < 2 || isempty(hrf), hrf = 'boynton'; end
if nargin < 1 || isempty(dt),  dt  = 0.01;      end


% ---- set up the time range

l = len/dt;
x = [0:l] / l * len;


% ---- generate hrf

switch hrf
    case 'boynton'
        if isempty(p)
            p = [2.25 1.25 2];
        elseif length(p) ~= 3
            error('ERROR: Wrong number of parameters for boynton HRF [%d]!', length(p));
        end

        delta = p(1);
        tau   = p(2);
        alph  = p(3);
        peak  = (alph .^ alph) * exp(-alph);

        ts    = ((x-delta)/tau).^alph .* exp(-(x-delta)/tau);
        ts(x <= delta) = 0;
        ts    = ts/peak;

    case 'gamma'
        if isempty(p)
            p = [6.3, 0.9 0];
        elseif length(p) ~= 2
            error('ERROR: Wrong number of parameters for single gamma HRF [%d]!', length(p));
        end

        rlag  = p(1);
        rdisp = p(2);
        olag  = p(3);

        ts = pdf('Gamma', x, rlag, rdisp);
        ts = ts / max(ts);

    case 'spm'
        if isempty(p)
            p = [6 1 16 1 6 0];
        elseif length(p) ~= 6
            error('ERROR: Wrong number of parameters for SPM HRF [%d]!', length(p));
        end

        rlag   = p(1);
        rdisp  = p(2);
        ulag   = p(3);
        udisp  = p(4);
        rurat  = p(5);
        olag   = p(6);

        x      = x - olag;

        ry     = pdf('Gamma', x, rlag, rdisp);
        uy     = pdf('Gamma', x, ulag, udisp);

        ts     = ry - uy / rurat;
        ts     = ts / max(ts);

    otherwise
        error('ERROR: Unknown hrf function!');
end

