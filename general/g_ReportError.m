function [] = g_ReportError(ME);

%``function [] = g_ReportError(ME)``;
%
%   Function for reporting of errors found in the code.
%

%   ~~~~~~~~~~~~~~~~~~
%
%   Changelog
%
%   2018-06-20 Grega Repovš
%              Initial version.
%

fprintf('\n\n=========================================\nExecution error! Processing failed! \nPlease check arguments and/or try running the command in Matlab or Octave directly.\n\nThe exact error reported:\n-----------------------------------------\n%s\n\n=========================================\n', prepareErrorReport(ME))



function [s] = prepareErrorReport(ME);

    s = '';
    s = [s sprintf('\nError identifier: %s', ME.identifier)];
    s = [s sprintf('\n   Error message: %s', ME.message)];
    for n = 1:length(ME.stack)
        if n == 1
            s = [s sprintf('\n     Error stack: %s -> %s [line: %d]', ME.stack(n).file, ME.stack(n).name, ME.stack(n).line)];
        else
            s = [s sprintf('\n                  %s -> %s [line: %d]', ME.stack(n).file, ME.stack(n).name, ME.stack(n).line)];
        end
    end
