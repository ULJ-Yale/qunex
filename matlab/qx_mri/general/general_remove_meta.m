function [out] = general_remove_meta(fin, fout)
%``general_remove_meta(fin, fout)``
%
%   Remove QuNex metadata from file.
%
%   .. qx_command:
%       type: matlab
%
%   Parameters:
%       --fin (str):
%           A path to the file from which to remove metadata.
%
%       --fout (str, default ''):
%           A path to save the output file. If empty, overwrites the input file.
%
%   Returns:
%       --out (nimage):
%           A nimage object with the extracted glm volumes.
%
%   Notes:
%       Some files created by QuNex contain metadata in the header that some
%       external tools may not be able to process correctly. This function
%       removes such metadata.
%
%   Examples:
%       ::
%
%           qunex general_remove_meta \
%               --fin='wm_effects.pscalar.nii' \
%               --fout='wm_effects_nometa.pscalar.ni'

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

    if nargin < 2 || isempty(fout)
        fout = fin;
    end

    ni = nimage(fin);
    ni.glm = [];
    ni.list = [];
    ni.roi = [];

    ni.img_saveimage(fout);

    if nargout > 0
        out = ni;
    end

end
