function [p, t, c, z, tz] = general_conjunction(img, method, effect, q, data, psign)

%``[p, t, c, z, tz] = general_conjunction(img, method, effect, q, data, psign)``
%
%	Accepts matrix of significance estimates [voxels, sessions] and computes
%	conjunction for 1 <= u <= n. Results at each step are thresholded using FDR
%	q. Based on Heller et al. (2017). NeuroImage 37, 1178–1185.
%	(https://doi.org/10.1016/j.neuroimage.2007.05.051).
%
%	INPUTS
%	======
%
%	--img 		data matrix
%	--method	method of calculating conjunction p ['Fisher']
%
%		 		- 'Simes' 	 ... pooling dependent p-values (eq. 5)
%		 		- 'Stouffer' ... pooling independent p-values (eq. 6)
%		 		- 'Fisher'	 ... pooling independent p-values (eq. 7)
%
%	--effects 	the effect of interest ['all']
%
%				- 'pos'	... positive effect only (one tailed test)
%				- 'neg'	... negative effect only (one tailed test)
%				- 'all'	... both effects (two tailed test)
%
%	--q			the FDR q value at which to threshold	[default: 0.05]
%	--data		the values in data matrix
%			
%				- 'z' ... z-values [default]
%				- 'p' ... p-values
%
%	--psign		in case of two-tailed test for p-values input, a
%				matrix that includes signs for the effect direction
%				if p-values are not signed.
%
%
%	OUTPUTS
%	=======
%
%	p
%		images of conjoined p values for u = 1 to u = n
%
%	t
%		p thresholded with q(FDR)
%
%	c
%		image with number of sessions that show significant effect
%
%	z
%		z-score values
%
%	tz
%		thresholded z-values
%
%  	NOTES
%   =====
%
%	In case of two-tailed test
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

%  ---- parsing arguments

if nargin < 6 ,                   psign  = [];       end
if nargin < 5 || isempty(data),   data   = 'z';      end
if nargin < 4 || isempty(q),      q      = 0.05;     end
if nargin < 3 || isempty(effect), effect = 'all';    end
if nargin < 2 || isempty(method), method = 'Fisher'; end

if strcmp(effect, "all")
	tail = 2;
else
	tail = 1;
end

%  _________________________________________________
%  ---- initializing

img = double(img);
[nvox nsub] = size(img);

p = zeros(nvox, nsub);
t = zeros(nvox, nsub);
z = zeros(nvox, nsub);
c = zeros(nvox, 1);
s = ones(nvox, 1);

%  _________________________________________________
%  ---- converting values

if (strcmpi(data, 'z'))	
	z = img;
	switch effect
		case 'all'
			s  = sign(mean(z,2));
			z  = z .* repmat(s, 1, nsub);
		case 'neg'
			z = z * -1;
	end

	if (~strcmpi(method,'Stouffer'))
		p = (1-normcdf(z, 0, 1));
	end
else 
	p = img;
	p(abs(p) < 0.00000000000000006) = sign(p(abs(p) < 0.00000000000000006)) .* 0.00000000000000006;
	p(p==0) = 0.00000000000000006;

	if strcmp(effect, "all")
		if min(p) >= 0
			if isempty(psign)
				fprintf('\nWARNING: No negative p-value and p-value signs are not provided!\n         It is assumed that only positive effects are present.\n         Please chech your data!\n');
				psign = sign(p);
			else
				if size(p) ~= size(psign)
					error('ERROR: Provided img and psign dimensions do not match!');
				end
				psign = sign(psign);
			end			
		else
			psign = sign(p);
			p     = abs(p);
		end

		% convert to z-values to identify the overall sign
		z = psign .* norminv((1-p/2), 0, 1);
		s = sign(mean(z, 2));
		z = z .* repmat(s, 1, nsub);
		
		% convert back to p-values
		if (~strcmpi(method,'Stouffer'))
			p = (1 - normcdf(z, 0, 1));
		end
	elseif (strcmpi(method,'Stouffer'))
		z = norminv((1-p), 0, 1);
	end
end

%  _________________________________________________
%  ----                               Check p-values

if (any(any(p > 1)) || any(any(p<0)))
	error('ERROR: p-values outside of range [0,1]! Please check your data!');
end

%  _________________________________________________
%  ----                                 Simes method

if strcmpi(method, 'Simes')
	pin = sort(p, 2);
	for u = 1:(nsub-1)
		m = 1:(nsub-u);
		m = [(nsub-u+1)./m 1];
		m = repmat(m, nvox, 1);
		p(:,u) = min(pin(:,u:nsub) .* m, [], 2);
	end
	p(:,nsub) = pin(:,nsub);
end


%  _________________________________________________
%  ----                              Stouffer method

if strcmpi(method, 'Stouffer')
	zin = sort(z, 2);
	for u = 1:nsub
		z(:,u) = sum(zin(:, 1:(nsub-u+1)), 2) ./ sqrt(nsub-u+1);
	end
	p = (1-normcdf(z, 0, 1));
end


%  _________________________________________________
%  ----                                Fisher method

if strcmpi(method, 'Fisher')

	pin = sort(p, 2);
	%img(img==0) = 0.0000000000001;
	pin = log(pin);

	for n = 1:nsub
		p(:,n) = 1 - chi2cdf(-2 * sum(pin(:, n:nsub), 2), 2 * (nsub-n+1));
	end
end

%  _________________________________________________
%  ---- If needed convert to z values
if (nargout >= 4)
	z = norminv((1-p), 0, 1);
	z(z > 8.2095) = 8.2095;
	z(z < -8.2095) = -8.2095;
end

%  _________________________________________________
%  ---- FDR thresholding

% correct for two-tailed p
p = p * tail;
p(p>1) = 1;

vrank = repmat([1:nvox]', 1, nsub);
vcrit = (vrank ./ nvox) .* (q);
ps    = sort(p);
vrank(ps > vcrit) = 0;
vrank = max(vrank);
vcrit = (vrank ./ nvox) .* (q);
vcrit = repmat(vcrit, nvox,1);

t = p;
mask = t > vcrit;
t(mask) = 1;

c = (p<=vcrit);
c = sum(c,2);

% -------------------
% flip if needed

switch effect
	case 'all'
		if (nargout >= 4)
			z = z .* repmat(s, 1, nsub); 
		end
		c = c .* s;
	case 'neg'
		if (nargout >= 4) 
			z = z * -1; 
		end
		c = c * -1;
end

% -------------  
% z-map thresholding

if nargout >= 5
	tz = z;
	tz(mask) = 0;
end
