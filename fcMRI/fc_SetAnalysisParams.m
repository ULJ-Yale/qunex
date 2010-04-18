function [in] = fc_SetAnalysisParams(in, roic, events, sframes, vframes, bframes, targetf, targete)

%
%	Takes parameters for connectivity analysis and sets them in the structure to be passed on
%

next = length(in) + 1;

in(next).roic 	= roic;
in(next).events	= events;
in(next).sframes	= sframes;
in(next).vframes	= vframes;
in(next).bframes	= bframes;
in(next).targetf	= targetf;
in(next).targete	= targete;

