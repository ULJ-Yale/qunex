function [vroi, wbroi] = NROI_CreateROI(in, V, E)

%
%		creates ROI volumes for the given input volume
%		needs also masks for ventricles and eyes
%


% -----------   get thresholds ------------

Vs = in .* V;
Vs = sort(Vs, 'descend');
vthreshold = Vs(300);
mthreshold = Vs(2000);

bthreshold = 500;
idiff = 600;


% -----------   Erase ventricles from whole brain mask ------------

oimage = reshape(in, 48, 64, 48);
simage = reshape(V, 48, 64, 48);
eimage = reshape(E, 48, 64, 48);

wbroi = ones(size(oimage));
wbroi((oimage>vthreshold) & simage) = 0;
vroi = ~wbroi;

checked = zeros(size(oimage));
midway = checked;
midway(oimage>mthreshold) = 1;
nearest = cat(3,[0 0 0; 0 1 0; 0 0 0], [0 1 0; 1 1 1; 0 1 0], [0 0 0; 0 1 0; 0 0 0]);

schng = 0;
change = 1;
while change
%for n = 1:20
	change = 0;
	current = wbroi;
	for x = 2:47
		for y = 2:63
			for z = 2:47
				if (simage(x,y,z))
					if((current(x,y,z)==0) & (~checked(x,y,z)))
						local = current(x-1:x+1,y-1:y+1,z-1:z+1);
						focus = oimage(x-1:x+1,y-1:y+1,z-1:z+1);
						%if (n<20)
							midfocus = midway(x-1:x+1,y-1:y+1,z-1:z+1);
							local(midfocus==1) = 0;
						%end
						local((focus<=oimage(x,y,z)-idiff)& nearest==1) = 0;
						wbroi(x-1:x+1,y-1:y+1,z-1:z+1) = local;	
						checked(x,y,z) = 1;	
					end 
				end
			end
		end
	end
	chng = sum(sum(sum(xor(wbroi,current))));
	if (chng)
		% fprintf('%d ',chng);
		schng = schng + chng;
		change = 1;
	end
end
% fprintf(' done (%d)\n', schng);

vroi = ~wbroi;
wbroi(oimage<bthreshold) = 0;
wbroi(eimage==1) = 0;

% -----------   Create ventricle ROI ------------

%vroi = zeros(size(oimage));
%vroi(oimage > vthreshold) = 1;



