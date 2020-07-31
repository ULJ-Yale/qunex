function img = nimages(varone, dtype, frames, verbose)

%``function img = nimages(varone, dtype, frames, verbose)``
%
%   A wrapper for nimage class constructor to be used when an array of images is
%   to be returned rather than just a single image. It takes the same arguments
%   as nimage.
%
%   INPUTS
%   ======
%
%   --varone    A number of possible argument types:
%
%               string
%                   File(s) will be read into a nimage object.
%               data matrix  
%                   F nimage object will be generated with data from the data 
%                   matrix.
%               cell array   
%                   An array of grimage objects will be generated each item 
%                   dependent on the type of the cell type.
%               nimage     
%                   The image will be copied.
%
%    --dtype    The datatype to store the data in. ['single']
%               In case of numeric data that matches a standard CIFTI image, 
%               this variable is interpreted as the type of CIFTI image, one of 
%               'dtseries' or 'dscalar' ['dtseries']
%    --frames   The number of frames to read from the image, all by default.
%               In case of numeric data and 'dscalar' dtype, this variable is
%               interpreted as a list of map names, if not provided, maps will 
%               be named 'Map 1', 'Map 2', ...
%    --verbose  Whether to be talkative
%
%   OUTPUT
%   ======
%   
%   img 
%       An array of nimage objects.
%
%   Strings
%   -------
%
%   If varone is a string, reading of files will be attempted. The results
%   depend on the Specifics of a string provided:
%
%   a single filename
%       A single filename will be read as a single file and will result in an
%       object array of length 1. If the filename is a .conc file, all the files
%       listed in the .conc file will be concatenated together in one long file.
%       The number of frames from each file will be stored in obj.runframes
%       vector
%
%   pipe separated list of files
%       A pipe (|) separated list of files will result in reading and
%       concatenating all of the listed files into a single long image object.
%       The number of frames from each file will be stored in the obj.runframes
%       vector.
%
%   a semicolon separated list of files
%       A semicolon (';') separated list of files will result in an array of
%       nimage objects, each object can be a single image, .conc list of images
%       or pipe separated list of images.
%
%   EXAMPLE USE
%   ===========
%
%   ::
%
%       img1 = nimages();
%       img2 = nimages('t1w.nii.gz');
%       img3 = nimages('boldlist.conc');
%       img4 = nimages('bold1.nii.gz|bold2.nii.gz|bold3.nii.gz');
%       img5 = nimages('boldlist.conc;bold1.nii.gz;bold2.nii.gz|bold3.nii.gz');
%       img6 = nimages(randn(91,191,91));
%       img7 = nimages(randn(91282,5));
%       img8 = nimages(randn(91282,5), 'dscalar', {'A', 'B', 'C', 'D', 'E'});
%
%   The results will be an array of:
%
%   - img1 ... an empty nimage object.
%   - img2 ... a nimage object with the content of a T1w image.
%   - img3 ... a nimage object with concatenated files listed in 'boldlist.conc'.
%   - img4 ... a nimage object with three bold files concatenated.
%   - img5 ... three image objects, img5(1) a concatenated set of images as 
%     specified in 'boldlist.conc', img5(2) a single bold run, and img5(3) a two 
%     concatenated bold images.
%   - img6 ... a volume nifti image with a single frame, assuming standard 2mm 
%     MNI atlas.
%   - img7 ... a dense timeseries CIFTI image with 5 frames.
%   - img8 ... a dense scalar image with 5 maps named A to E.
%

%   ~~~~~~~~~~~~~~~~~~
%
%   Changelog
%
%   2018-08-11 Grega Repovs
%              First version based on nimage code


if nargin < 4, verbose = false;  end
if nargin < 3, frames = [];      end
if nargin < 2, dtype = 'single'; end

if nargin > 0
    if isa(varone, 'char')
        images = regexp(varone, ';', 'split');
        for n = 1:length(images)
            parts = regexp(images{n}, '\|', 'split');
            for p = 1:length(parts)
                if p == 1
                    t = nimage(parts{p}, dtype, frames, verbose);
                else
                    t = [t nimage(parts{p}, dtype, frames, verbose)];
                end
            end
            img(n) = t;
        end

    else
        img(1) = nimage(varone, dtype, frames, verbose);
    end
else
    img(1) = nimage();
end

