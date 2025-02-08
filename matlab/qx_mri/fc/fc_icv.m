function [fcmat] =  fc_icv(data, fcargs)

%``fc_icv(data, fcargs)``
%
%   Function computes inverse covariance with an optional shrinkage or
%   standardization
%
%   Parameters:
%       --data (numeric matrix), T x N
%       --fcargs
%           .standardize  how to standardize 
%               - '' (default): no standardization, returns precision matrix
%               - 'partialcorr'
%               - 'semipartialcorr' - standardize by column
%
%           .shrinkage
%               - '' (default): no shrinkage, inverse computed with pinv:
%                               Moore-Penrose Pseudoinverse
%               - 'LW': Ledoit-Wolf estimate of optimal shrinkage
%               - 'OAS': Oracle Approximating Shrinkage
%                   
%
%   Returns:
%       fcmat (numerical matrix), NxN
%

if ~isfield(fcargs, 'standardize') || isempty(fcargs.standardize)
    standardize = ''; 
else 
    standardize = fcargs.standardize; 
end

if ~isfield(fcargs, 'shrinkage') || isempty(fcargs.shrinkage)
    shrinkage = '';
else 
    shrinkage = fcargs.shrinkage;
end
    
N = size(data,2);

% shrinkage
if strcmp(shrinkage, 'LW')
    [c, ~] = fc_cov_LW(data);
    c = inv(c);
elseif strcmp(shrinkage, 'OAS')
    [c, ~] = fc_cov_OAS(data);
    c = inv(c);
else
    c = inv(cov(data));
end

% standardize
fcmat = c;
if ~isempty(standardize)
    for i=1:N
        for j=1:N
            switch standardize
                case 'semipartialcorr'
                    fcmat(:,i) = -fcmat(:,i) ./ fcmat(i,i);
                case 'partialcorr'
                    fcmat(i,j) = -c(i,j) / sqrt(c(i,i) * c(j,j));
            end
        end
    end
    fcmat = fcmat + eye(N);
end