function [] = fc_compute_gbc3(flist, command, mask, verbose, target, targetf, rsmooth, rdilate, ignore, time, cv, vstep)

%``fc_compute_gbc3(flist, command, mask, verbose, target, targetf, rsmooth, rdilate, ignore, time, cv, vstep)``
%
%   Computes GBC maps for individuals as well as group maps.
%
%   NOTE: Please, note that fc_compute_gbc3 function is being deprecated.
%         The function will no longer be developed and will be removed in future 
%         releases of QuNex. Consider using fc_compute_gbc, which offers 
%         additional functionality, instead.
%
%   Parameters:
%       --flist (str):
%           A conc-like style list of session image files or conc files:
%
%           - session id:<session_id>
%           - roi:<path to the individual's ROI file>
%           - file:<path to bold files - one per line>
%
%           or a well strucutured string (see general_read_file_list).
%
%       --command (str):
%           The type of gbc to run: mFz, aFz, pFz, nFz, aD, pD, nD, mFzp, aFzp ...
%
%           ``<type of gbc>:<parameter>|<type of gbc>:<parameter> ...``
%
%           Following options are available:
%
%           - mFz:t
%               computes mean Fz value across all voxels (over threshold t)
%           - aFz:t
%               computes mean absolute Fz value across all voxels (over
%               threshold t)
%           - pFz:t
%               computes mean positive Fz value across all voxels (over
%               threshold t)
%           - nFz:t
%               computes mean positive Fz value across all voxels (below
%               threshold t)
%           - aD:t
%               computes proportion of voxels with absolute r over t
%           - pD:t
%               computes proportion of voxels with positive r over t
%           - nD:t
%               computes proportion of voxels with negative r below t
%           - mFzp:n
%               computes mean Fz value across n proportional ranges
%           - aFzp:n
%               computes mean absolute Fz value across n proportional ranges
%           - mFzs:n
%               computes mean Fz value across n strength ranges
%           - pFzs:n
%               computes mean Fz value across n strength ranges for positive
%               correlations
%           - nFzs:n
%               computes mean Fz value across n strength ranges for negative
%               correlations
%           - aFzs:n
%               computes mean absolute Fz value across n strength ranges
%           - mDs:n
%               computes proportion of voxels within n strength ranges of r
%           - aDs:n
%               computes proportion of voxels within n strength ranges of
%               absolute r
%           - pDs:n
%               computes proportion of voxels within n strength ranges of
%               positive r
%           - nDs:n
%               computes proportion of voxels within n strength ranges of
%               negative r.
%
%       --mask (int | logical | vector, default ''):
%           A mask defining which frames to use (1) and which not (0). All if
%           empty.
%
%       --verbose (bool, default false):
%           Report what is going on.
%
%       --target (vector, default FreeSurfer cortex codes):
%           Array of ROI codes that define target ROI.
%
%       --targetf (str):
%           Path to target folder for results.
%
%       --rsmooth (int, default ''):
%           Radius for smoothing (no smoothing if empty).
%
%       --rdilate (int, default ''):
%           Radius for dilating mask (no dilation if empty).
%
%       --ignore (str, default ''):
%           The column in *_scrub.txt file that matches bold file to be
%           used for ignore mask. All if empty.
%
%       --time (bool, default false):
%           Whether to print timing information.
%
%       --cv (bool, default false):
%           Whether to compute covariances instead of correlations.
%
%       --vstep (int, default 1200):
%           How many voxels to process in a single step.
%
%   Notes:
%       This function is a wrapper for nimage.img_compute_gbc method. It enables
%       computing GBC for a list of sessions. flist specifies the session
%       identities, bold files to compute GBC on and roi to use for specifying
%       the volume mask, voxels over which to compute GBC. mask specifies what
%       frames of an image to work on. target specifies the ROI codes that
%       define ROI from the session specific ROI files over which to compute GBC
%       for. Usually the session specific roi file would be that session's
%       FreeSurfer aseg or aseg+aparc segmentation. And if no target is
%       specified all gray matter voxels are used for computing GBC.
%   
%       What specifically gets computed is defined in the command string. For
%       specifics see help for the nimage.img_compute_gbc method.
%   
%       In addition, if rsmoot and rdilate are specified, each sessions bold
%       image will be 3D smoothed with the specifed FWHM in voxels. As sessions
%       gray matter masks differ and do not overlap precisely, rdilate will
%       dilate the borders with the provided number of voxels. Here it is
%       important to note that values from the expanded mask will not be used,
%       rather the values from the valid mask will be smeared into the dilated
%       area.
%   
%       The results will be saved in the targetf folder. The results of each
%       command will be saved in a separate file holding the computed GBC values
%       for all the sessions. The files will be named with the root of the flist
%       with _gbc_ and code for the specific gbc computed added.
%   
%       For more information see documentation for nimage.img_compute_gbc
%       method.
%
%   Examples:
%       ::
%
%           qunex fc_compute_gbc3 \
%               --flist='scz.list' \
%               --command='mFz:0.1|pFz:0.1|mFz:0.1|pD:0.3|mD:0.3' \
%               --mask=0 \
%               --verbose=true \
%               --target=gray \
%               --targetf=GBC \
%               --rsmooth=2 \
%               --rdilate=2 \
%               --ignore=udvarsme \
%               --time=true \
%               --cv=true
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

fprintf('\nWARNING: Please, note that fc_compute_gbc3 function is being deprecated.\n         The function will no longer be developed and will be removed in future releases of QuNex. \n         Instead, consider using fc_compute_gbc, which offers additional functionality.');

fprintf('\n\nStarting ...');

if nargin < 11 || isempty(vstep), vstep = [];   end
if nargin < 11, cv = [];         end
if nargin < 10, time = true;     end
if nargin < 9,  ignore = [];     end
if nargin < 8,  rdilate = [];    end
if nargin < 7,  rsmooth = [];    end
if nargin < 6,  targetf = '';    end
if nargin < 5,  target = [];     end
if nargin < 4,  verbose = false; end
if nargin < 3,  mask = [];       end

if isempty(target)
    % target = [3 8 9 10 11 12 13 16 17 18 19 20 26 27 28 42 47 48 49 50 51 52 53 54 55 56 58 59 60 96 97 1002 1003 1012 1014 1018 1019 1020 1026 1027 1028 1032 2002 2003 2012 2014 2018 2019 2020 2026 2027 2028 2032 1005 1006 1007 1008 1009 1010 1011 1013 1015 1016 1017 1021 1022 1023 1024 1025 1029 1030 1031 1033 1034 1035 2005 2006 2007 2008 2009 2010 2011 2013 2015 2016 2017 2021 2022 2023 2024 2025 2029 2030 2031 2033 2034 2035];
    target = [3 8 9 10 11 12 13 16 17 18 19 20 26 27 28 42 47 48 49 50 51 52 53 54 55 56 58 59 60 96 97 136 137 170 171 172 173 174 175 500 501 502 503 504 505 506 507 508 550 551 552 553 554 555 556 557 558 601 602 603 604 605 606 607 608 609 610 611 612 613 614 615 616 617 618 619 620 621 622 623 624 625 626 627 628 640 641 642 643 644 645 646 647 648 649 650 651 652 653 654 655 656 657 658 659 660 661 662 663 664 665 666 667 668 669 670 671 672 673 674 675 676 677 678 679 702 703 1000 1001 1002 1003 1004 1005 1006 1007 1008 1009 1010 1011 1012 1013 1014 1015 1016 1017 1018 1019 1020 1021 1022 1023 1024 1025 1026 1027 1028 1029 1030 1031 1032 1033 1034 1035 2000 2001 2002 2003 2004 2005 2006 2007 2008 2009 2010 2011 2012 2013 2014 2015 2016 2017 2018 2019 2020 2021 2022 2023 2024 2025 2026 2027 2028 2029 2030 2031 2032 2033 2034 2035 1100 1101 1102 1103 1104 1200 1201 1202 1205 1206 1207 1210 1211 1212 1105 1106 1107 1108 1109 1110 1111 1112 1113 1114 1115 1116 1117 1118 1119 1120 1121 1122 1123 1124 1125 1126 1127 1128 1129 1130 1131 1132 1133 1134 1135 1136 1137 1138 1139 1140 1141 1142 1143 1144 1145 1146 1147 1148 1149 1150 1151 1152 1153 1154 1155 1156 1157 1158 1159 1160 1161 1162 1163 1164 1165 1166 1167 1168 1169 1170 1171 1172 1173 1174 1175 1176 1177 1178 1179 1180 1181 2100 2101 2102 2103 2104 2105 2106 2107 2108 2109 2110 2111 2112 2113 2114 2115 2116 2117 2118 2119 2120 2121 2122 2123 2124 2125 2126 2127 2128 2129 2130 2131 2132 2133 2134 2135 2136 2137 2138 2139 2140 2141 2142 2143 2144 2145 2146 2147 2148 2149 2150 2151 2152 2153 2154 2155 2156 2157 2158 2159 2160 2161 2162 2163 2164 2165 2166 2167 2168 2169 2170 2171 2172 2173 2174 2175 2176 2177 2178 2179 2180 2181 2200 2201 2202 2205 2206 2207 2210 2211 2212 7100 7101 8001 8002 8003 8004 8005 8006 8007 8008 8009 8010 8011 8012 8013 8014 9000 9001 9002 9003 9004 9005 9006 9500 9501 9502 9503 9504 9505 9506 11100 11101 11102 11103 11104 11105 11106 11107 11108 11109 11110 11111 11112 11113 11114 11115 11116 11117 11118 11119 11120 11121 11122 11123 11124 11125 11126 11127 11128 11129 11130 11131 11132 11133 11134 11135 11136 11137 11138 11139 11140 11141 11142 11143 11144 11145 11146 11147 11148 11149 11150 11151 11152 11153 11154 11155 11156 11157 11158 11159 11160 11161 11162 11163 11164 11165 11166 11167 11168 11169 11170 11171 11172 11173 11174 11175 12100 12101 12102 12103 12104 12105 12106 12107 12108 12109 12110 12111 12112 12113 12114 12115 12116 12117 12118 12119 12120 12121 12122 12123 12124 12125 12126 12127 12128 12129 12130 12131 12132 12133 12134 12135 12136 12137 12138 12139 12140 12141 12142 12143 12144 12145 12146 12147 12148 12149 12150 12151 12152 12153 12154 12155 12156 12157 12158 12159 12160 12161 12162 12163 12164 12165 12166 12167 12168 12169 12170 12171 12172 12173 12174 12175];
end


%   ------------------------------------------------------------------------------------------
%   -------------------------------------------------- make a list of all the files to process

fprintf('\n ... listing files to process');

list = general_read_file_list(flist, 'all', [], verbose);

fprintf(' ... done.');


%   ------------------------------------------------------------------------------------------
%   -------------------------------------------- The main loop ... go through all the sessions

%   --- Get variables ready first

template = nimage(list.session(1).files{1}, 'single', 1);
nvoxels   = template.voxels;
desc      = parseCommand(command);
nvolumes  = length(desc);


template = template.zeroframes(list.nsessions);
for n = 1:nvolumes
    gbc(n) = template;
end
clear('template');

for s = 1:list.nsessions

    %   --- do we use a session specific mask

    usemask = false;
    if isfield(list.session(s), 'roi') && (~isempty(list.session(s).roi))
        usemask = true;
    end

    %   --- reading in image files
    tic;
    fprintf('\n ... processing %s', list.session(s).id);
    fprintf('\n     ... reading image file(s) ');

    y = [];

    nfiles = length(list.session(s).files);

    img = nimage(list.session(s).files{1});

    if ~isempty(mask),   img = img.sliceframes(mask); end
    if ~isempty(ignore), img = scrub(img, ignore); end

    if nfiles > 1
        for n = 2:nfiles
            new = nimage(list.session(s).files{n});
            fprintf(', %d', n);
            if ~isempty(mask),   new = new.sliceframes(mask); end
            if ~isempty(ignore), new = scrub(new, ignore); end
            img = [img new];
        end
    end

    if usemask
        imask = nimage(list.session(s).roi);
        imask = imask.ismember(target);

        if rsmooth
            limit = isempty(rdilate);
            img = img.img_smooth_3d_masked(imask, rsmooth, limit, verbose);
        end

        if rdilate
            imask = imask.img_grow_roi(rdilate);
        end

        img = img.maskimg(imask);
    end
    [img commands] = img.img_compute_gbc(command, [], [], verbose, [], time, cv, vstep);

    if usemask
        img = img.unmaskimg();
    end

    for n = 1:nvolumes
        timg = gbc(n);
        timg.data(:,s) = img.data(:,n);
        gbc(n) = timg;
    end
    fprintf(' [%.1fs]\n', toc);
end

for c = 1:nvolumes
    fname = [list.listname '_gbc_' desc{c}];
    gbc(c).img_saveimage(fullfile(targetf, fname));
end

%
%   ---- Auxilary functions
%

%   ---- Do the scrub

function [img] = scrub(img, ignore)

scol = ismember(img.scrub_hdr, ignore);
if sum(scol) == 1;
    mask = img.scrub(:,scol)';
    img  = img.sliceframes(mask==0);
    fprintf(' (scrubbed %d frames)', sum(mask));
else
    fprintf('\nWARNING: Field %s not present in scrubbing data, no frames scrubbed!', ignore);
end


%   ---- Parse the command

function [ext] = parseCommand(s)

    ext = {};

    a = splitby(s,'|');
    for n = 1:length(a)
        b = splitby(a{n}, ':');

        com = b{1};
        par = str2num(b{2});

        pre = com(1);
        pos = com(end);

        if ismember(pos, 'ps')
            if pos == 'p'
                sstep = 100 / par;
                parameter = floor([[1:sstep:100]', [1:sstep:100]'+(sstep-1)]);
                for p = 1:par
                    ext{end+1} = [com '_' num2str(parameter(p,1)) '_' num2str(parameter(p,2))];
                end
            else
                if ismember(pre, 'ap')
                    sv = 0;
                    ev = 1;
                    al = 1;
                elseif pre == 'm'
                    sv = -1;
                    ev = 1;
                    al = 1;
                else
                    sv = -1;
                    ev = 0;
                    al = 0;
                end
                sstep = (ev-sv) / par;
                parameter = [sv:sstep:ev];
                for p = 1:par
                    ext(end+1) = [com '_' num2str(parameter(p)) '_' num2str(parameter(p+1))];
                end

            end
        else
            ext{end+1} = [com '_' num2str(par)];
        end
    end


function [out] = splitby(s, d)
    c = 0;
    while length(s) >=1
        c = c+1;
        [t, s] = strtok(s, d);
        if length(s) > 1, s = s(2:end); end
        out{c} = t;
    end

