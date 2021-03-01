function [img] = img_embed_stats(img)

%``function [img] = img_embed_stats(img)``
%
%	Embeds the extra data on image signal, movement statistics, and frame use.
%
%   INPUT
%   =====
%       
%   --img   a nimage image object
%
%   OUTPUT
%   ======
%
%   img
%       a nimage image object
%
%   USE
%   ===
%
%   This method is used internaly to embed per frame statistics on image signal
%   (number of valid voxels in the volume, mean volume intensity, standard
%   deviation over voxels in a volume, dvars and median normalized dvars
%   measure, and frame displacement measure), movement statistics (displacement
%   in each direction, rotation across each axis).
%

%   ~~~~~~~~~~~~~~~~~~
%
%   Changelog
%   2013-10-19 Grega Repovs
%              Initial version.
%


mdata = 0;
fdata = 0;
sdata = 0;

img.data = img.image2D;

% ---> Check for movement data

if ~isempty(img.mov_hdr) && img.frames == size(img.mov, 1);
    data = zeros(7, img.frames);
    c = 0;
    for s = {'dx(mm)', 'dy(mm)', 'dz(mm)', 'X(deg)', 'Y(deg)', 'Z(deg)', 'scale'}
        c = c + 1;
        x = find(ismember(img.mov_hdr, s));
        if x
            data(c,:) = img.mov(:,x)';
        end
    end
    img.data(end-6:end,:) = data;
    mdata = 1;
end

% ---> Check for image statistics data

if ~isempty(img.fstats_hdr) && img.frames == size(img.fstats, 1);
    data = zeros(6, img.frames);
    c = 0;
    for s = {'n', 'm', 'sd', 'dvarsm', 'dvarsme', 'fd'};
        c = c + 1;
        x = find(ismember(img.fstats_hdr, s));
        if x
            data(c,:) = img.fstats(:,x)';
        end
    end
    img.data(2:7,:) = data;
    fdata = 1;
end

% ---> Check for scrubbing and use data

udata = sum(img.use == 0) > 0;

if ~isempty(img.scrub_hdr)
    sdata = 1;
end

if (sdata | mdata | fdata | udata) && img.frames == size(img.scrub, 1);
    data = zeros(7, img.frames);
    data(1,:) = img.use;

    if sdata
        c = 1;
        for s = {'mov', 'dvars', 'dvarsme'};
            c = c + 1;
            x = find(ismember(img.scrub_hdr, s));
            if x
                data(c,:) = img.scrub(:,x)';
            end
        end
    end

    data(5,:) = fdata;
    data(6,:) = sdata;
    data(7,:) = mdata;
    data = [1 2 4 8 16 32 64] * data;
    img.data(1,:) = typecast(cast(data, 'uint32'), 'single');
end

