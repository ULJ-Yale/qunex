% 
%  --- help for gmrimage/mri_ROIExtract ---
%
%  mri_ROIExtract - computes ROI extraction with the provided ROI file and data input
%
% Function to extract ROI data from target file based on ROI file 
% The file should consist of a single volume where ROIn is indicated by a scalar
% The input can have multiple volumes where a specific volume can be selected
%
% function [ROI input output outname] = mri_ROIExtract(roifile, inputfile, targetf, outname)
%
%   Returns
%       ROI   	- Input ROI file
%       input   - Input data file
%       targetf  - Target folder for results.
%       outname - Output file prefix name for results.
%
%   EXAMPLE USE
%   mri_ROIExtract('<roi_input_file>', '<data_input_file>','<output_target_folder>', '<output_file_prefix>');
%
%  ---
%  Written by Charlie Schleifer, 2017-08-20
%
%  2017-08-21 Alan Anticevic
%           - Edited generic functionality for single or multiple volumes
%

function [] = mri_ROIExtract(roifile, inputfile, targetf, outname)

% check for input arguments
if isempty(roifile),   return; end
if isempty(inputfile), return; end
if isempty(targetf),    return; end
if isempty(outname),   return; end

% create output directory
if ~exist(targetf, 'dir'), mkdir(targetf); end

% read images
mask = gmrimage(roifile);
if (mask.frames > 1 ), display('ERROR: roifile cannot have more than one frame'); return; end
input = gmrimage(inputfile);

% retrieve list of ROI labels
roiList = unique(mask.data);

% extract data from each ROI
for i = [1:length(roiList)];
	
	% get ROI value
	roiN = roiList(i);
	display(roiN)
	
	% initialize arrays
	tmp = [];
    allVolumes = [];

	% find indices belonging to ROI
	inds = find(mask.data > (roiN-0.5) & mask.data < (roiN+1)); 
	
	% extract ROI data from every subject (each frame in inputfile)
	for f = [1:input.frames];
		
		% get ROI data and mean
		tmp = input.data(inds,f);
		tmpMean = mean(tmp);
		
		% add to allVolumes
		allVolumes(:,f) = tmp;
		allVolumesMean(:,f) = tmpMean;
		
	end
	
	% save all volumes (one column per volume)
	s3 = strcat(targetf,'/',outname,'_ROI',num2str(i),'.csv');
	s4 = strcat(targetf,'/',outname,'_ROI',num2str(i),'_mean.csv');
	csvwrite([s3], allVolumes);
	csvwrite([s4], allVolumesMean);
	
end

return

