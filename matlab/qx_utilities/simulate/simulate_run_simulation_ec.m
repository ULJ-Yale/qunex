function [cors, sim] = simulate_run_simulation_ec(r, models, timepoints, nruns, k, md)

%``function [cors, runs] = simulate_run_simulation_ec(r, models, timepoints, nruns, k, md)``
%	
%   Function that generates multi normal timeseries with specified correlations.
%
%   INPUTS
%   ======
%
%   --r             list of correlations, one for each model
%   --models        array of structures specifying data models to generate
%   --timepoints    what timepoints to extract for correlation analyses
%   --nruns         how many simulations to run [100]
%   --k             division coefficient for corr timeseries [6]
%   --md            maximal allowed difference between desired and actual 
%                   correlation [0.01]
%
%   OUTPUTS
%   =======
%
%   cors
%       matrix with actual and estimated correlations for each model
%
%   sim  
%       array with actual simulation data
%

%   ~~~~~~~~~~~~~~~~~~
%
%   Changelog
%
%   2010-10-09 Grega Repovs
%              Initial version.
%	

if nargin < 6
    md = 0.01;
    if nargin < 5
        k = 6;
        if nargin < 4
            nruns = 100;
            if nargin < 3
                error('ERROR: Not enough parameters to run simulation!');
            end
        end
    end
end

savesim = false;
if nargout > 1
    savesim = true;
    sim.timepoints = timepoints;
    sim.nruns      = nruns;
    sim.k          = k;
    sim.r          = r;
end


% ---- key variables

nmodels = length(models);
ncond   = length(r);
cors    = zeros(nruns, ncond, nmodels+1);

% ---- precompute hrfs and regressors

for n = 1:nmodels
    mlen = 0;
    for c = 1:ncond
        [ts models(n).trials(c).modeldata] = simulate_generate_timeseries(models(n).trials(c).TR, models(n).trials(c).eventlist, models(n).trials(c).model, models(n).trials(c).modeldata);
        models(n).trials(c).model = 'raw';
        mlen = max(mlen, size(ts,1));
    end
    nregs = length(models(n).regs);
    X = [];
    for c = 1:nregs
        R = simulate_generate_timeseries(models(n).regs(c).TR, models(n).regs(c).eventlist, models(n).regs(c).model, models(n).regs(c).modeldata);
        R = simulate_trim_pad(R, mlen);
        X = [X R];
    end
    models(n).X    = X;
    models(n).mlen = mlen;
end
if savesim
    sim.models = models;
end

% ---- run the main loop

for s = 1:nruns

    % --- generate correlation series 
    
    cs = [];
    
    for c = 1:ncond
        [cs(c).ts er] = simulate_generate_correlated_timeseries([1 r(c); r(c) 1], length(models(1).trials(c).eventlist), md);
        cs(c).ts = 1 + cs(c).ts/k;
        er = corr(cs(c).ts);
        cors(s, c, 1) = er(1,2);
    end

    % --- loop through models
    
    for m = 1:nmodels

        % --- generate condition BOLD series
        
        ts  = [];
        
        for c = 1:ncond
            
            models(m).trials(c).eventlist(:,3) = cs(c).ts(:,1);
            ts(c).data(:,1) = simulate_generate_timeseries(models(m).trials(c).TR, models(m).trials(c).eventlist, models(m).trials(c).model, models(m).trials(c).modeldata);
            
            models(m).trials(c).eventlist(:,3) = cs(c).ts(:,2);
            ts(c).data(:,2) = simulate_generate_timeseries(models(m).trials(c).TR, models(m).trials(c).eventlist, models(m).trials(c).model, models(m).trials(c).modeldata);
            
        end
        
        % --- sum to a single bold
        
        y = zeros(models(m).mlen,2);
        
        for c = 1:ncond
            y = y + simulate_trim_pad(ts(c).data,models(m).mlen);
        end
        
        % --- regress out task
        
        [B res] = simulate_compute_glm(y, models(m).X);
        
        % --- extract datapoints and compute correlation
        
        for c = 1:ncond
            ts = simulate_extract_event_timepoints(models(m).trials(c).TR, res, models(m).trials(c).eventlist, timepoints);
            er = corr(ts);
            cors(s, c, m+1) = er(1, 2);
            sim.runs(s).models(m).c(c).ts = ts;
        end
        
        % --- save simulation data if asked
        
        if savesim
            sim.runs(s).models(m).bold = y;
            sim.runs(s).models(m).B    = B;
            sim.runs(s).models(m).res  = res;
        end
    end
end

            
    
    
    
    