function [A] = fc_mar(data, p)

%``fc_mar(data, p)``
%
%   This function identifies an coefficients "A" of autoregressive (AR) model 
%   from multivariate time series using the multivariate least square method.
%
%   Parameters:
%       --data (numeric matrix): NxT (N=ROIs, T=number of timepoints)
%       --p (integer): Order of the AR model to be identified (lags)
%
%   Returns:
%       A (numerical matrix): AR coefficients of size NxNp
%

N = size(data, 1);
T = size(data, 2);

X = data(:,p+1:T);

Z = zeros(N*p, T-p);
for i = 1:p
    Z(1+(i-1)*N:i*N,:) = data(:,p-i+1:T-i);
end

% same as X*Z'*inv(Z*Z')
A = (X*Z')/(Z*Z');

