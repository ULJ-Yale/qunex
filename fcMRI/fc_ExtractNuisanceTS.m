function [TS] = fc_ExtractNuisanceTS(B, ofile, ftarget, regress)

%	
%	Extract nuisance timeseries from the given BOLD run
%	
%	B - BOLD data
%	ofile - original (nonprocessed) BOLD file (to compute masks)
%	ftarget - folder where results are supposed to go, to put png overlays in 
%	regress - which regressors to extract
%	
%	

% ======================================================
% 	----> white matter

if strfind(regress, 'wm')
	WM = g_Read4DFP('Masks/WM.4dfp.img');
	TS.WM = mean(B(WM==1,:),1)';					fprintf(' WM');
end


% ======================================================
% 	----> ventricles and whole brain

if (~isempty(strfind(regress, 'wb')) | ~isempty(strfind(regress, 'v')))

	% 	----> load starting ventricle and eye masks

	V = g_Read4DFP('/data/iac12/space13/ccp/Matlab/Masks/V.4dfp.img');
	E = g_Read4DFP('/data/iac12/space13/ccp/Matlab/Masks/E.4dfp.img');

	% 	----> compute WB and V masks
	
	O = g_Read4DFPn(ofile, 1);						fprintf(' T2');
	[V WB] = NROI_CreateROI(O, V, E);				fprintf(' Seg');
	
	if strfind(regress, 'wb')
		WB = NROI_ShrinkROI(WB);						fprintf(' WB');
		WB = NROI_ShrinkROI(WB);						fprintf('.');
		WB = reshape(WB, 147456, 1);					fprintf('.');
		TS.WB = mean(B(WB==1,:),1)';					fprintf('.');
	end
		
	if strfind(regress, 'v')
		V = NROI_ShrinkROI(V);							fprintf(' V');
		V = reshape(V, 147456, 1);						fprintf('.');
		TS.V = mean(B(V==1,:),1)';						fprintf('.');
	end

end
	
% ======================================================
% 	----> save png overlays
						
						
if ftarget 

	O = g_Read4DFPn(ofile, 1);						fprintf(' T2');
	
	T2 = RGBReshape(O,3);
	
	if strfind(regress, 'v')
		V = RGBReshape(V,3);
	else
		V = 0;
	end
	
	if strfind(regress, 'wb')
		WB = RGBReshape(WB,3);
	else
		WB = 0;
	end
	
	if strfind(regress, 'wm')
		WM = RGBReshape(WM,3);
	else
		WM = 0;
	end
	
	img(:,:,1) = T2;
	img(:,:,2) = T2;
	img(:,:,3) = T2;

	img = img/max(max(max(img)));
	img = img * 0.7;
	img(:,:,3) = img(:,:,3)+WB*0.3;
	img(:,:,2) = img(:,:,2)+V*0.3;
	img(:,:,1) = img(:,:,1)+WM*0.3;

	path = strread(ofile, '%s', 'delimiter', '/');
	fname = char(path(length(path)));
	fname = strrep(fname, '.4dfp.img', strcat('_', regress, '_nuisance.png'));

	imwrite(img, strcat(ftarget, fname), 'png');  	fprintf(' png');
end

