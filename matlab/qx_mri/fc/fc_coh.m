function [fcmat] = fc_coh(A, B)

%``fc_coh(A, B)``
%
%   Function computes maximum values of Coherence for each of the given 
%   pairs of signal
%
%   Parameters:
%       --A (numeric matrix): NxT (N=ROIs, T=number of timepoints)
%       --B (numeric matrix): [] or MxT
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
            c = mscohere(A(i,:),A(j,:));
            fcmat(i,j) = max(c);
            fcmat(j,i) = fcmat(i,j);
        end
    end
else
    % calculating max. value coherence as: 
    %    coh(a, b) = (|cpsd_ab|^2)/(cpsd_aa*cpsd_bb)

    % numerator
    cpsd_ab = cpsd(A', B');
    numerator = abs(cpsd_ab).^2;
    
    % denominator
    cpsd_aa = cpsd(A', A');
    cpsd_bb = cpsd(B', B');
    denominator = bsxfun(@times, cpsd_aa, permute(cpsd_bb, [1 3 2]));
    fcmat = squeeze(max(numerator./denominator, [], 1));
end
