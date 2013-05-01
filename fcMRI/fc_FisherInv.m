function [r] = fc_FisherInv(fz)

%	
%  converts Fisher z values to pearson correlations
%
%  Created by Grega Repovs on 2007-06-23.
%  Copyright (c) 2007 Grega Repovs. All rights reserved.
%

t = exp(fz*2);
r = (t-1)./(t+1);


