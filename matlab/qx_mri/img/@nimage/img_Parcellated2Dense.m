function [img] = img_Parcellated2Dense(img, verbose, defineMissing)

%``function [img] = img_Parcellated2Dense(img, verbose)``
%
%	Expands a parcelated image to a dense image
%
%   INPUTS
%   ======
%
%   --img               a parcelated cifti nimage image object to convert
%   --verbose           should it report the details [false]
%   --defineMissing     what value should be used in case of missing values 
%                       (number or 'NaN') [0]
%
%   OUTPUT
%   ======
%
%   img
%       a resulting dense cifti nimage image object
%
%   USE
%   ===
%
%   This method is used to expand a parcellated cifti image to a dense cifti
%   image based on the information stored in cifti metatada.
%

%   ~~~~~~~~~~~~~~~~~~
%
%   Changelog
%   2019-06-29 Grega Repovs
%              Initial version.
%

% --> process variables

if nargin < 3 || isempty(defineMissing),  defineMissing = 0; end
if nargin < 2 || isempty(verbose),        verbose = false;   end

% --> extract data and metadata from the input image

data = img.image2D;
xml  = cast(img.meta(find([img.meta.code] == 32)).data, 'char')';

% --> set up new image format

if strcmp(img.filetype, '.ptseries')
    if verbose fprintf('\n===> Expanding .ptseries to .dtseries'); end
    img.filetype = '.dtseries';
elseif strcmp(img.filetype, '.pscalar')
    if verbose fprintf('\n===> Expanding .pscalar to .dscalar'); end
    img.filetype = '.dscalar';
else
    error('ERROR: The image provided to img_Parcellated2Dense is neither ptseries nor pscalar! Aborting');
end

img.voxels = 91282;
ndata = zeros(img.voxels, img.frames);
ndata(:) = defineMissing;

% --> load cifti brain model

model = load('cifti_brainmodel');

% --> process parcells

parcels = regexp(xml, '<Parcel Name="(?<name>.*?)">.*?(?<parcelparts><.*?)\s*</Parcel>', 'names');
nparcels = length(parcels);

for p = 1:nparcels
    parcel = parcels(p);
    parcelparts = regexp(parcel.parcelparts, '<(?<structure>.*?)>(?<indeces>.*?)\s*</(?<datatype>.*?)>\s*', 'names');
    
    for pp = 1:length(parcelparts)
        parcelpart = parcelparts(pp);

        if strcmp(parcelpart.datatype, 'VoxelIndicesIJK')
            ix = textscan(parcelpart.indeces, '%d'); 
            ix = reshape(ix{1}, 3, [])';
            id = sum([ix(:,1) + ix(:, 2) * 91 + ix(:,3) * 91 * 109], 2);
            members = model.mapping.structure_type == 3 & ismember(model.mapping.structure_indices, id);
            if verbose fprintf('\n---> Expanding parcel %s to %d datapoints', parcel.name, sum(members)); end
            ndata(members, :) = repmat(data(p, :), sum(members), 1);

        elseif strcmp(parcelpart.datatype, 'Vertices')        
            structure = regexp(parcelpart.structure, '.*?="(?<structure>.*?)"', 'tokens');
            stype = find(ismember([model.cifti.longnames], structure{1}));
            if stype == 0
                error('ERROR: Could not identify cifti structure! Aborting!');
            end

            ix = textscan(parcelpart.indeces, '%d'); 
            id = ix{1};
            members = model.mapping.structure_type == stype & ismember(model.mapping.structure_indices, id);
            if verbose fprintf('\n---> Expanding parcel %s to %d datapoints', parcel.name, sum(members)); end
            ndata(members, :) = repmat(data(p, :), sum(members), 1);

        else
            error('ERROR: Could not identify parcel type! Aborting!');
        end
    end
end

img.data = ndata;