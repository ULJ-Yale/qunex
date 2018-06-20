function [] = g_ReportError(ME);

%function [] = g_ReportError(ME);
%
%   Function for reporting of errors found in the code
%
%   ---
%   Written by Grega Repovš on 2018-06-20.
%

fprintf('\n\n=========================================\nExecution error! Processing failed! \nPlease check arguments and/or try running the command in Matlab or Octave directly.\n\nThe exact error reported:\n-----------------------------------------\n%s\n=========================================\n', getReport(ME))