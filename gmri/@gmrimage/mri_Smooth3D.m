function img = mri_Smooth3D(img, fwhm, verbose)

%	
%	Adjusted function, accepts fwhm in voxels.
%	Assumes isometric voxels of 333 format
%	Uses kernel window size 7
%	
%	Grega Repovs 2008.7.11
%	

if nargin < 3
    verbose = false;
end

ksd = fwhm/(2*sqrt(2*log(2)));

img.data = img.image4D;
data = single(img.data);

if verbose, fprintf('Smoothing frame    ');, end
for n = 1:img.frames
	if verbose, fprintf('\b\b\b\b%4d',n);, end
	data(:,:,:,n) = smoothvolume(data(:,:,:,n), ksd);
end
if verbose, fprintf('\b\b\b\b ... finished\n');, end
img.data = single(data);

function smoothed = smoothvolume(data, ksd)

%function smoothed = smooth3f(data, filt, sz, arg)
%SMOOTH3F          Smooth 3D data (fast version).
%   W = SMOOTH3F(V) smoothes input data V with a Gaussian kernel.  The
%   smoothed data is returned in W.
%
%   W = SMOOTH3F(V, 'filter') Filter can be 'gaussian' or 'box' (default)
%   and determines the convolution kernel.
%
%   W = SMOOTH3F(V, 'filter', SIZE) sets the size of the convolution
%   kernel (default is [3 3 3]). If SIZE is a scalar, the size is
%   interpreted as [SIZE SIZE SIZE].  Each element of SIZE is required
%   to be an odd integer.
%
%   W = SMOOTH3F(V, 'filter', SIZE, ARG) sets an attribute of the
%   convolution kernel. When filter is 'gaussian', ARG is the standard
%   deviation (default is .65).  If filter is 'box', ARG has no effect.
%
%   SMOOTH3F is similar to Matlab's built-in SMOOTH3 but uses a more
%   efficient algorithm.  (The only difference in calling the two
%   functions is that SMOOTH3F requires an odd SIZE argument).
%
%   See also SMOOTH3.

% Modified from TMW's SMOOTH3.
%  The following commented code tests SMOOTH3f against SMOOTH3:
% data = randn([50,50,50]);
% tic; orig = smooth3(data);  t(1) = toc;
% tic; modf = smooth3f(data); t(2) = toc;
% mse = sqrt(mean(abs(orig(:)-modf(:)).^2));   % mean squared error
% printf('SMOOTH3: %4.3f sec   SMOOTH3F: %4.3f sec    MSE: %5.3f', t(1), t(2), mse);

%%%%%%%%%%%%%%%%%%%%%%%%%%% Parse Inputs %%%%%%%%%%%%%%%%%%%%%%%%%%

sz = single([7 7 7])';
szHalf = (sz-1)/2;

%%%%%%%%%%%%%%%%%%%%%%%%%% Make the kernel %%%%%%%%%%%%%%%%%%%%%%%%
% Make three kernels so that the full convolution kernel is the
% outer product of the three ...

kernel{1} = gausskernel(szHalf(1),ksd);
kernel{2} = gausskernel(szHalf(2),ksd);
kernel{3} = gausskernel(szHalf(3),ksd);

%%%%%%%%%%%%%%%%%%%%%%%%%%% Do the Smooth %%%%%%%%%%%%%%%%%%%%%%%%%
% Its grossly inefficient to do the full convolution since the kernel
% is separable.  We use CONVNSEP to do three 1-D convolutions.
smoothed = convnsep(kernel{:}, padreplicate(data,(sz-1)/2), 'valid');


%%%%% TAKEN FROM TMW's SMOOTH3 rev 1.7 -- pads an array by replicating values.
function b=padreplicate(a, padSize)
numDims = length(padSize);
idx = cell(numDims,1);
for k = 1:numDims
  M = size(a,k);
  onesVector = ones(1,padSize(k));
  idx{k} = [onesVector 1:M M*onesVector];
end
b = a(idx{:});


function kernel = gausskernel(R,S)
%GAUSSKERNEL       Creates a discretized N-dimensional Gaussian kernel.
%   KERNEL = GAUSSKERNEL(R,S), for scalar R and S, returns a 1-D Gaussian
%   array KERNEL with standard deviation S, discretized on [-R:R].
%
%   If R is a D-dimensional vector and S is scalar, KERNEL will be a
%   D-dimensional isotropic Gaussian kernel with covariance matrix
%   (S^2)*eye(D), discretized on a lattice with points [-R(k):R(k)] in the
%   kth dimension.
%
%   If R and S are both D-dimensional vectors, KERNEL will be a
%   D-dimensional anisotropic Gaussian kernel on the lattice described
%   above, but with standard deviation S(k) in the kth dimension.
%
%   If R is scalar and S is a D-dimensional vector, R is treated as
%   as R*ones(D,1).
%
%   KERNEL is always normalized to sum to 1.

%%%%%%%%%%%%%%%%%%%%%%%%%%%% Check Inputs %%%%%%%%%%%%%%%%%%%%%%%%%%%%
D = numel(R);
D2 = numel(S);
if (((D > 1) && (~isvectord(R))) || ((D2> 1) && (~isvectord(S)))),
    error('Matrix arguments are not supported.');
end
if ((D>1)&&(D2>1)&&(D~=D2)), 
    error('R and S must have same number of elements (unless one is scalar).');
end;

if (D2>D),  D = D2;  R = R * ones(1,D); end;   % force bins/sigmas
if (D>D2),  S = S * ones(1,D);  end;           %   to be same length,
R = R(:)';   S = S(:)';                        % and force row vectors

S(S==0) = 1e-5;  % std==0 causes problems below, 1e-5 has same effect

%%%%%%%%%%%%%%%%%%%%%%%%%%% Make the Kernel %%%%%%%%%%%%%%%%%%%%%%%%%%
RR = 2*R + 1;
for k = 1:D
    % Make the appropriate 1-D Gaussian
    grid = [-R(k):R(k)]';
    gauss = exp(-grid.^2./(2*S(k).^2));  
    gauss = gauss ./ sum(gauss);

    % Then expand it against kernel-so-far ...
    if (k == 1),
        kernel = gauss;
    else    
        Dpast = ones(1,(k-1));
        expand = repmat(reshape(gauss, [Dpast RR(k)]), [RR(1:k-1) 1]);
        kernel = repmat(kernel, [Dpast RR(k)]) .* expand;
    end
end


function C = convnsep(varargin)
%CONVNSEP          N-dimensional convolution with separable kernels.
%   C = CONVNSEP(H1,H2,...,A) performs an N-dimensional convolution of A
%   with the separable kernel given by the outer product of the H1,H2,...
%   such that the input vector Hk is convolved along the kth dimension of
%   the real N-D array A.  If the number of kernels Hk is equal to M-1,
%   then the (HM..HN) kernels are taken to be 1.  No convolution occurs
%   for dimensions k with corresponding kernel Hk = 1.
%
%   C = CONVN(H1,H2,...,A,'shape') controls the size of the answer C:
%     'full'   - (default) returns the full N-D convolution
%     'same'   - returns the central part of the convolution that
%                is the same size as A.
%     'valid'  - returns only the part of the result that can be
%                computed without assuming zero-padded arrays.  The
%                size of the result is max(size(A,k)-size(Hk,k)+1,0)
%                in the kth dimension.
%
%   See also CONVN, CONV2.

% Modified from TMW's CONVN for efficiency.
%  The following commented code tests CONVNSEP against CONVN:
% D = 50;  R = 3;  sd = 1;
% data = randn([D,D,D]) + i*randn([D,D,D]);
% gauss1 = gausskernel(R,sd);    gauss3 = gausskernel([R,R,R],sd);
% tic; orig = convn(data,gauss3,'same');  toc
% tic; modf = convnsep(gauss1,gauss1,gauss1,data,'same'); toc
% mse = sqrt(mean(abs(orig(:)-modf(:)).^2))   % mean squared error


%%%%%%%%%%%%%%%%%%%%%%%%%%% Parse Inputs %%%%%%%%%%%%%%%%%%%%%%%%%%
% determine output shape
if (nargin < 2), error('At least two arguments are required.'); end;
if (ischar(varargin{end})),  
    shape = varargin{end};   varargin = varargin(1:end-1);
    if (length(varargin) == 1), 
        C = varargin{1};   return;     % If no kernels specified, no work to do
    end;
else
    shape = 'full';
end

% get target matrix
A = varargin{end};   varargin = varargin(1:end-1);
if (~isa(A,'double')),   A = double(A);  end;
D = ndims(A);

% get kernels
H = varargin;   N = length(H);
if (N > D),  error('Can not have more kernels than the number of dimensions in A.'); end;
for k = 1:D,
    if (k <= N)
        %if ((numel(H{k})>1) && ~isvectord(H{k})), error('All kernels Hk must be vectors.');  end;
        %if (~isa(H{k},'double')),  H(k) = double(H{k}(:));  end;  % force col/double
        Hisreal(k) = isreal(H{k});
    else
        H{k} = 1;
        Hisreal(k) = 1;
    end
end

%%%%%%%%%%%%%%%%%%%%%%%%%%%% Do the Conv %%%%%%%%%%%%%%%%%%%%%%%%%%
C = A;
for k = 1:N,
    orient = ones(1,ndims(A));   orient(k) = numel(H{k});
    kernel = reshape(H{k}, orient);

    if (Hisreal(k) & isreal(C))
        C = convnc(kernel,C);  
    elseif (Hisreal(k) & ~isreal(C))
        C = convnc(kernel,real(C)) + j*convnc(kernel,imag(C));
    elseif (~Hisreal(k) & isreal(C))
        C = convnc(real(kernel),C) + j*convnc(imag(kernel),C);  
    else
        Hr = real(kernel);    Hi = imag(kernel);
        Cr = real(C);         Ci = imag(C);
        C = convnc(Hr,Cr) - convnc(Hi,Ci) + j*(convnc(Hi,Cr) + convnc(Hr,Ci)); 
    end
end

%%%%%%%%%%%%%%%%%%%%%%%% Get the right shape %%%%%%%%%%%%%%%%%%%%%%
% nothing more to do for 'full' shape
if (strcmp(shape,'full')),  return;  end;
 
% but for 'same' or 'valid' we need to crop the conv result
subs = cell(1,ndims(C));
if (strcmp(shape,'same'))  
  for k = 1:D
      subs{k}  = floor(length(H{k})/2) + [1:size(A,k)];  % central region
  end
elseif (strcmp(shape,'valid'))
  for k = 1:D
      validLen = max(size(A,k)-length(H{k})+1,0);
      subs{k}  = length(H{k})-1 + [1:validLen];
  end
end
C = C(subs{:});


function dim = isvectord(vect)
%ISVECTORD         Returns the orientation of a 1-D vector.
%   ISVECTORD(VECT) is non-zero if exactly one dimension of VECT has
%   length greater than 1.  The return value is then the index of that
%   dimension.  Note that NDIMS can not be used to decide this question,
%   because it returns 2 for, e.g., (M x 1) and (1 x M) arrays.
%
%   Example:
%      isvectord(1);             % returns 0
%      isvectord([1 2 ; 3 4])    % returns 0
%      isvectord([1:10])         % returns 2
%
%   See also ISVECTOR (Matlab R14 and later).

nonsingle = [size(vect) > 1];
dim = find(nonsingle);
if ((length(dim)>1) || (isempty(dim))),  dim = 0;  end;

