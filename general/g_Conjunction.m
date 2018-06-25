function [p, t, c] = g_Conjunction(img, method, effect, q, data)

%
%	g_Conjunction
%
%	v 2.0 © Grega Repovš, Feb 27 2008
%
%	Accepts matrix of significance estimates [voxels, subjects] and computes conjunction for 1 <= u <= n.
%	Results at each step are thresholded using FDR q.
%	Based on Heller et al, NeuroImage 37 (2007) 1178 – 1185
%
%	Arguments:
%		 img - data matrix
%
%		 method - method of calculating conjunction p
%		 	- 'Simes' 		: pooling dependent p-values (eq. 5)
%		 	- 'Stouffer' 	: pooling independent p-values (eq. 6)
%		 	- 'Fisher'		: pooling independent p-values (eq. 7) [default]
%
%		effect - the effect of interest
%			- 'pos'			: positive effect only (one tailed test)
%			- 'neg'			: negative effect only (one tailed test)
%			- 'all'			: both effects (two tailed test) [default]
%
%		q - the FDR q value at which to threshold	[default: 0.05]
%
%		data - the values in data matrix
%			- 'z'			: z-values [default]
%			- 'p'			: p-values
%
%	Results (always in the same data format as the input )
%		p : images of conjoined p values for u = 1 to u = n
%		t : p thresholded with q(FDR)
%		c : image with number of subjects that show significant effect
%
%	========= UPDATE LOG =========
%
%	2015-10-20 Grega Repovs
%              - updated argument parsing
%   2018-06-25 Grega Repovs
%            - Replaced icdf and cdf with norminv and normcdf to support Octave
%

%  ---- parsing arguments

if nargin < 5 || isempty(data),   data   = 'z';      end
if nargin < 4 || isempty(q),      q      = 0.05;     end
if nargin < 3 || isempty(effect), effect = 'all';    end
if nargin < 2 || isempty(method), method = 'Fisher'; end

tail = 1;

%  _________________________________________________
%  ---- initializing

[nvox nsub] = size(img);

p = zeros(nvox, nsub);
t = zeros(nvox, nsub);
c = zeros(nvox, 1);
s = [];

%  _________________________________________________
%  ---- converting values

if (strcmpi(data, 'z'))

	switch effect
		case 'all'
			s    = sign(mean(img,2));
			img  = img.*repmat(s, 1, nsub);
			tail = 2;
		case 'neg'
			img = img * -1;
	end

	if (~strcmpi(method,'Stouffer'))
		img = (1-normcdf(img, 0, 1));
	end
end

if (strcmpi(method,'Stouffer') & strcmpi(data, 'p'))
	img = norminv((1-img), 0, 1);
end

%  _________________________________________________
%  ----                                 Simes method

if strcmpi(method, 'Simes')
	img = sort(img, 2);
	for u = 1:(nsub-1)
		m = 1:(nsub-u);
		m = [(nsub-u+1)./m 1];
		m = repmat(m,nvox,1);
		p(:,u) = min(img(:,u:nsub).*m, [], 2);
	end
	p(:,nsub) = img(:,nsub);
end


%  _________________________________________________
%  ----                              Stouffer method

if strcmpi(method, 'Stouffer')
	img = sort(img, 2);
	for u = 1:nsub
		p(:,u) = sum(img(:,1:(nsub-u+1)),2)./sqrt(nsub-u+1);
	end
	p = (1-normcdf(p, 0, 1));
end


%  _________________________________________________
%  ----                                Fisher method

if strcmpi(method, 'Fisher')

	img = sort(img, 2);
	img(img==0) = 0.0000000000001;
	img = log(img);

	for n = 1:nsub
		p(:,n) = 1.-chi2cdf(-2*sum(img(:, n:nsub),2), 2*(nsub-n+1));
	end
end


%  _________________________________________________
%  ---- FDR thresholding

vrank = repmat([1:nvox]', 1, nsub);
vcrit = (vrank./nvox).*q;
ps    = sort(p);
vrank(ps>vcrit)=0;
vrank = max(vrank);
vcrit = (vrank./nvox).*q;
vcrit = repmat(vcrit, nvox,1);

t = p;
mask = t>vcrit;
t(mask)=1/tail;

c = (p<=vcrit);
c = sum(c,2);


%  _________________________________________________
%  ---- If needed convert to z values

if (strcmpi(data, 'z'))
	p = norminv((1-p.*tail), 0, 1);
	p(p>5) = 5;

	switch effect
		case 'all'
			p = p .* repmat(s, 1, nsub);
			c = c .* s;
		case 'neg'
			p = p * -1;
			c = c * -1;
	end

	t = p;
	t(mask) = 0;
end

