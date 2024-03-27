function [fcmat] = fc_cc(A,B)

%``fc_cc(A,B)``
%
%   Function computes maximum values of Cross-correlation for a given pairs 
%   of signal
%
%   Note: Signals are preprocessed in fc_prepare
%
%   Parameters:
%       --A (numeric matrix): NxT (N=ROIs, T=number of timepoints)
%       --B (numeric matrix): [] or MxT
%          
%
%   Returns:
%       fcmat (numeric matrix): 
%           rois (B=[]): size = NxN
%           seedmaps: size = NxM
%

if isempty(B)
    fcmat = zeros(size(A,1), size(A,1));
    for i = 1:size(A,1)
        for j = i:size(A,1)
            [c,~] = xcorr(A(i,:),A(j,:));
            fcmat(i,j) = max(c);
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
            [c,~] = xcorr(A.Value(i,:),B.Value(j,:));
            fcmat(i,j) = max(c);
        end
    end
end


