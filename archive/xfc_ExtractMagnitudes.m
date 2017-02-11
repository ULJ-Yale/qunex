function [out] = fc_ExtractMagnitudes(mfile, rfile)

%	
%	fc_ExtractMagnitudes
%	
% 	Created by  on 2008-02-10.
% 	Copyright (c) 2008 . All rights reserved.
%	

mag = fc_Read4DFP(mfile);
mag = reshape(mag, 48*48*64, []);
roi = fc_Read4DFP(rfile);

roic = unique(roi);
nroi = length(roic);

for n = 1:nroi
	out(n).mag = mean(mag(roi == roic(n),:),1);
end

