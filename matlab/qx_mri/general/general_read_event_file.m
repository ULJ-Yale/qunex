function [out] = general_read_event_file(file, tunit)

%``general_read_event_file(file, tunit)``
%
%    Reads fidl event file and returns a structure.
%
%    INPUTS
%    ======
%
%    --file         fidl event file
%    --tunit
%
%     OUTPUT
%    ======
%
%    out
%        A structure that includes:
%
%        - frame   ... frame number of the event start
%        - elength ... event length in frames
%        - event_s ... start of the event in s
%        - event_l ... length of the event in s
%        - event   ... event code
%        - events  ... list of event names
%        - TR      ... TR in s
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 2 || isempty(tunit), tunit = 's'; end

[fin message] = fopen(file);
if fin == -1
    error('\n\nERROR: Could not open %s for reading. Please check your paths!\n\nMatlab message: %s', file, message);
end

s = fgetl(fin);
tevents = strread(s, '%s');
TR = str2num(char(tevents(1)));
tevents = tevents(2:length(tevents));

frame     = [];
elength = [];
event     = [];
beh     = [];
event_l = [];
event_s = [];

first = 1;

while feof(fin) == 0
    s = fgetl(fin);
    s = strrep(s, 'NA', 'NaN');

    data = strread(s, '%f');

    if length(data) >= 3

        frame     = [frame floor(data(1)/TR)+1];
        event_s = [event_s data(1)];

        el      = data(3);
        if strcmp(tunit, 'ms')
            el  = el / 1000;
        end

        elength = [elength floor(el/TR)];
        event_l = [event_l el];
        event     = [event data(2)];

        if first
            nbeh = length(data)-3;
            first = 0;
        end
        if nbeh
            beh = [beh; data(4:end)'];
        end
    elseif length(data) == 2
        if data(2) < 0
            frame     = [frame floor(data(1)/TR)+1];
            event_s = [event_s data(1)];
            elength = [elength abs(data(2))];
            event_l = [event_l floor(abs(data(2))*TR)];
            event     = [event -1];
        end
    end
end


fclose(fin);

out.fidl    = file;
out.frame   = frame';
out.elength = elength';
out.event_s = event_s';
out.event_l = event_l';
out.event   = event';
out.events  = tevents;
out.beh     = beh;
out.TR      = TR;
out.nevents = length(frame);

if max(event_l) >= 750 && min(event_l) > 10
    out = general_read_event_file(file, 'ms');
end
