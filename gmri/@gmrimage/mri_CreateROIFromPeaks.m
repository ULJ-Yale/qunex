function [img] = mri_CreateROIFrompeaksIn(img, peaksIn)
%function [img] = mri_CreateROIFrompeaksIn(img, peaksIn)
%
%   Creates ROI from given peaks data.
%
%   INPUT
%       peaksIn  - ROI data formated as:
%                  a) N x 5 matrix:
%                          [x1, y1, z1, radius1, value1;
%                           x2, y2, z2, radius2, value2;
%                                       ...
%                           xN, yN, zN, radiusN, valueN]
%                  b) string with N x 5 data, where rows are separated by
%                     a semicolon:
%                          'x1, y1, z1, radius1, value1 \n
%                           x2, y2, z2, radius2, value2 \n
%                           xN, yN, zN, radiusN, valueN'
%                  c) name of the file containing the data formated as
%                     described in part b).
%
%                  Where: x, y, z are coordinated of each peak,
%                         radius is the radious of the peak in mm,
%                         value is the value of the peak (ID, z value,...).
%
%   USE EXAMPLE
%       img = img.mri_CreateROIFrompeaksIn(peaksIn)
%
%   ---
%   Written by Aleksij Kraljic, 08-08-2017

% --- check weather the input is: a) matrix (nx5) b) string c) file
if ~isnumeric(peaksIn)
    if exist(peaksIn,'file') == 2
        peaksIn = [];
        fileID = fopen('ROI.txt','r');
        t = 0;
        i = 1;
        while t ~= -1
            t = fgetl(fileID);
            if t ~= -1
               peaksIn(i,:) = str2num(t); 
            end
            i = i + 1;
        end
        fclose(fileID);
    else
        peaksIn = str2num(peaksIn);
    end
end

% --- extract data from the input
X = peaksIn(:,1); Y = peaksIn(:,2); Z = peaksIn(:,3);
R = peaksIn(:,4);
val = peaksIn(:,5);
[num_pk, ~] = size(peaksIn);

% --- if img is CIFTI-2 extract volume components to a NIFTI format
embedBack = false;
if strcmpi(img.imageformat, 'CIFTI-2')
    surf_img = img;
    img = surf_img.mri_ExtractCIFTIVolume();
    embedBack = true;
end

% --- convert xyz to ijk
ijk = img.mri_GetIJK([X, Y, Z]);
i = ijk(:,1); j = ijk(:,2); k = ijk(:,3);

% --- clear img data to zero
img.data = zeros(size(img.data));

% --- grow ROIs from each peak
img.data = img.image4D;

for p = 1:num_pk
    N = ceil(R(p)/2);
    i1 = i(p)-N; j1 = j(p)-N; k1 = k(p)-N;
    i2 = i(p)+N; j2 = j(p)+N; k2 = k(p)+N;
    
    if i1 < 0, i1 = 0; end
    if i2 > 91, i2 = 91; end
    if j1 < 0, j1 = 0; end
    if j2 > 109, j2 = 109; end
    if k1 < 0, k1 = 0; end
    if k2 > 91, k2 = 91; end
    
    for I = i1:i2
        for J = j1:j2
            for K = k1:k2
                xyz = img.mri_GetXYZ([I,J,K]);
                dist = sqrt((xyz(1)-X(p))^2+(xyz(2)-Y(p))^2+(xyz(3)-Z(p))^2);
                % -> empty field: assign ROI value
                if dist <= R(p) && img.data(I,J,K) == 0
                    img.data(I,J,K) = val(p);
                % -> not empty field: handle by assigining ROI value of the closest one
                elseif dist <= R(p) && img.data(I,J,K) ~= 0
                   nInd = find(peaksIn(:,5) == img.data(I,J,K));
                   nX = peaksIn(nInd,1); nY = peaksIn(nInd,2); nZ = peaksIn(nInd,3);
                   cXYZ = img.mri_GetXYZ([I, J, K]);
                   nDist = sqrt((nX-cXYZ(1))^2+(nY-cXYZ(2))^2+(nZ-cXYZ(3))^2);
                   if nDist > dist
                       img.data(I,J,K) = val(p);
                   end
                end
            end
        end
    end
end

% --- if the input image is CIFTI-2 embed the modified data back
if embedBack
    surf_img = surf_img.mri_EmbedCIFTIVolume(img);
    img = surf_img;
end

end

