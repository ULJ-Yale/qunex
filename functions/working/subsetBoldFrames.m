% this function creates a CIFTI named 'outf', saving only the frames in 'inf' specified in the vector'keepframes'
% example: subsetBoldFrames('bold3_Atlas_scrub_g7_hpss_res-VWMWBe.dtseries.nii', 'test_output.dtseries.nii', [9:18 48:57 87:96 126:135 165:174 204:213 243:252 282:291 321:330 360:369])

function [] = subsetBoldFrames(inf, outf, keepframes)
	
	% load original data
	bold = gmrimage(inf)
	
	% chose which frames to keep	
	display(keepframes)
	boldSubset = bold
	boldSubset.data = bold.data(:,keepframes)
	
	% update frame counts
	boldSubset.frames=size(boldSubset.data,2)
	boldSubset.runframes=boldSubset.frames
	
	% save data
	boldSubset.mri_saveimage(outf)

