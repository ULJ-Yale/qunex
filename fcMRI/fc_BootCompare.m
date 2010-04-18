function [out] = fc_BootCompare(nb, sfile, tfile, ofile)

%	
%	
%	
%	
%	
%	
%	
%	
%	

%  ----- read images

simg = fc_Read4DFP(sfile);
timg = fc_Read4DFP(tfile);

simg = reshape(simg, 48*48*64, []);
timg = reshape(timg, 48*48*64, []);

snum = size(simg, 2);
tnum = size(timg, 2);

%  ----- set up bootstrap

bs = bootstrp(nb, @(x)[x'], [1:snum]');
bs = bs';

%  ----- do it

bstep   = 64;
samples = 48*48;

fprintf('\nRunning ');

for n = 0:samples-1
	a = n * bstep + 1;
	b = a + bstep - 1;
	
	bst1 = simg(a:b,bs);                                   
	bst2 = bst1';                                          
	bst2 = reshape(bst2, snum, nb, bstep);                 % -> gives estimate x bootstrap x oxel
	bst3 = mean(bst2,1);                                   % -> gives average over estimates
	bst3 = reshape(bst3, nb, bstep);                       % -> reshapes to bootstrap x voxel
	
	
	for m = 1:tnum
		smp = repmat(timg(a:b,m)',nb,1);
		cmp = bst3 < smp;
		timg(a:b,m) = fc_ptoz(sum(cmp)'/nb);
	end
	if mod(n,48) == 0
		fprintf('.');
	end
end
fprintf('\nSaving...');
fc_Save4DFP(ofile,timg);

fprintf('\nMean...');
mimg = mean(simg,2);
fc_Save4DFP(strrep(sfile,'.img','-m.img'),mimg);

fprintf('\nDone!\n');


