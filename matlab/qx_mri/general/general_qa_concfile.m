% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

function [r, doIt] = general_qa_concfile(file, doIt, target)

%``function [r, doIt] = general_qa_concfile(file, doIt, target)``
%
%	Computes the specified statistics on images specified in the conc file and
%   saves them to the target file.
%
%   INPUTS
%   ======
%
%   --file      The conc file that specifies the images.
%   --do        A string specifying what statistics to compute ['m,sd'].
%   --target    The root name for the files to save the results to [''].
%
%   OUTPUTS
%   =======
%
%   r
%       An array of nimage objects with the resulting images, one volume for
%       each file. The volumes are in the order of files in the conc file. The
%       objects are in the order of statistics specified.
%
%   do
%       A cell array of statistics done.
%
%   USE
%   ===
%   The function reads the conc file and then runs img_stats(doIt) on each of the
%   files. It saves the results for each of the statistics in a separate file
%   named <target>.<stat>.<relevant extension>. If no target is specified no
%   files will be saved.
%
%	EXAMPLE USE
%   ===========
%
%   ::
%
%       general_qa_concfile('OP337.conc', 'm,sd,min,max', 'OP337');
%

if nargin < 3 || isempty(target), target = ''    ; end
if nargin < 2 || isempty(doIt),     doIt = {'m','sd'}; end

if ~iscell(doIt)
    doIt = strtrim(regexp(doIt, ',', 'split'));
end

files = general_read_concfile(file);
nfiles = length(files);
nstats = length(doIt);

t = nimage(files{1}, [], 1);
for nr = 1:nstats
    r(nr) = t.zeroframes(nfiles);
end

for n = 1:nfiles
    d = nimage(files{n});
    d = d.img_stats(doIt);
    d.data = d.image2D;
    for nr = 1:nstats
        r(nr).data(:,n) = d.data(:,nr);
    end
end

if ~isempty(target)
    for nr = 1:nstats
        r(nr).img_saveimage([target '.' doIt{nr}]);
    end
end
