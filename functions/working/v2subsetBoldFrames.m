
% indices of frames to keep (Delay first 10 frames)
keepframes = [9:18 48:57 87:96 126:135 165:174 204:213 243:252 282:291 321:330 360:369]

% path to subjects
subjectsfolder = '/gpfs/project/fas/n3/Studies/Anticevic.DP5/subjects/'

% list of scans
scans = {'ta6143','ta5880','ta5927','ta6698','ta6508','pb0345','pb0769','pb1898','ta7396','ta7099','ta8215','ta8468','ta6764','ta5544','ta6155','ta6313','ta6325','ta6665','ta8787','pb2360','ta7061','ta7244','ta7496','ta8113','ta8182','ta8815','ta9168','ta9740','ta9588','ta9478','pb0508','pb0792','pb0890','pb1165','pb1452','pb2814','ta5679','pb3425','pb2572'}

% path to target data within subject
path = '/images/functional/'

% input CIFTI
datalist = {'bold3_Atlas_scrub_g7_hpss_res-VWMWBe.dtseries.nii','bold4_Atlas_scrub_g7_hpss_res-VWMWBe.dtseries.nii','bold12_Atlas_scrub_g7_hpss_res-VWMWBe.dtseries.nii','bold13_Atlas_scrub_g7_hpss_res-VWMWBe.dtseries.nii'}

% outname prefix
outname = 'DelayFrames_'

%% run for all subjects
for i = 1:length(scans)
	
	scanID = scans(i)
	
	for j = 1:length(datalist)
	
		data = datalist(j)
		
		% load original data
		infile = strcat(subjectsfolder,'/',scanID,'/',path,'/',data)
		bold = gmrimage(infile)
		
		% chose which frames to keep	
		boldSubset = bold
		boldSubset.data = bold.data(:,keepframes)
		
		% update frame counts
		boldSubset.frames=size(boldSubset.data,2)
		boldSubset.runframes=boldSubset.frames
		
		% save data
		outfile = char(strcat(subjectsfolder,'/',scanID,'/',path,'/',outname,data))
		boldSubset.mri_saveimage(outfile)
	
	end
end