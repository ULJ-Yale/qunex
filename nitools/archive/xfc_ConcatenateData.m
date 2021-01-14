function [] = fc_ConcatenateData(flist, targetf)

%	
%	fc_ConcatenateData
%
%	Concatenates two or more time-series extracts
%	
%	flist   	- array list of Strings that are pathways to the time-series extract files
%	targetf		- a filename for the extracted timeseries
%
% 	Created by Joshua J Kim on 2008-07-24.



fprintf('\n\nConcatenating data ...');

total = load(flist{1});

for n = 2:length(flist)
	addition = load(flist{n});
	for x = 1:length(addition.data.ts)
		total.data.ts{x} = [total.data.ts{x} addition.data.ts{x}];
	end
	total.data.regions = [total.data.regions addition.data.regions];
	for y = 1:length(addition.data.ts)
		total.data.files{y} = [total.data.files{y} addition.data.files{y}];
	end
end

fprintf('\n\nSaving ...');

data.ts = total.data.ts;
data.regions = total.data.regions;
data.files = total.data.files;
save(targetf, 'data')

fprintf('\n\n FINISHED!\n\n');
