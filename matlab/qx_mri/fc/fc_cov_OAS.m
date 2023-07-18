function [sigma, shrinkage] = fc_cov_OAS(data)

%``fc_cov_OAS(data)``
%
%   This function is a reimplementation of scikit-learn Oracle Approximating
%   Shrinkage Estimator (sklearn.covariance.OAS()).
%   https://scikit-learn.org/stable/modules/generated/sklearn.covariance.OAS.html
%
%   Parameters:
%       --data (numeric matrix): n x p (n=samples, p=features)
%          
%
%   Returns:
%       sigma (numeric matrix): 
%           shrunk covariance: size = TxT 
%       shrinkage (number)
%

n = size(data, 1);
p = size(data, 2);

emp_cov = (cov(data) * (n-1)) /n;
mu = trace(emp_cov)/ p;
alpha = mean(emp_cov.*emp_cov, 'all');
num = alpha + mu^2;
den = (n + 1)* (alpha - (mu^2) / p);
if den == 0
    shrinkage = 1;
else
    shrinkage = min(1, num/den);
end

sigma = (1 - shrinkage) * emp_cov + shrinkage*(eye(p)*mu);    
