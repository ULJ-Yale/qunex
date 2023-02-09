function [fcmat] = fc_mi(A, B, fcargs)

%``fc_mi(A, B, fcargs)``
%
%   This function computes Kraskov's estimation of mutual information.
%
%   Parameters:
%       --A (numeric matrix): NxT (N=ROIs, T=number of timepoints)
%       --B (numeric matrix): [] or MxT
%       --fcargs
%           .k  (positive integer): argument used in KNN algorithm
%               default = 3
%          
%
%   Returns:
%       fcmat (numeric matrix): 
%           rois (B=[]): size = NxN
%           seedmaps: size = NxM
%

if ~isfield(fcargs, 'k') || isempty(fcargs.k)
    k = 3;
else
    k = fcargs.k;
end

if isempty(B)
    fcmat = zeros(size(A,1), size(A,1));
    for i = 1:size(A,1)
        for j = i:size(A,1)
            mi = fc_mi_cont_cont(A(i,:), A(j,:), k);
            fcmat(i,j) = mi;
            fcmat(j,i) = fcmat(i,j);
        end
    end
else
    A_n = size(A, 1);
    B_n = size(B, 1);
    fcmat = zeros(A_n, B_n);
    A = parallel.pool.Constant(A);
    B = parallel.pool.Constant(B);
    parfor i = 1:A_n
        for j = 1:B_n
            mi = fc_mi_cont_cont(A.Value(i,:),B.Value(j,:), k);
            fcmat(i,j) = mi;
        end
    end
end


