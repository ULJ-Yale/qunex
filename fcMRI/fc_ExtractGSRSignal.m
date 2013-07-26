function  [] = fc_extractGSRSignal(flist, roifile, tfile, bolds)

% function  [] = fc_extractGSRSignal(flist, roifile, tfile, bolds)
%
%   function for extraction of GSR signal
%
%   flist   - file with subject list
%   roifile - file that specifies the ROI for which to export the GSR
%   tfile   - the file to export the timeseries to
%   bolds   - which bold files to work on
%
%   (c) Grega Repovs - 2013-07-26


if nargin < 4
    bolds = [];
    if nargin < 3
        tfile = [];
        if nargin < 2
            error('ERROR: Please specify flist an roifile!');
        end
    end
end

if tfile == [], tfile = 'GSR'; end
if bolds == [], bolds = [1]; end
nbolds = length(bolds);


%   ------------------------------------------------------------------------------------------
%                                                      make a list of all the files to process

fprintf('\n ... listing files to process');

subject = g_ReadSubjectsList(flist);
nsub = length(subject);

fprintf(' ... done.');

%   ------------------------------------------------------------------------------------------
%                                                         set up datastructure to save results

for n = 1:nsub
    data(n).subject = subject(n).id;
end



%   ------------------------------------------------------------------------------------------
%                                                The main loop ... go through all the subjects


for s = 1:nsub

    fprintf('\n ... processing %s', subject(s).id);

    % ---> reading ROI file

    fprintf('\n     ... creating ROI mask');

    if isfield(subject(s), 'roi')
        sroifile = subject(s).roi;
    else
        sroifile = [];
    end

    if strcmp(sroifile,'none')
        roi = gmrimage.mri_ReadROI(roifile);
    else
        roi = gmrimage.mri_ReadROI(roifile, sroifile);
    end
    nregions = length(roi.roi.roinames);

    % ---> running bolds

    for b in 1:nbolds

        data(s).bold(b).boldid = bolds(b)

        % load original, nogsr, gsr, coeff files

        forig  = gmrimage(sprintf('%s/images/images/functional/bold%d_g7_hpss.4dfp.img', subject(s).folder, b));
        fnogsr = gmrimage(sprintf('%s/images/images/functional/bold%d_g7_hpss_res-mwmvd.4dfp.img', subject(s).folder, b));
        fgsr   = gmrimage(sprintf('%s/images/images/functional/bold%d_g7_hpss_res-mwmvwbd.4dfp.img', subject(s).folder, b));
        fcoeff = gmrimage(sprintf('%s/images/images/functional/bold%d_g7_hpss_res-mwmvwbd-coeff.4dfp.img', subject(s).folder, b));

        % compute noGSR - GSR

        fdgsr  = fnogsr - fgsr;

        % extract WB and WBd

        data(s).bolds(b).WB    = forig.mri_ExtractROI(fcoeff, 2);
        data(s).bolds(b).WBd   = [0 diff(data(s).bolds(b).WB)];

        % extract Type 1 WBsd

        data(s).bolds(b).WBsd1 = zeros(nroi, length(data(s).bolds(b).WB ));
        for r = 1:nregions
            data(s).bolds(b).WBsd1(r,:) = data(s).bolds(b).WB * mean(fcoeff.data(roi.mri_ROIMask(r), 11)) + data(s).bolds(b).WBd * mean(fcoeff.data(roi.mri_ROIMask(r), 20));
        end

        % extract Type 2 WBsd

        data(s).bolds(b).WBsd2 = fdgsr.mri_ExtractROI(roi);

    end
end

save(targetf, 'data');

