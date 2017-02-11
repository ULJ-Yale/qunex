function [x] = fc_ptoz(p,mu,sigma,pcov,alpha)



if nargin<1
    error('stats:norminv:TooFewInputs','Input argument P is undefined.');
end
if nargin < 2
    mu = 0;
end
if nargin < 3
    sigma = 1;
end


if nargout>2
   if nargin<4
      error('stats:norminv:TooFewInputs',...
            'Must provide covariance matrix to compute confidence bounds.');
   end
   if ~isequal(size(pcov),[2 2])
      error('stats:norminv:BadCovariance',...
            'Covariance matrix must have 2 rows and columns.');
   end
   if nargin<5
      alpha = 0.05;
   elseif ~isnumeric(alpha) | numel(alpha)~=1 | alpha<=0 | alpha>=1
      error('stats:norminv:BadAlpha',...
            'ALPHA must be a scalar between 0 and 1.');
   end
end



sigma(sigma <= 0) = NaN;
p(p < 0 | 1 < p) = NaN;

x0 = -sqrt(2).*erfcinv(2*p);
try
    x = sigma.*x0 + mu;
catch
    error('stats:norminv:InputSizeMismatch',...
          'Non-scalar arguments must match in size.');
end


if nargout>=2
   xvar = pcov(1,1) + 2*pcov(1,2)*x0 + pcov(2,2)*x0.^2;
   if any(xvar<0)
      error('stats:norminv:BadCovariance',...
            'PCOV must be a positive semi-definite matrix.');
   end
   normz = -norminv(alpha/2);
   halfwidth = normz * sqrt(xvar);
   xlo = x - halfwidth;
   xup = x + halfwidth;
end
