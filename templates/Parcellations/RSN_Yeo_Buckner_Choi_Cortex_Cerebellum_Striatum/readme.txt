This folder contains CIFTI files for the RSN parcellation from Yeo et al. (2011), Buckner et al. (2011)
and Choi et al. (2012).

Both 7-network and 17-network resolution versions are provided.

Separate files are provided for the Cerebral Cortex, Cerebellum, and Striatum
parcellations, as well as a combined version across all 3 structures.

Files with the suffix "filled" indicate that the files follow the standard
CIFTI template of 91282 greyordinates -- greyordinates which are not part of
the parcellation have a value of 0 (e.g. all subcortical voxels are zeroed out
in "rsn_yeo-cortex_17network_islands_LR_filled.dscalar.nii" which contains only 
the cortical parcellation).

"Networks" indicates that all parcels within a network are assigned the same
value/label (e.g. there are 7 different values in "rsn_yeo-cortex_7network_networks_LR_filled.dscalar.nii", 
corresponding to the 7 networks).

"Islands" indicates that each individual isolated parcel is assigned its own
value/label (e.g. there are 97 different values in "rsn_yeo-cortex_7network_islands_LR_filled.dscalar.nii", 
since there are multiple parcels in each network).
