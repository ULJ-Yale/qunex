function [in] = fc_SetAnalysisParamsBeh(in, col, events, vframes, bframes, targetf, targete)

%
%	Takes parameters for connectivity analysis and sets them in the structure to be passed on
%

next = length(in) + 1;

in(next).col 		= col;
in(next).events		= events;
in(next).vframes	= vframes;
in(next).bframes	= bframes;
in(next).targetf	= targetf;
in(next).targete	= targete;

