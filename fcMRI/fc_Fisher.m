function [r] = fc_Fisher(r)

%
%  converts pearson correlations to fisher z values
%
%  Created by Grega Repovs on 2007-06-23.
%  Copyright (c) 2007 Grega Repovs. All rights reserved.
%

r = double(r);
r = r*0.9999999;
%r(r > 0.99999) =  0.99999;
%r(r < -0.99999) = -0.99999;
%fz = 0.5*log((1+r)./(1-r));
r = atanh(r);
r = single(r);
if ~isreal(r)
    r = real(r);
end


