function [] = s_ComputeBehavioralCorrelations(imgfile, datafile, target)

%	function [] = s_ComputeBehavioralCorrelations(imgfile, datafile, target)
%	
%   The function computes correlations between given images and provided data and 
%   outputs resulting images per each behavioral variable.
%
%   Input parameters
%      imgfile  - data in either a single multi volume file or a conc file
%      datafile - a tab, space or comma delimited text file with a header line and one 
%                 column per variable
%      target   - a string specifying the results to compute separated by comma or space
%                 : 'r'  - compute independent correlations for each behavioral variable
%                 : 't1' - compute multiple regression (GLM) and report Type I SS based results
%                 : 't3' - compute multiple regression (GLM) and report Type III SS based results
%	
% 	Created by  on 2010-03-18.
% 	Copyright (c) 2010 Grega Repovs. All rights reserved.
%	

% ------ check the parameters

if nargin < 3
    target = 'r';
    if nargin < 2
        error('ERROR: Not enough parameters specified in the function call! Please check the documentation!')
    end
end

% ------ check files

g_CheckFile(datafile, 'data table file', 'errorstop');
g_CheckFile(imgfile, 'image data', 'errorstop');

% ------ read behavioral data

bdata = importdata(datafile);

% ------ read image data

img = nimage(imgfile);

% ===================
% ------ process data

% ------------------------> Correlations

if strfind(target, 'r')
    [r, Z] = img.img_ComputeCorrelations(bdata.data, true);
    
    for n = 1:length(bdata.colheaders)
        r.img_saveimageframe(n, [r.rootfilename '-' bdata.colheaders{n} '_r']);
        Z.img_saveimageframe(n, [r.rootfilename '-' bdata.colheaders{n} '_Z']);
    end
    
end

if strfind(target, 't1')
    [B, Z] = img.img_ComputeRTypeI(bdata.data, true);
    
    for n = 1:length(bdata.colheaders)
        B.img_saveimageframe(n, [r.rootfilename '-' bdata.colheaders{n} '_T-I_B']);
        Z.img_saveimageframe(n, [r.rootfilename '-' bdata.colheaders{n} '_T-I_Z']);
    end
    
end

if strfind(target, 't3')
    [B, Z] = img.img_ComputeRTypeIII(bdata.data, true);
    
    for n = 1:length(bdata.colheaders)
        B.img_saveimageframe(n, [r.rootfilename '-' bdata.colheaders{n} '_T-III_B']);
        Z.img_saveimageframe(n, [r.rootfilename '-' bdata.colheaders{n} '_T-III_Z']);
    end
    
end



