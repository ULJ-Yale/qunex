function [out] = fc_CompareROICorr(tniz, rniz)

%	
%	Takes two sets of ROI timeseries and compares correlations. 
%
%	niz.corr.bsr 	= sample x correlation matrix
%	niz.corr.bspr 	= sample x partial correlation matrix
%
%	outputs out.
%		mgdiffr		= mean difference in correlations
%		mgdiffpr	= mean difference in partial correlations
%		pgdiffr		= significance (p) of differences in correlations
%		pgdiffpr	= significance (p) of differences in parital correlations
%		

%   --- set variables

nsamples = size(tniz.corr.bsr,1);

%	--- compute differences and significances

gdiffr 	= tniz.corr.bsr - rniz.corr.bsr;
gdiffpr = tniz.corr.bspr - rniz.corr.bspr;

mgdiffr	 = mean(gdiffr, 1);
mgdiffpr = mean(gdiffpr, 1);

gdiffr 	= gdiffr > 0;
gdiffpr = gdiffpr > 0;

pgdiffr  = sum(gdiffr, 1)/nsamples;
pgdiffpr = sum(gdiffpr, 1)/nsamples;

pgdiffr  = abs(abs(pgdiffr-0.5)-0.5);
pgdiffpr = abs(abs(pgdiffpr-0.5)-0.5);

%	--- prepare output

out.mgdiffr  = mgdiffr;
out.mgdiffpr = mgdiffpr;
out.pgdiffr  = pgdiffr;
out.pgdiffpr = pgdiffpr;




