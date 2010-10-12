function [ts, hrf, tso, te] = si_GenerateTimeseries(TR, eventlist, model, modeldata)

%	function [ts] = si_GenerateTimeseries(TR, eventlist, model)
%	
%   Function for generation of simulated BOLD timeseries
%
%   Inputs
%       - TR:           TR of the simulated timecourse
%       - eventlist:    matrix or cell array of matrices with columns:
%           - start time in seconds
%           - duration in seconds
%           - weight
%       - model:        boynton | spm | empirical | raw | unassumed
%       - modeldata:    parameters or the actual HRF timecourse depending on model
%	
% 	Created by Grega Repovš on 2010-10-09.
%	

if nargin < 4
    modeldata = [];
    if nargin < 3
        model = 'boynton';
        if nargin < 2
            error('ERROR: Not enough parameters to generate a timeseries!');
        end
    end
end

% ---- Check if we have a cell array on our hands

if iscell(eventlist)
    ncells = length(eventlist);
    for n = 1:ncells
        ts{n} = si_GenerateTimeseries(TR, eventlist{n}, model);
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
    case 'boynton'
        if isempty(modeldata)
            modeldata = [2.25, 1.25, 2];
        end
        t = [0:320]./10;
        hrf = fmri_hemodyn(t, 2.25, 1.25, 2);
    case 'spm'
        hrf = spm_hrf(0.1);
    case 'empirical'
        hrf = resample(modeldata, round(TR*10), 1);
    case 'raw'
        hrf = modeldata;
end

% ---- Generate event timeseries

eventlist(:,1:2) = round(eventlist(:,1:2)*10);

nevents  = size(eventlist,1);
tslength = sum(eventlist(nevents, 1:2))+length(hrf);
te       = zeros(tslength, 1);

for n = 1:nevents
    te(eventlist(n,1):eventlist(n,1)+eventlist(n,2)-1,1) = eventlist(n,3);
end

% ---- convolve with hrf and downsample to TR size


tso = conv(te, hrf);
ts = resample(tso, 1, round(TR*10),0);




