function  [] = fc_ExtractGSRSignal(flist, roifile, tfile, bolds)

% function  [] = fc_ExtractGSRSignal(flist, roifile, tfile, bolds)
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

if isempty(tfile), tfile = 'GSR'; end
if isempty(bolds), bolds = [1]; end
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

    for b = 1:nbolds

        data(s).bold(b).boldid = bolds(b);

        % load original, nogsr, gsr, coeff, nuisance files
        
        fprintf('\n     ... reading data');

        forig  = gmrimage(sprintf('%s/images/functional/bold%d_g7_hpss.4dfp.img', subject(s).folder, b));
        fnogsr = gmrimage(sprintf('%s/images/functional/bold%d_g7_hpss_res-mwmvd.4dfp.img', subject(s).folder, b));
        fgsr   = gmrimage(sprintf('%s/images/functional/bold%d_g7_hpss_res-mwmvwbd.4dfp.img', subject(s).folder, b));
        fcoeff = gmrimage(sprintf('%s/images/functional/bold%d_g7_hpss_res-mwmvwbd_coeff.4dfp.img', subject(s).folder, b));
        fnuiss = gmrimage(sprintf('%s/images/ROI/nuisance/bold%d_nuisance.4dfp.img', subject(s).folder, b));
        
        fcoeff.data = fcoeff.image2D;
        fnuiss.data = fnuiss.image2D;

        % compute noGSR - GSR
        
        fprintf('\n     ... extracting signal');

        fdgsr  = fnogsr - fgsr;

        % extract WB and WBd

        data(s).bold(b).WB    = forig.mri_ExtractROI(fnuiss, 2);
        data(s).bold(b).WBd   = [0 diff(data(s).bold(b).WB)];

        % set up Type 1 and Type 2 WBsd extraction

        data(s).bold(b).WBsd1 = zeros(nregions+1, length(data(s).bold(b).WB ));
        data(s).bold(b).WBsd2 = zeros(nregions+1, length(data(s).bold(b).WB ));

        % if there are ROI specified, do them first

        if nregions > 0

            % Type 1

            for r = 1:nregions
                mask = roi.mri_ROIMask(r);
                data(s).bold(b).WBsd1(r,:) = data(s).bold(b).WB * mean(fcoeff.data(mask, 11)) + data(s).bold(b).WBd * mean(fcoeff.data(mask, 20));
            end

            % Type 2

            data(s).bold(b).WBsd2(1:nregions,:) = fdgsr.mri_ExtractROI(roi);

        end

        % add data for WB mask Type 1

        data(s).bold(b).WBsd1(nregions+1,:) = data(s).bold(b).WB * mean(fcoeff.data(fnuiss.mri_ROIMask(2), 11)) + data(s).bold(b).WBd * mean(fcoeff.data(fnuiss.mri_ROIMask(2), 20));

        % add data for WB mask Type 2

        data(s).bold(b).WBsd2(nregions+1,:) = fdgsr.mri_ExtractROI(fnuiss, 2);

    end
end

fprintf('\n... saving');
save(tfile, 'data');

fprintf('\nDONE!\n');

