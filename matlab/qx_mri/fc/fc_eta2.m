function [eta] = fc_eta2(a, b)

%``fc_eta2(a, b)``
%
%   Computes Eta2 coefficients.
%
%   If just one argument is given, it computes a matrix of eta coefficients
%   between each pair of columns in the original matrix. If two matrices of
%   equal size are given, it computes and array of eta coefficients comparing
%   homologous columns from both matrices. If the first argument is a column
%   vector and the second a matrix, it returns an array of eta coefficients
%   between the vector a and each column of the matrix b.
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin > 1
    colsb = size(b,2);
    colsa = size(a,2);
    if colsa ~= colsb
        if (colsb > 1) & (colsa == 1)
            a = repmat(a, 1, colsb);
        else
            error('ERROR: Sets a and b are not of equal column size [a: %d, b: %d]', colsa, colsb);
        end
    end
    if size(a) ~= size(b)
        error('ERROR: Sets a and b are not of equal size!');
    end
    m = (a+b)./2;
    M = mean(m, 1);
    if colsb > 1
        M = repmat(M, size(b,1), 1);
    end
    eta = 1 - sum((a-m).^2+(b-m).^2,1)./sum((a-M).^2+(b-M).^2, 1);
else
    nvar = size(a,2);
    fprintf('Eta: %5d      ');
    eta = ones(nvar,nvar);
    for n = 1:nvar-1
        eta(n,n+1:nvar) = fc_eta2(a(:, n), a(:, n+1:nvar));
        eta(n+1:nvar,n) = eta(n,n+1:nvar)';
        fprintf('\b\b\b\b\b%5d',n);
    end
    fprintf('\b\b\b\b\b\b\b\b\b\b')
end

