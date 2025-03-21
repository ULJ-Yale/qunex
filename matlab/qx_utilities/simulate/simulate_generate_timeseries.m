function [ts, hrf, tso, te] = simulate_generate_timeseries(TR, eventlist, model, modeldata)

%``simulate_generate_timeseries(TR, eventlist, model, modeldata)``
%
%   Function for generation of simulated BOLD timeseries.
%
%   Parameters:
%       --TR (float):
%           TR of the simulated timecourse in seconds.
%
%       --eventlist (matrix | cell array):
%           Matrix or cell array of matrices with columns:
%
%           - start time in seconds
%           - duration in seconds
%           - weight.
%
%       --model (str, default 'boynton'):
%           Can be one of the following:
%
%           - 'boynton'
%           - 'spm'
%           - 'gamma'
%           - 'empirical'
%           - 'raw'
%           - 'unassumed'.
%
%       --modeldata (str, default ''):
%           Parameters or the actual HRF timecourse depending on model.
%
%   Returns:
%       ts
%           
%       hrf
%           
%       tso
%           
%       te
%           
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 4
    modeldata = [];
    if nargin < 3
        model = 'boynton';
        if nargin < 2
            error('ERROR: Not enough parameters to generate a timeseries!');
        end
    end
end

model = lower(model);

% ---- Check if we have a cell array on our hands

if iscell(eventlist)
    ncells = length(eventlist);
    for n = 1:ncells
        ts{n} = simulate_generate_timeseries(TR, eventlist{n}, model);
    end
    return
end


% ---- Are we making an unassumed regressor

if strcmp(model, 'unassumed')
    nreg = modeldata;
    nevents = size(eventlist,1);
    tslength = floor(eventlist(nevents, 1)/TR)+nreg;
    ts = zeros(tslength, nreg);

    for n = 1:nevents
        for m = 1:nreg
            ts(floor(eventlist(n,1)/TR)+m-1,m) = 1;
        end
    end

    hrf = [];
    return
end


% ---- Generate HRF

switch model

    case {'boynton', 'spm', 'gamma'}
        hrf = general_hrf(0.1, hrf_type, [], modeldata);
    case 'empirical'
        hrf = resample(modeldata, round(TR*10), 1);
    case 'raw'
        hrf = modeldata;
    otherwise
        error('There was no valid HRF type specified! [%s]', model);
end

% ---- Generate event timeseries

eventlist(:,1:2) = round(eventlist(:,1:2)*10);

nevents  = size(eventlist,1);
tslength = sum(eventlist(nevents, 1:2))+length(hrf);
te       = zeros(tslength, 1);

for n = 1:nevents
    te(eventlist(n,1):eventlist(n,1)+eventlist(n,2)-1,1) = te(eventlist(n,1):eventlist(n,1)+eventlist(n,2)-1,1) + eventlist(n,3);
end

% ---- convolve with hrf and downsample to TR size


tso = conv(te, hrf);
ts = resample(tso, 1, round(TR*10),0);




