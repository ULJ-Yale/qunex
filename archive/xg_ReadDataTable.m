function [data] = g_ReadDataTable(file, header)

%	function [data] = g_ReadDataTable(file)
%	
%	Reads a tab or comma delimited file. Retuns a data matrix and a cell array with column names.
%	
%	Input parameters:
%	   file   - filename for the data file
%	   header - should we read the header or not [true | false]
%               an optional parameter with default value: true
%	
%	Output
%	   data.data   - data matrix
%	   data.names  - cell matrix with column names
%	
% 	Created by Grega Repovs on 2010-03-18.
% 	Copyright (c) 2010. All rights reserved.
%	

if nargin < 2
    header = true;
end

% ---- Check file

g_CheckFile(file, 'data table file', 'errorstop')

% ---- Open file

data = importdata(file)


