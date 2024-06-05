function [ok] = general_check_fcargs(options)

%``general_check_fcargs(options)``
%
%   Function checks if the arguments of the given fc measure is valid.
%
%   Parameters:
%       --options (struct)
%
%   Returns:
%       ok (boolean)
%

ok = true;
if ismember(options.fcmeasure, {'r', 'cv', 'rho', 'cc', 'coh', 'mar'}) && sum(strcmp(fieldnames(options), 'fcargs')) > 0
    fprintf('FC measure %s should have no additional arguments defined \n', options.fcmeasure);
    ok = false;
elseif strcmp(options.fcmeasure, 'icv') && ismember('fcargs', fieldnames(options))
    fc_args = fieldnames(options.fcargs);
    for i = 1:numel(fc_args)
        arg_val = options.fcargs.(fc_args{i});
        arg = fc_args{i};
        if ~ismember(arg, {'standardize', 'shrinkage'})
            fprintf('Argument %s for FC measure %s does not exist \n', arg, options.fcmeasure);
            ok = false;
        elseif strcmp(arg, 'standardize')
            if ~ismember(arg_val, {'partialcorr', 'semipartialcorr', ''})
                fprintf('Value of argument %s=%s for FC measure %s is not valid \n', arg, arg_val, options.fcmeasure);
                ok = false;
            end
        elseif strcmp(arg, 'shrinkage')
            if ~ismember(arg_val, {'OAS', 'LW', ''})
                fprintf('Value of argument %s=%s for FC measure %s is not valid \n', arg, arg_val, options.fcmeasure);
                ok = false;
            end
        end
    end
elseif strcmp(options.fcmeasure, 'mi') && ismember('fcargs', fieldnames(options))
   fc_args = fieldnames(options.fcargs);
   if size(options.fcargs, 1) > 1 || (size(options.fcargs, 1) == 1 && ~strcmp(fc_args{1}, 'k'))
       fprintf('FC measure %s should have at most one argument "k" \n', options.fcmeasure);
       ok = false;
   end
   arg_val = options.fcargs.(fc_args{1});
   if ~strcmp(arg_val, '') && (~isnumeric(arg_val) || arg_val < 1)
       fprintf('Argument "k" for FC measure %s should be integer > 0 \n', options.fcmeasure);
       ok = false;
   end
elseif strcmp(options.fcmeasure, 'te') && ismember('fcargs', fieldnames(options))
    fc_args = fieldnames(options.fcargs);
    for i = 1:numel(fc_args)
        arg_val = options.fcargs.(fc_args{i});
        arg = fc_args{i};
        if ~ismember(arg, {'lags', 'k'})
            fprintf('Argument %s for FC measure %s does not exist \n', arg, options.fcmeasure);
            ok = false;
        elseif ~isnumeric(arg_val) || arg_val < 1
            fprintf('Value of argument %s=%s for FC measure %s is not valid (arguments "lags" and "k" should be integers > 0) \n', arg, arg_val, options.fcmeasure);
            ok = false;
        end
    end
end


