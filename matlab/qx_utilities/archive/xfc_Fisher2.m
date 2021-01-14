function [r] = fc_Fisher2(r)

%
%  converts pearson correlations to fisher z values
%
%  Created by Grega Repovs on 2007-06-23.
%  Copyright (c) 2007 Grega Repovs. All rights reserved.
%

% fprintf('1');
% r = r*0.9999999;
% fprintf('3');
% %r(r > 0.99999) =  0.99999;
% %r(r < -0.99999) = -0.99999;
% %fz = 0.5*log((1+r)./(1-r));
% r = atanh(r);
% fprintf('5');
% if ~isreal(r)
%     fprintf('6');
%     r = real(r);
% end
% fprintf('7');



% fprintf(' v2 1');
% r(r > 0.99999) =  0.99999;
% fprintf('2');
% r(r < -0.99999) = -0.99999;

fprintf(' v2 1');
r = r * 0.99999;
fprintf('2');
fz = 0.5*log((1+r)./(1-r));
fprintf('3');


