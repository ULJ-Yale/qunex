function [nuisance hdr] = general_extract_nuisance(img, fsimg, bmimg, target, ntarget, wbmask, sessionroi, nroi, shrink, verbose)

%``general_extract_nuisance(img, fsimg, bmimg, target, ntarget, wbmask, sessionroi, nroi, shrink, verbose)``
%
%    Extracts the specified nuisances and saves it into .nuisance file.
%
%   Parameters:
%       --img (str or nimage):
%           nimage or a path to a bold file to process
%       --fsimg (str or nimage):
%           nimage, a path to a freesurfer segmentation or '1b' for extraction 
%           based on the first frame of the BOLD timeseries
%       --bmimg (str or nimage):
%           nimage, a path to brain mask for this specific bold or [] for
%           image thresholding []
%       --target (str):
%           a path to the folder to save results into, default: where bold image 
%           is, 'none': do not save in external file 
%       --ntarget (str):
%           where to store used masks and their png image, 'none' for nowhere
%       --wbmask (str or nimage):
%           nimage or a path to a mask used to exclude ROI from the whole-brain 
%           nuisance regressor [none]
%       --sessionroi (str or nimage):
%           nimage or a path to a mask used to create session specific nroi 
%           [none]
%       --nroi (str):
%           ROI.names file to use to define additional nuisance ROI to regress 
%           out when additionally provided a list of ROI, those will not be 
%           masked by bold brain mask (e.g. 'nroi.names|eyes,scull')
%       --shrink (boolean, true):
%           Whether to erode ROI before using them. 
%       --verbose (boolean):
%           wheather to report on progress or not [not]
%
%   Outputs:
%
%       nuisance (numeric):
%           A n-times-m matrix that contains a timeseries of each extracted 
%           nuisance signal in a separate column.
%       hdr (cell array):
%           The names of extracted nuisance signals.
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 10, verbose     = false; end
if nargin < 9,  shrink      = true;  end
if nargin < 8,  nroi        = [];    end
if nargin < 7,  sessionroi  = [];    end
if nargin < 6,  wbmask      = [];    end
if nargin < 5,  store       = [];    end
if nargin < 4,  target      = [];    end
if nargin < 3,  bmimg       = [];    end

if nargin < 2
    error('ERROR: No tissue segmentation image (aseg, aparc+aseg) provided!');
end

if nargin < 1
    error('ERROR: No BOLD image provided!');
end

brainthreshold = 300;
fs_gm          = [3 8 9 10 11 12 13 16 17 18 19 20 26 27 28 42 47 48 49 50 51 52 53 54 55 56 58 59 60 96 97 136 137 170 171 172 173 174 175 500 501 502 503 504 505 506 507 508 550 551 552 553 554 555 556 557 558 601 602 603 604 605 606 607 608 609 610 611 612 613 614 615 616 617 618 619 620 621 622 623 624 625 626 627 628 640 641 642 643 644 645 646 647 648 649 650 651 652 653 654 655 656 657 658 659 660 661 662 663 664 665 666 667 668 669 670 671 672 673 674 675 676 677 678 679 702 703 1000 1001 1002 1003 1004 1005 1006 1007 1008 1009 1010 1011 1012 1013 1014 1015 1016 1017 1018 1019 1020 1021 1022 1023 1024 1025 1026 1027 1028 1029 1030 1031 1032 1033 1034 1035 2000 2001 2002 2003 2004 2005 2006 2007 2008 2009 2010 2011 2012 2013 2014 2015 2016 2017 2018 2019 2020 2021 2022 2023 2024 2025 2026 2027 2028 2029 2030 2031 2032 2033 2034 2035 1100 1101 1102 1103 1104 1200 1201 1202 1205 1206 1207 1210 1211 1212 1105 1106 1107 1108 1109 1110 1111 1112 1113 1114 1115 1116 1117 1118 1119 1120 1121 1122 1123 1124 1125 1126 1127 1128 1129 1130 1131 1132 1133 1134 1135 1136 1137 1138 1139 1140 1141 1142 1143 1144 1145 1146 1147 1148 1149 1150 1151 1152 1153 1154 1155 1156 1157 1158 1159 1160 1161 1162 1163 1164 1165 1166 1167 1168 1169 1170 1171 1172 1173 1174 1175 1176 1177 1178 1179 1180 1181 2100 2101 2102 2103 2104 2105 2106 2107 2108 2109 2110 2111 2112 2113 2114 2115 2116 2117 2118 2119 2120 2121 2122 2123 2124 2125 2126 2127 2128 2129 2130 2131 2132 2133 2134 2135 2136 2137 2138 2139 2140 2141 2142 2143 2144 2145 2146 2147 2148 2149 2150 2151 2152 2153 2154 2155 2156 2157 2158 2159 2160 2161 2162 2163 2164 2165 2166 2167 2168 2169 2170 2171 2172 2173 2174 2175 2176 2177 2178 2179 2180 2181 2200 2201 2202 2205 2206 2207 2210 2211 2212 7100 7101 8001 8002 8003 8004 8005 8006 8007 8008 8009 8010 8011 8012 8013 8014 9000 9001 9002 9003 9004 9005 9006 9500 9501 9502 9503 9504 9505 9506 11100 11101 11102 11103 11104 11105 11106 11107 11108 11109 11110 11111 11112 11113 11114 11115 11116 11117 11118 11119 11120 11121 11122 11123 11124 11125 11126 11127 11128 11129 11130 11131 11132 11133 11134 11135 11136 11137 11138 11139 11140 11141 11142 11143 11144 11145 11146 11147 11148 11149 11150 11151 11152 11153 11154 11155 11156 11157 11158 11159 11160 11161 11162 11163 11164 11165 11166 11167 11168 11169 11170 11171 11172 11173 11174 11175 12100 12101 12102 12103 12104 12105 12106 12107 12108 12109 12110 12111 12112 12113 12114 12115 12116 12117 12118 12119 12120 12121 12122 12123 12124 12125 12126 12127 12128 12129 12130 12131 12132 12133 12134 12135 12136 12137 12138 12139 12140 12141 12142 12143 12144 12145 12146 12147 12148 12149 12150 12151 12152 12153 12154 12155 12156 12157 12158 12159 12160 12161 12162 12163 12164 12165 12166 12167 12168 12169 12170 12171 12172 12173 12174 12175];
fs_wm          = [2 7 41 46 703 3000 3001 3002 3003 3004 3005 3006 3007 3008 3009 3010 3011 3012 3013 3014 3015 3016 3017 3018 3019 3020 3021 3022 3023 3024 3025 3026 3027 3028 3029 3030 3031 3032 3033 3034 3035 4000 4001 4002 4003 4004 4005 4006 4007 4008 4009 4010 4011 4012 4013 4014 4015 4016 4017 4018 4019 4020 4021 4022 4023 4024 4025 4026 4027 4028 4029 4030 4031 4032 4033 4034 4035 3100 3101 3102 3103 3104 3105 3106 3107 3108 3109 3110 3111 3112 3113 3114 3115 3116 3117 3118 3119 3120 3121 3122 3123 3124 3125 3126 3127 3128 3129 3130 3131 3132 3133 3134 3135 3136 3137 3138 3139 3140 3141 3142 3143 3144 3145 3146 3147 3148 3149 3150 3151 3152 3153 3154 3155 3156 3157 3158 3159 3160 3161 3162 3163 3164 3165 3166 3167 3168 3169 3170 3171 3172 3173 3174 3175 3176 3177 3178 3179 3180 3181 4100 4101 4102 4103 4104 4105 4106 4107 4108 4109 4110 4111 4112 4113 4114 4115 4116 4117 4118 4119 4120 4121 4122 4123 4124 4125 4126 4127 4128 4129 4130 4131 4132 4133 4134 4135 4136 4137 4138 4139 4140 4141 4142 4143 4144 4145 4146 4147 4148 4149 4150 4151 4152 4153 4154 4155 4156 4157 4158 4159 4160 4161 4162 4163 4164 4165 4166 4167 4168 4169 4170 4171 4172 4173 4174 4175 4176 4177 4178 4179 4180 4181 5001 5002 13100 13101 13102 13103 13104 13105 13106 13107 13108 13109 13110 13111 13112 13113 13114 13115 13116 13117 13118 13119 13120 13121 13122 13123 13124 13125 13126 13127 13128 13129 13130 13131 13132 13133 13134 13135 13136 13137 13138 13139 13140 13141 13142 13143 13144 13145 13146 13147 13148 13149 13150 13151 13152 13153 13154 13155 13156 13157 13158 13159 13160 13161 13162 13163 13164 13165 13166 13167 13168 13169 13170 13171 13172 13173 13174 13175 14100 14101 14102 14103 14104 14105 14106 14107 14108 14109 14110 14111 14112 14113 14114 14115 14116 14117 14118 14119 14120 14121 14122 14123 14124 14125 14126 14127 14128 14129 14130 14131 14132 14133 14134 14135 14136 14137 14138 14139 14140 14141 14142 14143 14144 14145 14146 14147 14148 14149 14150 14151 14152 14153 14154 14155 14156 14157 14158 14159 14160 14161 14162 14163 14164 14165 14166 14167 14168 14169 14170 14171 14172 14173 14174 14175];
fs_csf         = [4 5 14 15 24 43 44 72 701];

if verbose,
    fprintf('\nRunning general_extract_nuisance\n-------------------------\n');
    fprintf('\nParameters:\n-----------');
    fprintf('\n            img: %s', img);
    fprintf('\n          fsimg: %s', fsimg);
    fprintf('\n          bmimg: %s', bmimg);
    fprintf('\n         target: %s', target);
    fprintf('\n        ntarget: %s', ntarget);
    fprintf('\n         wbmask: %s', wbmask);
    fprintf('\n     sessionroi: %s', sessionroi);
    fprintf('\n           nroi: %s', nroi);
    fprintf('\n         shrink: %s\n', num2str(shrink));
end


% --------------------------------------------------------------
%                                                      read BOLD

if verbose, verbose = '\n---> Reading bold [%s]'; end
img = getImage(img, [], verbose);
img.data(isnan(img.data)) = 0;


% --------------------------------------------------------------
%                                                 get brain mask

if isempty(bmimg)
    if verbose, fprintf('\n---> Computing bold brain mask'); end
    bmimg = img.zeroframes(1);
    bimg.data = min(img.data, [], 2) > brainthreshold;
else
    if verbose, verbose = '\n---> Reading bold brain mask [%s]'; end
    bmimg = getImage(bmimg, [], verbose);
end


% --------------------------------------------------------------
%                                          get segmentation mask

if verbose, verbose = '\n---> Reading segmentation mask [%s]'; end
fsimg = getImage(fsimg, [], verbose);


% --------------------------------------------------------------
%                               define tissue based nuisance ROI

V   = fsimg.zeroframes(1);
WB  = fsimg.zeroframes(1);
WM  = fsimg.zeroframes(1);

bmimg.data = (bmimg.data > 0) & (fsimg.data > 0);

WM.data = (ismember(fsimg.data, fs_wm)) & (bmimg.data > 0);
if shrink, WM = WM.img_shrink_roi(); end
WM.data = WM.image2D;

V.data  = ismember(fsimg.data, fs_csf) & (bmimg.data > 0);
WB.data = (bmimg.data > 0) & (WM.data ~=1) & ~V.data;

%if shrink, V  = V.img_shrink_roi('surface', 6); end
if shrink, WB = WB.img_shrink_roi('edge', 10);  end %'edge', 10
if shrink, WM = WM.img_shrink_roi();            end
%if shrink, WM = WM.img_shrink_roi();            end

WB.data = WB.image2D;
WM.data = WM.image2D;
V.data  = V.image2D;


% --------------------------------------------------------------
%                                  define ROI to exclude from WB

if verbose, verbose = '\n---> Reading whole brain exclusion mask [%s]'; end
wbmask = getImage(wbmask, fsimg, verbose);


% --------------------------------------------------------------
%                                 define additional nuisance ROI

if ~isempty(sessionroi) && ischar(sessionroi)
    if strcmp(sessionroi, 'aseg')
        sessionroi = fsimg;
    elseif strcmp(sessionroi, 'wb')
        sessionroi = bimg;
    end
end


if ~isempty(nroi)
    [fnroi nomask] = processeROI(nroi);

    if verbose, verbose = '\n---> Reading additional nuisance roi [%s]'; end
    nroi = getImage(fnroi, sessionroi, verbose);

    maskcodes = find(~ismember(nroi.roi.roinames, nomask));
    if ~isempty(maskcodes)
        for mc = maskcodes
            nroi.data(bmimg.data == 0 & nroi.data == mc) = 0;
        end
    end
end

% --------------------------------------------------------------
%                                              combine nuisances

nuisance = [];
hdr      = {};

nuisance = [nuisance img.img_extract_roi(V)'];
nuisance = [nuisance img.img_extract_roi(WM)'];
nuisance = [nuisance img.img_extract_roi(WB)'];
hdr      = {'V', 'WM', 'WB'};

if ~isempty(wbmask)
    mWB = WB;
    wbmask = wbmask.img_grow_roi(2);
    mWB.data(wbmask.image2D > 0) = 0;
    nuisance = [nuisance img.img_extract_roi(mWB)'];
    hdr  = [hdr 'mWB'];
end

if ~isempty(nroi)
   nuisance = [nuisance img.img_extract_roi(nroi)'];
   hdr      = [hdr, nroi.roi.roinames];
end



% --------------------------------------------------------------
%                                       save in an external file

if ~strcmp(target, 'none')
    
    fname = img.img_basename();

    % --- save stats

    if verbose, fprintf('\n---> saving nuisance signals [%s]', fullfile(target, [fname '.nuisance'])); end

    % generate header
    version = general_get_qunex_version();
    header = sprintf('# Generated by QuNex %s on %s\n#', version, datestr(now,'YYYY-mm-dd_HH.MM.SS'));

    general_write_table(fullfile(target, [fname '.nuisance']), [[1:size(nuisance,1)]' nuisance], ['frame', hdr], 'mean,sd', '%-16s|%-16d|%-16.10f|%-15s', ' ', header);
end



% --------------------------------------------------------------
%                                           save nuisance images

if ~strcmp(ntarget, 'none')

    if verbose, fprintf('\n---> saving mask image'); end

    O = img.zeroframes(1);
    O.data = img.data(:,1);

    nimg = WB.zeroframes(5);
    nimg.data = nimg.image2D();
    nimg.data(:,1) = O.image2D();
    nimg.data(:,2) = WB.image2D();
    nimg.data(:,3) = V.image2D();
    nimg.data(:,4) = WM.image2D();
    nimg.data(:,5) = (WB.image2D()>0)*1 + (V.image2D()>0)*2 + (WM.image2D()>0)*3;

    if ~isempty(wbmask)
        nimg = [nimg mWB];
    end

    if ~isempty(nroi)
        nimg = [nimg nroi];
    end

    % --- get filename to save to

    fname = [img.img_basename() '_nuisance'];

    nimg.img_saveimage(fullfile(ntarget, fname));

    % --- compose PNG

    O  = O.img_slice_matrix(3);
    WB = WB.img_slice_matrix(3);
    V  = V.img_slice_matrix(3);
    WM = WM.img_slice_matrix(3);

    pic(:,:,1) = O;
    pic(:,:,2) = O;
    pic(:,:,3) = O;

    % pic = pic ./ 2800; % max(max(max(pic))); --- Change due to high values in embedded data!
    pic = pic ./ max(max(max(pic)));
    %pic = pic * 0.7;

    pic(:,:,3) = pic(:,:,3)+WB*0.3;
    pic(:,:,2) = pic(:,:,2)+V*0.3;
    pic(:,:,1) = pic(:,:,1)+WM*0.3;

    if ~isempty(nroi)
        nroi   = nroi.img_slice_matrix(3);
        rcodes = unique(nroi);
        rcodes = rcodes(rcodes > 0);
        cmap   = hsv(length(rcodes));

        isize  = size(nroi);
        nroi   = reshape(nroi, prod(isize), 1);
        cROI   = repmat(nroi, 1, 3);

        for rc = 1:length(rcodes)
            tm = nroi==rcodes(rc);
            cROI(tm,1) = cmap(rc,1);
            cROI(tm,2) = cmap(rc,2);
            cROI(tm,3) = cmap(rc,3);
        end
        cROI = cROI .*3;
        cROI = reshape(cROI, [isize 3]);
        pic  = pic + cROI;
    end

    % --- save png

    try
        imwrite(pic, fullfile(ntarget, [img.img_basename() '_nuisance.png']), 'png');
    catch
        fprintf('\n---> WARNING: Could not save mask PNG image! Check supported image formats!');
    end
end

if verbose, fprintf('\n---> done!\n'); end


% ======================================================
%   ---> open image
%

function [mimg] = getImage(mimg, fsimg, verbose)

    if isempty(mimg), return, end

    if ~isa(mimg, 'nimage')
        if strfind(mimg, '.names')
            if verbose, fprintf(verbose, mimg); end
            mimg = nimage.img_prep_roi(mimg, fsimg);
        else
            if verbose, fprintf(verbose, mimg); end
            mimg = nimage(mimg);
        end
    end
    mimg.data = mimg.image2D;


% ======================================================
%   ---> process extra ROI name
%

function [filename nomask] = processeROI(s)

    [filename, s] = strtok(s, '|');
    nomask = {};
    while ~isempty(s)
        s = strrep(s, '|', '');
        [r, s] = strtok(s, ',');
        if ~isempty(r)
            nomask(end+1) = {r};
        end
    end


