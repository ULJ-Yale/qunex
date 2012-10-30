function [img] = mri_Scrub(img, com)

%function [img] = mri_Scrub(img, com)
%
%   Scrubs image according to the command
%
%       input:
%           img   - mrimage object
%           comm  - the description of how to scrub
%                      format:
%                      a) string only --> use the relevant column from .scrub file
%                      b) string:string --> use the relevant columnd from .scrub and then either
%                                           NA - set the bad frames to value NaN
%                                           RM - delete the bad frames from the image
%                      c) string:string:number --> use the number to threshold based on .bstats and .mov files
%
%       output:
%           img  - scrubbed image
%
%       Grega Repovs - 2012-10-29
%

if nargin < 2
    fprintf('\n\nERROR in the use of gmrimage.mri_Scrub!')
    help('gmrimage.mri_Scrub');
    error();
end

r   = 50;
fdt = 0.5;

% ---- process the command

com = regexp(com, ',|;|:|\|', 'split');

if length(com) < 3
    if isempty(img.scrub), error('ERROR: mri_Scrub(), missing .scrub data file!'); end
    mask = scrub(:, ismember(img.scrub, com));
    if length(com) == 2
        do = com{2};
    else
        do = 'RM';
    end
else
    stype = com{1};
    do    = com{2};
    if isempty(img.fstats), error('ERROR: mri_Scrub(), missing .bstats data file!'); end

    if stype(1) == 'i' or stype(1) == 'u'
        ui = stype(1);
        dv = stype(2:end);
    else
        ui = [];
        dv = stype;
    end

    if strcmp(dv, 'mov')
        if isempty(img.mov), error('ERROR: mri_Scrub(), missing .mov/.dat data file!'); end
        fdt = str2num(com{3});
        if length(com) > 3, r = str2num(com{4}); end
        mask = evaluateMov(img.mov, r, fdt);
    else
        dvt  = str2num(com{3});
        mask = img.fstats(:, ismember(img.fstats_hdr, dv)) >= dvt;
        if ~isempty(ui)
            if isempty(img.mov), error('ERROR: mri_Scrub(), missing .mov/.dat data file!'); end
            if length(com) > 3, fdt = str2num(com{4}); end
            if length(com) > 4, fdt = str2num(com{5}); end
            mov = evaluateMov(img.mov, r, fdt);
            if ui = 'i'
                mask = mask == 1 | mov == 1;
            else
                mask = mask == 1 & mov == 1;
            end
        end
    end
end

if strcmp(do, 'NA')
    img.data = img.image2D;
    img.data(:, mask==1) = NaN;
else
    img = img.sliceframes(mask<1);
end







        mov        = [];
        mov_hdr    = [];
        fstats     = [];
        fstats_hdr = [];
        scrub      = [];
        scrub_hdr  = [];