function [img peak] = img_FindPeaks(img, minsize, maxsize, val, t, verbose)

%function [img peak] = img_FindPeaks(img, minsize, maxsize, val, t, verbose)
%
%		Find peaks and uses watershed algorithm to grow regions from them.
%
%       image       - input image
%       minsize     - minimal size of the resulting ROI  [0]
%       maxize      - maximum size of the resulting ROI  [inf]
%       val         - whether to find positive, negative or both ('n', 'p', 'b') [b]
%       t           - threshold value [0]
%       verbose     - whether to be verbose (1) and also report the peaks (2) [false]
%
%    (c) Grega Repovs, 2015-04-11
%
%

if nargin < 6 || isempty(verbose), verbose = false; end
if nargin < 5 || isempty(t),       t       = 0;     end
if nargin < 4 || isempty(val),     val     = 'b';   end
if nargin < 3 || isempty(maxsize), maxsize = inf;   end
if nargin < 2 || isempty(minsize), minsize = 1;     end


% --- Set up data

img.data  = img.image4D;

data  = zeros(size(img.data)+2);
data(2:(img.dim(1)+1),2:(img.dim(2)+1),2:(img.dim(3)+1)) = img.data;

peak  = [];
plist = zeros(img.voxels, 4);
ulist = zeros(img.voxels, 3);

% --- Flip to focus on the relevant value(s)

if strcmp(val, 'b')
    data = abs(data);
elseif strcmp(val, 'p')
    data(data < 0) = 0;
elseif strcmp(val, 'n')
    data(data > 0) = 0;
    data = data * -1;
else
    error('No value specified!');
end

data(data < t) = 0;

% --- Find all the relevant maxima

p  = 0;

if verbose, fprintf('\n---> identifying intial set of peaks'); end

for x = 2:img.dim(1)+1
    for y = 2:img.dim(2)+1
        for z = 2:img.dim(3)+1
            if data(x, y, z) > 0 && data(x, y, z) == max(max(max(data((x-1):(x+1), (y-1):(y+1), (z-1):(z+1)))))
                p = p + 1;
                peak(p).xyz   = [x, y z];
                peak(p).value = data(x, y, z);
            end
        end
    end
end


% --- remove peaks that are too close





% --- Flood to identify ROI, eliminate small ROI and repeat as needed

while true

    if verbose, fprintf('\n---> flooding %d peaks', length(peak)); end

    seg = ones(size(data));
    np  = 0;
    nu  = 0;

    seg(data == 0) = 0;

    % set up initial priority list

    for n = 1:length(peak)
        x = peak(n).xyz(1);
        y = peak(n).xyz(2);
        z = peak(n).xyz(3);
        peak(n).size = 1;
        seg(x, y, z) = n + 2;
        [seg, plist, np] = addPriority(data, seg, plist, x, y, z, np);
    end

    % Flood it

    while np > 0

        x = plist(1,1);
        y = plist(1,2);
        z = plist(1,3);

        plist(1:np,:) = plist(2:(np+1),:);
        np = np - 1;

        u = unique(seg((x-1):(x+1), (y-1):(y+1), (z-1):(z+1)));
        u = u(u>2);

        if length(u) == 1;
            seg(x, y, z) = u;
            peak(u-2).size = peak(u-2).size + 1;
            [seg, plist, np] = addPriority(data, seg, plist, x, y, z, np);
        else
            nu = nu + 1;
            ulist(nu,:) = [x y z];
        end
    end

    % --- Assign border voxels

    for n = 1:nu

        mdist = inf;
        cparc = 0;

        x = ulist(n,1);
        y = ulist(n,2);
        z = ulist(n,3);

        u = unique(seg((x-1):(x+1), (y-1):(y+1), (z-1):(z+1)));
        u = u(u>2);

        for l = 1:length(u)
            k = u(l);
            cdist = sqrt(sum((ulist(n,:) - peak(k-2).xyz).^2));
            if cdist < mdist
                mdist = cdist;
                cparc = k;
            end
        end
        seg(x, y, z) = cparc;
    end

    % any regions too small?

    small = [peak.size];
    small = small(small < minsize);

    if isempty(small)
        break
    else
        minpeak = min(small);
        psizes  = [peak.size];
        usizes  = sort(unique([peak.size]));
        for n = 2:length(usizes)
            if sum(psizes(psizes<=usizes(n))) < minsize
                minpeak = usizes(n);
            else
                break
            end
        end
    end


    % identify and remove the smallest

    nremove = sum([peak.size] <= minpeak);
    peak = peak([peak.size] > minpeak);

    if verbose, fprintf('\n---> %d ROI too small, removing %d ROI of size %d or smaller, remaining %d ROI.', length(small), nremove, minpeak, length(peak)); end

end


% --- Trim regions that are too large


big = find([peak.size] > maxsize);

if ~isempty(big) && verbose, fprintf('\n\n---> found %d ROI that are too large', length(big)); end

for n = 1:length(big)

    b  = big(n);
    np = 0;
    seg(seg==(b+2)) = 1;

    if verbose, fprintf('\n---> reflooding region %d', b); end

    x = peak(b).xyz(1);
    y = peak(b).xyz(2);
    z = peak(b).xyz(3);

    peak(b).size = 1;
    seg(x, y, z) = b + 2;
    [seg, plist, np] = addPriority(data, seg, plist, x, y, z, np);

    while np > 0

        x = plist(1,1);
        y = plist(1,2);
        z = plist(1,3);

        plist(1:np,:) = plist(2:(np+1),:);
        np = np - 1;

        seg(x, y, z) = b + 2;
        peak(b).size = peak(b).size + 1;
        [seg, plist, np] = addPriority(data, seg, plist, x, y, z, np);

        if peak(b).size >= maxsize
            break
        end

    end

end

seg(seg < 3) = 0;
for p = 1:length(peak)
    seg(seg==p+2) = p+1;
    peak(p).label = p+1;
end

% --- querry ROI properties

stats = regionprops(seg, data, {'Centroid','WeightedCentroid'});

% --- report peaks

if verbose, fprintf('\n\n===> peak report'); end
for p = 1:length(peak)
    peak(p).value = img.data(peak(p).xyz(1)-1, peak(p).xyz(2)-1, peak(p).xyz(3)-1);
    peak(p).Centroid = stats(peak(p).label).Centroid - 1;
    peak(p).WeightedCentroid = stats(peak(p).label).WeightedCentroid - 1;
    peak(p).xyz = peak(p).xyz - 1;

    % if verbose > 1, fprintf('\nROI:%3d  label: %3d  value: %5.1f  voxels: %3d  indeces: %3d %3d %3d  centroid: %5.1f %5.1f %5.1f  wcentroid: %4.1f %4.1f %4.1f', p, peak(p).label, peak(p).value, peak(p).size, peak(p).xyz, peak(p).Centroid, peak(p).WeightedCentroid); end
    if verbose > 1, fprintf('\nROI:%3d  label: %3d  value: %5.1f  voxels: %3d  indeces: %3d %3d %3d  centroid: %5.1f %5.1f %5.1f  wcentroid: %4.1f %4.1f %4.1f', p, peak(p).label, peak(p).value, peak(p).size, peak(p).xyz, peak(p).Centroid, peak(p).WeightedCentroid); end
end

% --- the end

if verbose, fprintf('\n===> DONE\n'); end

img.data = seg(2:(img.dim(1)+1),2:(img.dim(2)+1),2:(img.dim(3)+1));


% --- SUPPORT FUNCTIONS

function [seg, plist, np] = addPriority(data, seg, plist, x, y, z, np)

    for xi = x-1:x+1
        for yi = y-1:y+1
            for zi = z-1:z+1
                if seg(xi, yi, zi) == 1
                    seg(xi, yi, zi) = 2;
                    np = np + 1;
                    v  = data(xi, yi, zi);
                    for n = 1:np
                        if v > plist(n, 4)
                            plist(n+1:np+1,:) = plist(n:np,:);
                            plist(n,:) = [xi, yi, zi, v];
                            break
                        end
                    end
                end
            end
        end
    end



