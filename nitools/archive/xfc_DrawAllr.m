function [niz] = fc_DrawAll(alldata, t, roi)

%	
%	

tdata = alldata.tnizi;
rdata = alldata.rnizi;
dif = alldata.diff;

clc
for n = 1:length(tdata)

	side = tdata(n).fevents.events;
	if strcmp(side, 'l_long')
		side = 'left';
	else
		side = 'right';
	end
	
	droi = roi.(tdata(n).subject);
	naslov = [tdata(n).subject '-' tdata(n).data '-' side];
	
	img = fc_Read4DFP([tdata(n).subject '_5_25_50.img']);
	img = reshape(img, 48, 64, 48);
	stats = regionprops(img, 'Centroid');
	cord = [stats.Centroid];
	cord = reshape(cord, 3, [])';
	cord = [(cord(:,2).*-1/48+0.5)*2 (cord(:,1).*1/64-0.5)*2 (cord(:,3).*-1/48+1)];
	cord = [cord(:,1)+cord(:,1).*cord(:,3) cord(:,2)+cord(:,2).*cord(:,3)];

	xc = 265;
	yc = 350;

	xd = 200;
	yd = 300;

	cord = [cord(:,1)*xd + xc cord(:,2)*yd + yc];
	
%	fprintf('\nOpenNewDocument("task %s","task correlations", "subject: %s", "data: %s, %s side")\n', [tdata(n).subject '-' tdata(n).data '-' side], tdata(n).subject, tdata(n).data, side);
%	fc_DrawConnections(tdata(n).corr.r, tdata(n).corr.p_r, t, droi, cord);

%	fprintf('\nOpenNewDocument("rest %s","rest correlations", "subject: %s", "data: %s, %s side")\n', [tdata(n).subject '-' rdata(n).data '-' side], rdata(n).subject, rdata(n).data, side);
%	fc_DrawConnections(rdata(n).corr.r, rdata(n).corr.p_r, t, droi, cord);
	
	fprintf('\nOpenNewDocument("task-rest %s","task-rest correlations", "subject: %s", "data: %s, %s side")\n', [tdata(n).subject '-' tdata(n).data '-' side], tdata(n).subject, tdata(n).data, side);
	fc_DrawConnections(dif(n).mgdiffr, dif(n).pgdiffr, t, droi, cord);

end
