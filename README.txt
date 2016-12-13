# README File for Processing Pipelines

Background
==========
This is a general purpose analytic pipeline that handles flexible directory inputs and subject lists. 
The objective is to streamline functions pre and post HCP pipelines and dofcMRI code. 
The pipeline supports data organization, QA, building lists, various wb_command tools, etc.
The pipeline is flexible and can be updated by adding functions developed around other tools. 

Descriptions of functions
=====================
List of functions can be obtained by running the following command from the terminal: 

ap help

Usage
=============

 	-------- general help for analysis pipeline: -------- 

 		* interactive usage: 
		ap <function_name> <study_folder> '<list of cases>' [options]

 		* flagged usage: 
		ap --function=<function_name> --studyfolder=<study_folder> --subjects='<list of cases>' [options]

 		* interactive example (no flags): 
		ap dicomsort /some/path/to/study/subjects '100001 100002'

 		* flagged example (no interactive terminal input): 
		ap --function=dicomsort --studyfolder=/some/path/to/study/subjects --subjects='100001,100002'

 		* function-specific help and usage: 
		ap dicomsort

 	-------- list of specific supported function: -------- 

 		--- data organization --- 
		dicomsort			sort dicoms and setup nifti files from dicoms
		dicom2nii			convert dicoms to nifti files
		setuphcp 			setup data structure for hcp processing
		hpcsync 			sync with yale hpc cluster(s) for original hcp pipelines (studyfolder/)
		hpcsync2			sync with yale hpc cluster(s) for dofcmri integration (studyfolder/subject/hcp/subject)
		awshcpsync			sync hcp data from aws s3 cloud

 		--- hcp pipeline --- 
		hpc1				prefreesurfer component of the hcp pipeline (cluster aware)
		hpc2				freesurfer component of the hcp pipeline (cluster aware)
		hpc3				postfreesurfer component of the hcp pipeline (cluster aware)
		hpc4				volume component of the hcp pipeline (cluster aware)
		hpc5				surface component of the hcp pipeline (cluster aware)
		hpcd				diffusion component of the hcp pipeline (cluster aware)
		hcpdlegacy			diffusion processing that is hcp compliant for legacy data with standard fieldmaps (cluster aware)

 		--- generating lists & qc functions --- 
		setuplist	 		setup list for fcmri analysis / preprocessing or volume snr calculations
		nii4dfpconvert 			convert nifti hcp-processed bold data to 4dpf format for fild analyses
		cifti4dfpconvert 		convert cifti hcp-processed bold data to 4dpf format for fild analyses
		ciftismooth 			smooth & convert cifti bold data to 4dpf format for fild analyses
		fidlconc 			setup conc & fidl even files for glm analyses
		qcpreproc			run visual qc for a given modality (t1w,tw2,myelin,bold,dwi)

 		--- dwi analyses & probabilistic tractography functions --- 
		fsldtifit 			run fsl dtifit (cluster aware)
		fslbedpostxgpu 			run fsl bedpostx w/gpu (cluster aware)
		isolatesubcortexrois 		isolate subject-specific subcortical rois for tractography
		isolatethalamusfslnuclei 	isolate fsl thalamic rois for tractography
		probtracksubcortex 		run fsl probtrackx across subcortical nuclei (cpu)
		pretractography			generates space for cortical dense connectomes (cluster aware)
		pretractographydense		generates space for whole-brain dense connectomes (cluster aware)
		probtrackxgpucortex		run fsl probtrackx across cortical mesh for dense connectomes w/gpu (cluster aware)
		makedensecortex			generate dense cortical connectomes (cluster aware)
		probtrackxgpudense		run fsl probtrackx for whole brain & generates dense whole-brain connectomes (cluster aware)

 		--- misc analyses --- 
		boldparcellation		parcellate bold data and generate pconn files via user-specified parcellation
		dwidenseparcellation		parcellate dense dwi tractography data via user-specified parcellation
		printmatrix			extract parcellated matrix for bold data via yeo 17 network solutions
		boldmergenifti			merge specified nii bold timeseries
		boldmergecifti			merge specified citi bold timeseries
		bolddense			compute bold dense connectome (needs >30gb ram per bold)
		palmanalysis			run palm and extract data from rois (cluster aware)

 		--- fix ica de-noising --- 
		fixica				run fix ica de-noising on a given volume
		postfix				generates wb_view scene files in each subjects directory for fix ica results
		boldhardlinkfixica		setup hard links for single run fix ica results
		fixicainsertmean		re-insert mean image back into mapped fix ica data (needed prior to dofcmrip calls)
		fixicaremovemean		remove mean image from mapped fix ica data
		boldseparateciftifixica		separate specified bold timeseries (results from fix ica - use if bolds merged)
		boldhardlinkfixicamerged	setup hard links for merged fix ica results (use if bolds merged)
		

References
==========

Yang GJ, Murray JD, Repovs G, Cole MW, Savic A, Glasser MF, Pittenger C,
Krystal JH, Wang XJ, Pearlson GD, Glahn DC, Anticevic A. Altered global brain
signal in schizophrenia. Proc Natl Acad Sci U S A. 2014 May 20;111(20):7438-43.
doi: 10.1073/pnas.1405289111. PubMed PMID: 24799682; PubMed Central PMCID:
PMC4034208.
