function [out] = fc_CompareROICorrAll(tnizi, rnizi)

nnizi = length(tnizi);
combo = [];

for n = 1:nnizi
	
	key = [tnizi(n).subject '-' tnizi(n).data];
	for m = 1:nnizi
		lock = [rnizi(m).subject '-' rnizi(m).data];
		if strcmp(key, lock)
			break
		end
	end
		
	combo(n) = m;
	
	out.diff(n) = fc_CompareROICorr(tnizi(n), rnizi(m));

end


for n = 1:nnizi
	tnizi(n).corr = rmfield(tnizi(n).corr, {'bsr' 'bspr'});
	rnizi(n).corr = rmfield(rnizi(n).corr, {'bsr' 'bspr'});
end

for n = 1:nnizi
	out.tnizi(n) = tnizi(n);
	out.rnizi(n) = rnizi(combo(n));
end
