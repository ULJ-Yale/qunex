function [niz] = fc_ComputeROICorr(niz, frames, nsamples)

%	
%	Takes two sets of ROI timeseries and computes correlations and partial correlations. 
%	It returns the original structure plus correlations, partial correlations and samples
%
%	niz.timeseries 	= structure that holds event x timeseries x region datablock
%	frames			= which frames of the timeseries to take into computation
%	nsamples		= how many samples to draw
%
%	outputs niz.corr.
%		bsr			= sample x correlation matrix
%		bspr		= sample x partial correlation matrix
%	

%   --- set variables

fprintf('\nComputing correlations ');

nframes 	= length(frames);
nregions 	= size(niz.timeseries,3);
nevents 	= size(niz.timeseries,1);

data = zeros(nframes * nevents, nregions);

%	--- Create a data block of timepoints of interes

fprintf('\n... setting up data ');

for r = 1:nregions
	data(:,r) = reshape(niz.timeseries(:,frames,r), [], 1);
end

%	--- Sample and compute correlations

fprintf('\n... sampling covariances');
sample_cov = data2cov(data, nsamples);

fprintf('\n... computing correlations');
sample_corr = cov2corr(sample_cov);

fprintf('\n... computing partial correlations ... ');
sample_parcorr = cov2parcorr(sample_cov);

fprintf('\n... reorganizing data ... ');

sample_corr = reshape(sample_corr, nregions*nregions, []);
sample_parcorr = reshape(sample_parcorr, nregions*nregions, []);
Mr = sample2stats(sample_corr,'mean');
Mpr = sample2stats(sample_parcorr,'mean');


% ----- reorganize results

select = [];
for i = 1:nregions-1
	for j = i+1:nregions
		select = [select nregions*(i-1)+j];
	end
end

corr.bsr = sample_corr(select,:)';
corr.bspr = sample_parcorr(select,:)';
corr.r = Mr(select)';
corr.pr = Mpr(select)';

%	--- Compute significances of correlations

fprintf('\n... computing significances');

p_r	= corr.bsr > 0;
p_pr = corr.bspr > 0;

p_r  = sum(p_r, 1)/nsamples;
p_pr = sum(p_pr, 1)/nsamples;

corr.p_r  = abs(abs(p_r-0.5)-0.5);
corr.p_pr = abs(abs(p_pr-0.5)-0.5);


%	--- prepare output

niz.corr = corr;

fprintf('\nDone!\n');

