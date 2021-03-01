function [res] = img_save_4dfp(obj, filename, extra)

%   ``function [res] = img_save_4dfp(obj, filename, extra)``
%
%   Saves a 4dfp image based on the existing header information.
%
%   INPUTS
%	======
%
%   --obj      	 nimage object
%   --filename 	 the filename to use
%   --extra    	 key, value structure of fields to add to ifh header file []
%
%	OUTPUT
%	======
%	
%	res
%
%

%   ~~~~~~~~~~~~~~~~~~
%
%   Changelog
%
%	2009-11-19 Grega Repovs
%			   Initial version.
%	2013-10-19 Grega Repovs
%			   Added call for embedding data


if nargin < 3
	extra = [];
end


% ---> embed extra data if available

obj = obj.img_embed_stats();

% ---> set up file to save

filename = strtrim(filename);
obj = obj.unmaskimg;

% -- force littleendian
%
% if find(ismember(obj.hdr4dfp.value, 'bigendian'))
%    obj.hdr4dfp.value{ismember(obj.hdr4dfp.value, 'bigendian')} = 'littleendian';
% end

mformat = 'b';
if ismember('littleendian', obj.hdr4dfp.value)
    mformat = 'l';
end

root = strrep(filename, '.img', '');
root = strrep(root, '.4dfp', '');

[fim message] = fopen([root '.4dfp.img'],'w', mformat);
if fim == -1
    error('\n\nERROR: Could not open %s for saving. Please check your paths!\n\nMatlab message: %s', [root '.4dfp.img'], message);
end

res = fwrite(fim, obj.data, 'float32');
fclose(fim);

hdrf = strcat(root, '.4dfp.hdr');
ifhf = strcat(root, '.4dfp.ifh');

if (exist(hdrf))
	delete(hdrf);
end
if (exist(ifhf))
	delete(ifhf);
end

[fifh message] = fopen(ifhf,'w');
if fifh == -1
    error('\n\nERROR: Could not open %s for saving. Please check your paths!\n\nMatlab message: %s', ifhf, message);
end

hdr = obj.hdr4dfp;
hdr.value{ismember(hdr.key, 'matrix size [4]')} = num2str(obj.frames);
nhdr = length(hdr.key);

for n = 1:nhdr
    fprintf(fifh, '%s := %s\n', hdr.key{n}, hdr.value{n});
end

for n = 1:length(extra)
	fprintf(fifh, '%s := %s\n', char(extra(n).key), char(extra(n).value));
end

fclose(fifh);
