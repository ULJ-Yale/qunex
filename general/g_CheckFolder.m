function [ok] = g_CheckFile(filename, description, create, v)

if nargin < 4
	v = true;
	if nargin < 3
		create = true;
	end
end

if ~exist(filename, 'file')
	pause(5);
end

if exist(filename, 'file')
	if v
		fprintf('... found %s (%s)\n', description, filename);
	end
	ok = true;
else
	ok = false;
	if create 
		mkdir(filename);
		if v
			fprintf('... could not find %s (%s) a new folder was created!\n', description, filename);
		end
	else 
		if v & (~create)
			fprintf('... could not find %s (%s), please check your paths!\n', description, filename);
		end
	end
end
