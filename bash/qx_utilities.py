def dwi_bedpostx_gpu():
    """
    ``dwi_bedpostx_gpu``

    This function runs the FSL bedpostx_gpu processing using a GPU-enabled
    node or via a GPU-enabled queue if using the scheduler option.

    It explicitly assumes the Human Connectome Project folder structure for
    preprocessing and completed diffusion processing. DWI data is expected to
    be in the following folder::

        <study_folder>/<session>/hcp/<session>/T1w/Diffusion

    Parameters:
        --sessionsfolder (str):
            Path to study folder that contains sessions.
        --sessions (str):
            Comma separated list of sessions to run.
        --fibers (str, default '3'):
            Number of fibres per voxel.
        --weight (str, default '1'):
            ARD weight, more weight means less secondary fibres per voxel.
        --burnin (str, default '1000'):
            Burnin period.
        --jumps (str, default '1250'):
            Number of jumps.
        --sample (str, default '25'):
            Sample every.
        --model (str, default '2'):
            Deconvolution model:

            - '1' ... with sticks,
            - '2' ... with sticks with a range of diffusivities,
            - '3' ... with zeppelins.

        --rician (str, default 'yes'):
            Replace the default Gaussian noise assumption with Rician noise
            ('yes'/'no').
        --gradnonlin (str, default detailed below):
            Consider gradient nonlinearities ('yes'/'no'). By default set
            automatically. Set to 'yes' if the file grad_dev.nii.gz is present,
            set to 'no' if it is not.
        --overwrite (str, default 'no'):
            Delete prior run for a given session.
        --scheduler (str):
            A string for the cluster scheduler (LSF, PBS or SLURM) followed by
            relevant options, e.g. for SLURM the string would look like this:
            --scheduler='SLURM,jobname=<name_of_job>,
            time=<job_duration>,ntasks=<numer_of_tasks>,
            cpus-per-task=<cpu_number>,mem-per-cpu=<memory>,
            partition=<queue_to_send_job_to>'
            Note: You need to specify a GPU-enabled queue or partition.

    Examples:
        Run directly via:

        >>> ${TOOLS}/${QUNEXREPO}/bash/qx_utilities/dwi_bedpostx_gpu.sh \\
            --<parameter1> --<parameter2> --<parameter3> ... --<parameterN>

        NOTE: --scheduler is not available via direct script call.

        Run via:

        >>> qunex dwi_bedpostx_gpu --<parameter1> --<parameter2> ... \\
                  --<parameterN>

        NOTE: scheduler is available via qunex call.

        --scheduler       A string for the cluster scheduler (LSF, PBS or SLURM)
                          followed by relevant options

        For SLURM scheduler the string would look like this via the qunex call::

            --scheduler='SLURM,jobname=<name_of_job>,time=<job_duration>, \\
            ntasks=<number_of_tasks>,cpus-per-task=<cpu_number>, \\
            mem-per-cpu=<memory>,partition=<queue_to_send_job_to>'

        >>> qunex dwi_bedpostx_gpu \\
                  --sessionsfolder='<path_to_study_sessions_folder>' \\
                  --sessions='<comma_separarated_list_of_cases>' \\
                  --fibers='3' \\
                  --burnin='3000' \\
                  --model='3' \\
                  --scheduler='<name_of_scheduler_and_options>' \\
                  --overwrite='yes'
    """


def dwi_dtifit():
    """
    ``dwi_dtifit``

    This function runs the FSL dtifit processing locally or via a scheduler.
    It explicitly assumes the Human Connectome Project folder structure for
    preprocessing and completed diffusion processing.

    The DWI data is expected to be in the following folder::

        <study_folder>/<session>/hcp/<session>/T1w/Diffusion

    Parameters:
        --sessionsfolder (str):
            Path to study folder that contains sessions.
        --sessions (str):
            Comma separated list of sessions to run.
        --overwrite (str):
            Delete prior run for a given session ('yes' / 'no').
        --species (str):
            dtifit currently supports processing of human and macaqu data. If
            processing macaques set this parameter to macaque.
        --mask (str, default 'T1w/Diffusion/nodif_brain_mask'):
            Set binary mask file.
        --bvecs (str, default 'T1w/Diffusion/bvecs'):
            b vectors file.
        --bvals (str, default 'T1w/Diffusion/bvals'):
            b values file.
        --cni (str):
            Input confound regressors [not set by default].
        --sse (str):
            Output sum of squared errors [not set by default].
        --wls (str):
            Fit the tensor with weighted least square [not set by default].
        --kurt (str):
            Output mean kurtosis map (for multi-shell data [not set by default].
        --kurtdir (str):
            Output parallel/perpendicular kurtosis map (for multi-shell data)
            [not set by default].
        --littlebit (str):
            Only process small area of brain [not set by default].
        --save_tensor (str):
            Save the elements of the tensor [not set by default].
        --zmin (str):
            Min z [not set by default].
        --zmax (str):
            Max z [not set by default].
        --ymin (str):
            Min y [not set by default].
        --ymax (str):
            Max y [not set by default].
        --xmin (str):
            Min x [not set by default].
        --xmax (str):
            Max x [not set by default].
        --gradnonlin (str):
            Gradient nonlinearity tensor file [not set by default].
        --scheduler (str):
            A string for the cluster scheduler (e.g. LSF, PBS or SLURM) followed
            by relevant options; e.g. for SLURM the string would look like
            this::

                --scheduler='SLURM,jobname=<name_of_job>,time=<job_duration>,ntasks=<numer_of_tasks>, cpus-per-task=<cpu_number>,mem-per-cpu=<memory>,partition=<queue_to_send_job_to>'

    Examples:
        Run directly via::

         >>> ${TOOLS}/${QUNEXREPO}/bash/qx_utilities/dwi_dtifit.sh \\
         --<parameter1> --<parameter2> --<parameter3> ... --<parameterN>

        NOTE: --scheduler is not available via direct script call.

        Run via:

        >>> qunex dwi_dtifit --<parameter1> --<parameter2> ... --<parameterN>

        NOTE: scheduler is available via qunex call.

        --scheduler
            A string for the cluster scheduler (e.g. LSF, PBS or SLURM) followed
            by relevant options.

        For SLURM scheduler the string would look like this via the qunex call::

         --scheduler='SLURM,jobname=<name_of_job>,time=<job_duration>,ntasks=<number_of_tasks>,cpus-per-task=<cpu_number>, mem-per-cpu=<memory>,partition=<queue_to_send_job_to>'

        >>> qunex dwi_dtifit \\
                  --sessionsfolder='<path_to_study_sessions_folder>' \\
                  --sessions='<comma_separarated_list_of_cases>' \\
                  --scheduler='<name_of_scheduler_and_options>' \\
                  --overwrite='yes'
    """


def dwi_eddy_qc():
    """
    ``dwi_eddy_qc``

    This function is based on FSL's eddy to perform quality control on diffusion
    MRI (dMRI) datasets. It explicitly assumes the that eddy has been run and
    that EDDY QC by Matteo Bastiani, FMRIB has been installed.

    For full documentation of the EDDY QC please examine the README file.

    The function assumes that eddy outputs are saved in the following folder::

        <folder_with_sessions>/<session>/hcp/<session>/Diffusion/eddy/

    Parameters:
        --sessionsfolder (str):
            Path to study folder that contains sessions.
        --session (str):
            Session ID to run EDDY QC on.
        --eddybase (str) :
            This is the basename specified when running EDDY (e.g.
            eddy_unwarped_images)
        --eddyidx (str):
            EDDY index file.
        --eddyparams (str):
            EDDY parameters file.
        --mask (str):
            Binary mask file (most qc measures will be averaged across voxels
            labeled in the mask).
        --bvalsfile (str):
            bvals input file.
        --report (str, default 'individual'):
            If you want to generate a group report ('individual' or 'group').
        --overwrite (str):
            Delete prior run for a given session.
        --eddypath (str, default '<study_folder>/<session>/hcp/<session>/Diffusion/eddy/'):
            Specify the relative path of the eddy folder you want to use for
            inputs.
        --bvecsfile (str):
            If specified, the tool will create a bvals_no_outliers.txt and a
            bvecs_no_outliers.txt file that contain the bvals and bvecs of the
            non-outlier volumes, based on the MSR estimates.

    Special parameters:
        --list (str):
            Text file containing a list of qc.json files obtained from SQUAD. If
            --report='group', then this argument needs to be specified.
        --groupvar (str):
            Text file containing extra grouping variable. Extra optional input
            if --report='group'.
        --outputdir (str, default '<eddyBase>.qc'):
              Output directory. Extra optional input if --report='group'.
        --update (str):
            Applies only if --report='group' - set to <true> to update existing
            single session qc reports.

    Output files:
        Outputs for individual run:

        - qc.pdf               ... single session QC report
        - qc.json              ... single session QC and data info
        - vols_no_outliers.txt ... text file that contains the list of the
          non-outlier volumes (based on eddy residuals)

        Outputs for group run:

        - group_qc.pdf ... single session QC report
        - group_qc.db  ... database

    Examples:
         >>> dwi_eddy_qc.sh --sessionsfolder='<path_to_study_folder_with_session_directories>' \\
                            --session='<session_id>' \\
                            --eddybase='<eddy_base_name>' \\
                            --report='individual' \\
                            --bvalsfile='<bvals_file>' \\
                            --mask='<mask_file>' \\
                            --eddyidx='<eddy_index_file>' \\
                            --eddyparams='<eddy_param_file>' \\
                            --bvecsfile='<bvecs_file>' \\
                            --overwrite='yes'
    """


def dwi_legacy():
    """
    ``dwi_legacy``

    This function runs the DWI preprocessing using the FUGUE method for legacy
    data that are not TOPUP compatible.

    It explicitly assumes the the Human Connectome Project folder structure for
    preprocessing.

    DWI data needs to be in the following folder::

        <study_folder>/<session>/hcp/<session>/T1w/Diffusion

    T1w data needs to be in the following folder::

        <study_folder>/<case>/hcp/<case>/T1w

    Warning:
        - If PreFreeSurfer component of the HCP Pipelines was run the function
          will make use of the T1w data [Results will be better due to superior
          brain stripping].
        - If PreFreeSurfer component of the HCP Pipelines was NOT run the
          function will start from raw T1w data [Results may be less optimal]. -
          If you are this function interactively you need to be on a GPU-enabled
          node or send it to a GPU-enabled queue.

    Parameters:
        --sessionsfolder (str, default '.'):
            Path to study data folder.
        --sessions (str):
            Comma separated list of sessions to run.
        --scanner (str):
            Name of scanner manufacturer ('siemens' or 'ge' supported).
        --echospacing (str):
            EPI Echo Spacing for data [in msec]; e.g. 0.69
        --PEdir (int):
            Use 1 for Left-Right Phase Encoding, 2 for Anterior-Posterior.
        --unwarpdir (str):
            Direction for EPI image unwarping; e.g. 'x' or 'x-' for LR/RL, 'y'
            or 'y-' for AP/PA; may been to try out both -/+ combinations.
        --usefieldmap (str):
            Whether to use the standard field map ('yes' | 'no'). If set to
            <yes> then the parameter --TE becomes mandatory.
        --diffdatasuffix (str):
            Name of the DWI image; e.g. if the data is called
            <SessionID>_DWI_dir91_LR.nii.gz - you would enter DWI_dir91_LR.
        --overwrite (str):
            Delete prior run for a given session ('yes' | 'no').

    Specific parameters:
        --TE (float):
            This is the echo time difference of the fieldmap sequence - find
            this out form the operator - defaults are *usually* 2.46ms on
            SIEMENS.

    Output files:
         - DiffFolder=${SessionsFolder}/${Session}/Diffusion
         - T1wDiffFolder=${SessionsFolder}/${Session}/T1w/Diffusion\_"$DiffDataSuffix"

         ::

             $DiffFolder/$DiffDataSuffix/rawdata
             $DiffFolder/$DiffDataSuffix/eddy
             $DiffFolder/$DiffDataSuffix/data
             $DiffFolder/$DiffDataSuffix/reg
             $DiffFolder/$DiffDataSuffix/logs
             $T1wDiffFolder

    Examples:
        Examples using Siemens FieldMap (needs GPU-enabled node).

        Run directly via:

        >>> ${TOOLS}/${QUNEXREPO}/bash/qx_utilities/DWIPreprocPipelineLegacy.sh \\
            --<parameter1> --<parameter2> --<parameter3> ... --<parameterN>

        NOTE: --scheduler is not available via direct script call.

        Run via:

        >>> qunex dwi_legacy --<parameter1> --<parameter2> ... --<parameterN>

        NOTE: scheduler is available via qunex call.

        --scheduler
            A string for the cluster scheduler (e.g. LSF, PBS or SLURM) followed
            by relevant options.

        For SLURM scheduler the string would look like this via the qunex call::

             --scheduler='SLURM,jobname=<name_of_job>,time=<job_duration>,ntasks=<number_of_tasks>,cpus-per-task=<cpu_number>,mem-per-cpu=<memory>,partition=<queue_to_send_job_to>'

        >>> qunex dwi_legacy \\
                  --sessionsfolder='<folder_with_sessions>' \\
                  --sessions='<comma_separarated_list_of_cases>' \\
                  --function='dwi_legacy' \\
                  --PEdir='1' \\
                  --echospacing='0.69' \\
                  --TE='2.46' \\
                  --unwarpdir='x-' \\
                  --diffdatasuffix='DWI_dir91_LR' \\
                  --usefieldmap='yes' \\
                  --scanner='siemens' \\
                  --overwrite='yes'

        Example with flagged parameters for submission to the scheduler using
        Siemens FieldMap (needs GPU-enabled queue):

        >>> qunex dwi_legacy \\
                  --sessionsfolder='<folder_with_sessions>' \\
                  --sessions='<comma_separarated_list_of_cases>' \\
                  --function='dwi_legacy' \\
                  --PEdir='1' \\
                  --echospacing='0.69' \\
                  --TE='2.46' \\
                  --unwarpdir='x-' \\
                  --diffdatasuffix='DWI_dir91_LR' \\
                  --scheduler='<name_of_scheduler_and_options>' \\
                  --usefieldmap='yes' \\
                  --scanner='siemens' \\
                  --overwrite='yes'

        Example with flagged parameters for submission to the scheduler using GE
        data without FieldMap (needs GPU-enabled queue):

        >>> qunex dwi_legacy \\
                  --sessionsfolder='<folder_with_sessions>' \\
                  --sessions='<comma_separarated_list_of_cases>' \\
                  --diffdatasuffix='DWI_dir91_LR' \\
                  --scheduler='<name_of_scheduler_and_options>' \\
                  --usefieldmap='no' \\
                  --PEdir='1' \\
                  --echospacing='0.69' \\
                  --unwarpdir='x-' \\
                  --scanner='ge' \\
                  --overwrite='yes'
    """


def dwi_parcellate():
    """
    ``dwi_parcellate``

    This function implements parcellation on the DWI dense connectomes using a
    whole-brain parcellation (e.g. Glasser parcellation with subcortical labels
    included).
    
    It explicitly assumes the the Human Connectome Project folder structure for
    preprocessing. Dense Connectome DWI data needs to be in the following
    folder::
    
        <folder_with_sessions>/<case>/hcp/<case>/MNINonLinear/Results/Tractography/
    
    Parameters:
        --sessionsfolder (str):
            Path to study data folder.
        --session (str):
            Comma separated list of sessions to run.
        --matrixversion (str):
            Matrix solution version to run parcellation on; e.g. 1 or 3.
        --parcellationfile (str):
            Specify the absolute path of the file you want to use for
            parcellation (e.g.
            /gpfs/project/fas/n3/Studies/Connectome/Parcellations/glasser_parcellation/LR_Colelab_partitions_v1d_islands_withsubcortex.dlabel.nii).
        --outname (str):
            Specify the suffix output name of the pconn file.
        --lengths (str, defaults 'no'):
            Parcellate lengths matrix ('yes' / 'no').
        --waytotal (str, defaults 'none'):
            Use the waytotal normalized version of the DWI dense connectome.
            Options:
    
            - 'none'     ... without waytotal normalization
            - 'standard' ... standard waytotal normalized
            - 'log'      ... log-transformed waytotal normalized.
    
    Examples:
        Run directly via:
    
        >>> ${TOOLS}/${QUNEXREPO}/bash/qx_utilities/dwi_parcellate.sh \\
         --<parameter1> --<parameter2> --<parameter3> ... --<parameterN>
    
        NOTE: --scheduler is not available via direct script call.
    
        Run via:
    
        >>> qunex dwi_parcellate --<parameter1> --<parameter2> ... \\
                  --<parameterN>
    
        NOTE: scheduler is available via qunex call.
    
        --scheduler
            A string for the cluster scheduler (e.g. LSF, PBS or SLURM) followed by
            relevant options.
    
        For SLURM scheduler the string would look like this via the qunex call::
    
            --scheduler='SLURM,jobname=<name_of_job>,time=<job_duration>,ntasks=<number_of_tasks>,cpus-per-task=<cpu_number>,mem-per-cpu=<memory>,partition=<queue_to_send_job_to>'
    
        >>> qunex dwi_parcellate --sessionsfolder='<folder_with_sessions>' \\
                  --sessions='<comma_separarated_list_of_cases>' \\
                  --matrixversion='3' \\
                  --parcellationfile='<dlabel_file_for_parcellation>' \\
                  --overwrite='no' \\
                  --outname='LR_Colelab_partitions_v1d_islands_withsubcortex'
    
        Example with flagged parameters for submission to the scheduler:
    
        >>> qunex dwi_parcellate --sessionsfolder='<folder_with_sessions>' \\
                  --sessions='<comma_separarated_list_of_cases>' \\
                  --matrixversion='3' \\
                  --parcellationfile='<dlabel_file_for_parcellation>' \\
                  --overwrite='no' \\
                  --outname='LR_Colelab_partitions_v1d_islands_withsubcortex' \\
                  --scheduler='<name_of_scheduler_and_options>'
    """


def dwi_probtrackx_dense_gpu():
    """
    ``dwi_probtrackx_dense_gpu``

    This function runs the probtrackxgpu dense whole-brain connectome generation by
    calling ${ScriptsFolder}/run_matrix1.sh or ${ScriptsFolder}/run_matrix3.sh.
    Note that this function needs to send work to a GPU-enabled queue or you need
    to run it locally from a GPU-equiped machine.

    It explicitly assumes the Human Connectome Project folder structure and
    completed dwi_bedpostx_gpu and dwi_pre_tractography functions processing:

    - HCP Pipelines
    - FSL 5.0.9 or greater

    Processed DWI data needs to be here::

        <study_folder>/<session>/hcp/<session>/T1w/Diffusion

    BedpostX output data needs to be here::

        <study_folder>/<session>/hcp/<session>/T1w/Diffusion.bedpostX

    T1w images need to be in MNINonLinear space here::

        <study_folder>/<session>/hcp/<session>/MNINonLinear

    Parameters:
        --sessionsfolder (str):
            Path to study folder that contains sessions.
        --sessions (str):
            Comma separated list of sessions to run.
        --overwrite (str):
            Delete a prior run for a given session ('yes' / 'no').
            Note: this will delete only the Matrix run specified by the -omatrix
            flag.
        --omatrix1 (str):
            Specify if you wish to run matrix 1 model [yes or omit flag]
        --omatrix3 (str):
            Specify if you wish to run matrix 3 model [yes or omit flag]
        --nsamplesmatrix1 (str, default '10000'):
            Number of samples.
        --nsamplesmatrix3 (str, default '3000'):
            Number of samples.
        --nsamplesmatrix1 (str, default '10000'):
            Number of samples.
        --nsamplesmatrix3 (str, default '3000'):
            Number of samples.
        --distancecorrection (str, default 'no'):
            Use distance correction.
        --storestreamlineslength (str, default 'no'):
            Store average length of the streamlines.
        --scriptsfolder (str):
            Location of the probtrackX GPU scripts.
        --loopcheck (flag):
            Generic parameter set by default (will be parameterized in the future).
        --forcedir (flag):
            Generic parameter set by default (will be parameterized in the future).
        --fibthresh (str, default '0.01'):
            Generic parameter set by default (will be parameterized in the future).
        --c (str, default '0.2'):
            Generic parameter set by default (will be parameterized in the future).
        --sampvox (str, default '2'):
            Generic parameter set by default (will be parameterized in the future).
        --randfib (str, default '1'):
            Generic parameter set by default (will be parameterized in the future).
        --S (str, default '2000'):
            Generic parameter set by default (will be parameterized in the future).
        --steplength (str, default '0.5'):
            Generic parameter set by default (will be parameterized in the future).

    Output files:
        Dense Connectome CIFTI Results in MNI space for Matrix1 will be here::

           <study_folder>/<session>/hcp/<session>/MNINonLinear/Results/Conn1.dconn.nii.gz

        Dense Connectome CIFTI Results in MNI space for Matrix3 will be here::

           <study_folder>/<session>/hcp/<session>/MNINonLinear/Results/Conn3.dconn.nii.gz

    Notes:
        Use:
            The function calls either of these based on the --omatrix1 and --omatrix3 flags::

                $HCPPIPEDIR_dMRITractFull/tractography_gpu_scripts/run_matrix1.sh
                $HCPPIPEDIR_dMRITractFull/tractography_gpu_scripts/run_matrix3.sh

            Both functions are cluster-aware and send the jobs to the GPU-enabled
            queue. They do not work interactively.

        Note on waytotal normalization and log transformation of streamline counts:
            waytotal normalization is computed automatically as part of the run
            prior to any inter-session or group comparisons to account for
            individual differences in geometry and brain size. The function divides
            the dense connectome by the waytotal value, turning absolute streamline
            counts into relative proportions of the total streamline count in each
            session.

            Next, a log transformation is computed on the waytotal normalized data,
            which will yield stronger connectivity values for longe-range
            projections. Log-transformation accounts for algorithmic distance bias
            in tract generation (path probabilities drop with distance as
            uncertainty is accumulated).

            See Donahue et al. (2016) The Journal of Neuroscience, 36(25):6758–6770.
            DOI: https://doi.org/10.1523/JNEUROSCI.0493-16.2016

            The outputs for these files will be in::

                /<path_to_study_sessions_folder>/<session>/hcp/<session>/MNINonLinear/Results/Tractography/<MatrixName>_waytotnorm.dconn.nii
                /<path_to_study_sessions_folder>/<session>/hcp/<session>/MNINonLinear/Results/Tractography/<MatrixName>_waytotnorm_log.dconn.nii

    Examples:
        Run directly via:

        >>> ${TOOLS}/${QUNEXREPO}/bash/qx_utilities/dwi_probtrackx_dense_gpu.sh \\
        --<parameter1> --<parameter2> --<parameter3> ... --<parameterN>

        NOTE: --scheduler is not available via direct script call.

        Run via:

        >>> qunex dwi_probtrackx_dense_gpu --<parameter1> --<parameter2> ... --<parameterN>

        NOTE: scheduler is available via qunex call.

        --scheduler
            A string for the cluster scheduler (e.g. LSF, PBS or SLURM) followed by
            relevant options.

        For SLURM scheduler the string would look like this via the qunex call::

            --scheduler='SLURM,jobname=<name_of_job>,time=<job_duration>,ntasks=<number_of_tasks>,cpus-per-task=<cpu_number>,mem-per-cpu=<memory>,partition=<queue_to_send_job_to>'

        >>> qunex dwi_probtrackx_dense_gpu --sessionsfolder='<path_to_study_sessions_folder>' \\
                  --sessions='<comma_separarated_list_of_cases>' \\
                  --scheduler='<name_of_scheduler_and_options>' \\
                  --omatrix1='yes' \\
                  --nsamplesmatrix1='10000' \\
                  --overwrite='no'
    """


def dwi_seed_tractography_dense():
    """
    ``dwi_seed_tractography_dense``

    This function implements reduction on the DWI dense connectomes using a given
    'seed' structure (e.g. thalamus).

    It explicitly assumes the the Human Connectome Project folder structure for
    preprocessing. Dense Connectome DWI data needs to be in the following folder::

        <folder_with_sessions>/<case>/hcp/<case>/MNINonLinear/Results/Tractography/

    It produces the following outputs:

    - Dense connectivity seed tractography file:
      ``<folder_with_sessions>/<case>/hcp/<case>/MNINonLinear/Results/Tractography/<session>_Conn<matrixversion>_<outname>.dconn.nii``
    - Dense scalar seed tractography file:
      ``<folder_with_sessions>/<case>/hcp/<case>/MNINonLinear/Results/Tractography/<session>_Conn<matrixversion>_<outname>_Avg.dscalar.nii``

    Parameters:
        --sessionsfolder (str):
            Path to study folder that contains sessions.
        --sessions (str):
            Comma separated list of sessions to run.
        --matrixversion (str):
            Matrix solution version to run parcellation on; e.g. 1 or 3.
        --seedfile (str):
            Specify the absolute path of the seed file you want to use as a seed for
            dconn reduction (e.g.
            <study_folder>/<case>/hcp/<case>/MNINonLinear/Results/Tractography/CIFTI_STRUCTURE_THALAMUS_RIGHT.nii.gz).
            Note: If you specify --seedfile='gbc' then the function computes an
            average across all streamlines from every greyordinate to all other
            greyordinates.
        --outname (str):
            Specify the suffix output name of the dscalar file.
        --overwrite (str):
            Delete prior run for a given session ('yes' / 'no').
        --waytotal (str, default 'none'):
            Use the waytotal normalized version of the DWI dense connectome.
            Default:

            - 'none'     ... without waytotal normalization
            - 'standard' ... standard waytotal normalized
            - 'log'      ... log-transformed waytotal normalized.

    Examples:
        Run directly via:

        >>> ${TOOLS}/${QUNEXREPO}/bash/qx_utilities/dwi_seed_tractography_dense.sh \\
            --<parameter1> --<parameter2> --<parameter3> ... --<parameterN>

        NOTE: --scheduler is not available via direct script call.

        Run via:

        >>> qunex dwi_seed_tractography_dense --<parameter1> --<parameter2> ... --<parameterN>

        NOTE: scheduler is available via qunex call.

        --scheduler
            A string for the cluster scheduler (e.g. LSF, PBS or SLURM) followed by
            relevant options.

        For SLURM scheduler the string would look like this via the qunex call::

            --scheduler='SLURM,jobname=<name_of_job>,time=<job_duration>,ntasks=<number_of_tasks>,cpus-per-task=<cpu_number>,mem-per-cpu=<memory>,partition=<queue_to_send_job_to>'

        >>> qunex dwi_seed_tractography_dense --sessionsfolder='<folder_with_sessions>' \\
                   --session='<case_id>' \\
                   --matrixversion='3' \\
                   --seedfile='<folder_with_sessions>/<case>/hcp/<case>/MNINonLinear/Results/Tractography/CIFTI_STRUCTURE_THALAMUS_RIGHT.nii.gz' \\
                   --overwrite='no' \\
                   --outname='THALAMUS'
    """


def extract_roi():
    """
    ``extract_roi``

    This function calls img_roi_extract.m and extracts data from an input file for
    every ROI in a given template file. The function needs a matching file type for
    the ROI input and the data input (i.e. both NIFTI or CIFTI). It assumes that
    the template ROI file indicates each ROI in a single volume via unique scalar
    values.

    Parameters:
        --roifile (str):
            Path ROI file (either a NIFTI or a CIFTI with distinct scalar values per
            ROI).
        --inputfile (str):
            Path to input file to be read that is of the same type as --roifile
            (i.e. CIFTI or NIFTI).
        --outpath (str):
            New or existing directory to save outputs in.
        --outname (str):
            Output file base-name (to be appended with 'ROIn').

    Output files:
        <output_name>.csv
           Matrix with one ROI per row and one column per frame in
           singleinputfile.

    Examples:
        >>> qunex roi_extract \\
        --roifile='<path_to_roifile>' \\
        --inputfile='<path_to_inputfile>' \\
        --outdir='<path_to_outdir>' \\
        --outname='<output_name>'
    """


def fc_compute_wrapper():
    """
    ``fc_compute_wrapper``

    This function implements Global Brain Connectivity (GBC) or seed-based
    functional connectivity (FC) on the dense or parcellated (e.g. Glasser
    parcellation).

    For more detailed documentation run <help fc_compute_gbc3>, <help
    nimage.img_compute_gbc> or <help fc_compute_seedmaps_multiple> inside MATLAB.

    Parameters:
        --calculation (str):
            Run <seed>, <gbc> or <dense> calculation for functional connectivity.
        --runtype (str):
            Run calculation on a <list> (requires a list input), on 'individual'
            sessions (requires manual specification) or a 'group' of individual
            sessions (equivalent to a list, but with manual specification).
        --targetf (str):
            Specify the absolute path for output folder. If using
            --runtype='individual' and left empty the output will default to
            --inputpath location for each session
        --overwrite (str, default 'no'):
            Delete prior run for a given session.
        --covariance (str, default 'false'):
            Whether to compute covariances instead of correlations ('true' /
            'false').

    Specific parameters:
        --flist (str):
            Specify ∗.list file of session information. If specified then
            --sessionsfolder, --inputfile, --session and --outname are omitted.
        --sessionsfolder (str):
            Path to study sessions folder.
        --sessions (str):
            Comma separated list of sessions to run.
        --inputfiles (str):
            Specify the comma separated file names you want to use (e.g.
            /bold1_Atlas_MSMAll.dtseries.nii,bold2_Atlas_MSMAll.dtseries.nii).
        --inputpath (str):
            Specify path of the file you want to use relative to the master study
            folder and session directory (e.g. '/images/functional/').
        --outname (str):
            Specify the suffix name of the output file name.
        --target (str, default detailed below):
            Array of ROI codes that define target ROI. Defaults to FreeSurfer cortex
            codes.
        --rsmooth (str, default ''):
            Radius for smoothing (no smoothing if empty).
        --rdilate (str, default ''):
            Radius for dilating mask (no dilation if empty).
        --gbc-command (str):
            Specify the the type of gbc to run. This is a string describing GBC to
            compute. E.g. 'mFz:0.1|mFz:0.2|aFz:0.1|aFz:0.2|pFz:0.1|pFz:0.2'

            mFz:t
                computes mean Fz value across all voxels (over threshold t)
            aFz:t
                computes mean absolute Fz value across all voxels (over threshold t)
            pFz:t
                computes mean positive Fz value across all voxels (over threshold t)
            nFz:t
                computes mean positive Fz value across all voxels (below
                threshold t)
            aD:t
                computes proportion of voxels with absolute r over t
            pD:t
                computes proportion of voxels with positive r over t
            nD:t
                computes proportion of voxels with negative r below t
            mFzp:n
                computes mean Fz value across n proportional ranges
            aFzp:n
                computes mean absolute Fz value across n proportional ranges
            mFzs:n
                computes mean Fz value across n strength ranges
            pFzs:n
                computes mean Fz value across n strength ranges for positive
                correlations
            nFzs:n
                computes mean Fz value across n strength ranges for negative
                correlations
            mDs:n
                computes proportion of voxels within n strength ranges of r
            aDs:n
                computes proportion of våoxels within n strength ranges of
                absolute r
            pDs:n
                computes proportion of voxels within n strength ranges of
                positive r
            nDs:n
                computes proportion of voxels within n strength ranges of
                negative r.

        --verbose (str, default 'false'):
            Report what is going on.
        --time (str, default 'false'):
            Whether to print timing information.
        --vstep (str, default '1200'):
            How many voxels to process in a single step.
        --roinfo (str):
            An ROI file for the seed connectivity.
        --method (str, default 'mean'):
            Method for extracting timeseries - 'mean' or 'pca'.
        --options (str, default ''):
            A string defining which session files to save. Default assumes all:

            - 'r'  ... save map of correlations
            - 'f'  ... save map of Fisher z values
            - 'cv' ... save map of covariances
            - 'z'  ... save map of Z scores.

        --extractdata (str):
            Specify if you want to save out the matrix as a CSV file (only available
            if the file is a ptseries).
        --ignore (str, default ''):
            The column in ∗_scrub.txt file that matches bold file to be used for
            ignore mask. All if empty.
        --mask (str):
            An array mask defining which frames to use (1) and which not (0). All if
            empty. If single value is specified then this number of frames is
            skipped.
        --mem-limit (str, default '4'):
            Restrict memory. Memory limit expressed in gigabytes.

    Examples:
        Run directly via:

        >>> ${TOOLS}/${QUNEXREPO}/bash/qx_utilities/fc_compute_wrapper.sh \\
            --<parameter1> --<parameter2> --<parameter3> ... --<parameterN>

        NOTE: --scheduler is not available via direct script call.

        Run via:

        >>> qunex fc_compute_wrapper --<parameter1> --<parameter2> ... --<parameterN>

        NOTE: scheduler is available via qunex call.

        --scheduler
            A string for the cluster scheduler (e.g. LSF, PBS or SLURM) followed by
            relevant options.

        For SLURM scheduler the string would look like this via the qunex call::

            --scheduler='SLURM,jobname=<name_of_job>,time=<job_duration>,ntasks=<number_of_tasks>,cpus-per-task=<cpu_number>,mem-per-cpu=<memory>,partition=<queue_to_send_job_to>'

        >>> qunex fc_compute_wrapper \\
                  --sessionsfolder='<folder_with_sessions>' \\
                  --calculation='seed' \\
                  --runtype='individual' \\
                  --sessions='<comma_separarated_list_of_cases>' \\
                  --inputfiles='<files_to_compute_connectivity_on>' \\
                  --inputpath='/images/functional' \\
                  --extractdata='yes' \\
                  --ignore='udvarsme' \\
                  --roinfo='ROI_Names_File.names' \\
                  --options='' \\
                  --method='' \\
                  --targetf='<path_for_output_file>' \\
                  --mask='5' \\
                  --covariance='false'

        >>> qunex fc_compute_wrapper \\
                  --sessionsfolder='<folder_with_sessions>' \\
                  --runtype='list' \\
                  --flist='sessions.list' \\
                  --extractdata='yes' \\
                  --outname='<name_of_output_file>' \\
                  --ignore='udvarsme' \\
                  --roinfo='ROI_Names_File.names' \\
                  --options='' \\
                  --method='' \\
                  --targetf='<path_for_output_file>' \\
                  --mask='5' \\
                  --covariance='false'

        >>> qunex fc_compute_wrapper \\
                  --sessionsfolder='<folder_with_sessions>' \\
                  --calculation='gbc' \\
                  --runtype='individual' \\
                  --sessions='<comma_separarated_list_of_cases>' \\
                  --inputfiles='bold1_Atlas_MSMAll.dtseries.nii' \\
                  --inputpath='/images/functional' \\
                  --extractdata='yes' \\
                  --outname='<name_of_output_file>' \\
                  --ignore='udvarsme' \\
                  --gbc-command='mFz:' \\
                  --targetf='<path_for_output_file>' \\
                  --mask='5' \\
                  --target='' \\
                  --rsmooth='0' \\
                  --rdilate='0' \\
                  --verbose='true' \\
                  --time='true' \\
                  --vstep='10000' \\
                  --covariance='false'

        >>> qunex fc_compute_wrapper \\
                  --sessionsfolder='<folder_with_sessions>' \\
                  --calculation='gbc' \\
                  --runtype='list' \\
                  --flist='sessions.list' \\
                  --extractdata='yes' \\
                  --outname='<name_of_output_file>' \\
                  --ignore='udvarsme' \\
                  --gbc-command='mFz:' \\
                  --targetf='<path_for_output_file>' \\
                  --mask='5' \\
                  --target='' \\
                  --rsmooth='0' \\
                  --rdilate='0' \\
                  --verbose='true' \\
                  --time='true' \\
                  --vstep='10000' \\
                  --covariance='false'
    """


def parcellate_anat():
    """
    ``parcellate_anat``

    This function implements parcellation on the dense cortical thickness OR myelin
    files using a whole-brain parcellation (e.g. Glasser parcellation with
    subcortical labels included).

    Parameters:
         --sessionsfolder (str):
            Path to study data folder.
         --session (str):
            Comma separated list of sessions to run
         --inputdatatype (str):
            Specify the type of dense data for the input file (e.g. MyelinMap_BC or
            corrThickness).
         --parcellationfile (str):
            Specify the absolute path of the ∗.dlabel file you want to use for
            parcellation.
         --outname (str):
            Specify the suffix output name of the pconn file.
         --overwrite (str):
            Delete prior run for a given session ('yes' / 'no').
         --extractdata (flag):
            Specify if you want to save out the matrix as a CSV file.

    Examples:
        Run directly via:

        >>> ${TOOLS}/${QUNEXREPO}/bash/qx_utilities/parcellate_anat.sh \\
            --<parameter1> --<parameter2> --<parameter3> ... --<parameterN>

        NOTE: --scheduler is not available via direct script call.

        Run via:

        >>> qunex parcellate_anat \\
                  --<parameter1> --<parameter2> --<parameter3> ... --<parameterN>

        NOTE: scheduler is available via qunex call:

        --scheduler
            A string for the cluster scheduler (e.g. LSF, PBS or SLURM) followed by
            relevant options.

        For SLURM scheduler the string would look like this via the qunex call::

            --scheduler='SLURM,jobname=<name_of_job>,time=<job_duration>,ntasks=<number_of_tasks>,cpus-per-task=<cpu_number>,mem-per-cpu=<memory>,partition=<queue_to_send_job_to>'

        >>> qunex parcellate_anat --sessionsfolder='<folder_with_sessions>' \\
                  --session='<case_id>' \\
                  --inputdatatype='MyelinMap_BC' \\
                  --parcellationfile='<dlabel_file_for_parcellation>' \\
                  --overwrite='no' \\
                  --extractdata='yes' \\
                  --outname='<name_of_output_pconn_file>'
    """


def parcellate_bold():
    """
    ``parcellate_bold``

    This function implements parcellation on the BOLD dense files using a
    whole-brain parcellation (e.g. Glasser parcellation with subcortical labels
    included).

    Parameters:
        --sessionsfolder (str):
            Path to study folder that contains sessions.
        --sessions (str):
            Comma separated list of sessions to run.
        --inputfile (str):
            Specify the name of the file you want to use for parcellation (e.g.
            'bold1_Atlas_MSMAll_hp2000_clean').
        --inputpath (str):
            Specify path of the file you want to use for parcellation relative to
            the master study folder and session directory (e.g.
            '/images/functional/').
        --inputdatatype (str):
            Specify the type of data for the input file (e.g. 'dscalar' or
            'dtseries').
        --parcellationfile (str):
           Specify the absolute path of the file you want to use for parcellation
           (e.g. '/gpfs/project/fas/n3/Studies/Connectome/Parcellations/glasser_parcellation/LR_Colelab_partitions_v1d_islands_withsubcortex.dlabel.nii').
        --singleinputfile (str):
           Parcellate only a single file in any location. Individual flags are not
           needed (--session, --sessionsfolder, --inputfile).
        --overwrite (str):
            Delete prior run ('yes' / 'no').
        --computepconn (str, default 'no'):
            Specify if a parcellated connectivity file should be computed (pconn).
            This is done using covariance and correlation ('yes' / 'no').
        --outname (str):
            Specify the suffix output name of the pconn file.
        --outpath (str):
            Specify the output path name of the pconn file relative to the master
            study folder (e.g. '/images/functional/').
        --useweights (str, default 'no'):
            If computing a parcellated connectivity file you can specify which
            frames to omit (e.g. 'yes' or 'no').
        --weightsfile (str):
            Specify the location of the weights file relative to the master study
            folder (e.g. '/images/functional/movement/bold1.use').
        --extractdata (str):
            Specify if you want to save out the matrix as a CSV file.

    Examples:
        Run directly via:

        >>> ${TOOLS}/${QUNEXREPO}/bash/qx_utilities/parcellate_bold.sh \\
            --<parameter1> --<parameter2> --<parameter3> ... --<parameterN>

        NOTE: --scheduler is not available via direct script call.

        Run via:

        >>> qunex parcellate_bold --<parameter1> --<parameter2> ... --<parameterN>

        NOTE: scheduler is available via qunex call.

        --scheduler
            A string for the cluster scheduler (e.g. LSF, PBS or SLURM) followed by
            relevant options.

        For SLURM scheduler the string would look like this via the qunex call::

            --scheduler='SLURM,jobname=<name_of_job>,time=<job_duration>,ntasks=<number_of_tasks>,cpus-per-task=<cpu_number>,mem-per-cpu=<memory>,partition=<queue_to_send_job_to>'

        >>> parcellate_bold.sh --sessionsfolder='<folder_with_sessions>' \\
                               --session='<session_id>' \\
                               --inputfile='<name_of_input_file' \\
                               --inputpath='<path_for_input_file>' \\
                               --inputdatatype='<type_of_dense_data_for_input_file>' \\
                               --parcellationfile='<dlabel_file_for_parcellation>' \\
                               --overwrite='no' \\
                               --extractdata='yes' \\
                               --outname='<name_of_output_pconn_file>' \\
                               --outpath='<path_for_output_file>'
    """


def run_qc():
    """
    ``run_qc``

    This function runs the QC preprocessing for a specified modality / processing
    step.

    Currently Supported: ${SupportedQC}

    This function is compatible with both legacy data [without T2w scans] and
    HCP-compliant data [with T2w scans and DWI].

    With the exception of rawNII, the function generates 3 types of outputs, which
    are stored within the Study in <path_to_folder_with_sessions>/QC :

    - .scene files that contain all relevant data loadable into Connectome Workbench
    - .png images that contain the output of the referenced scene file.
    - .zip file that contains all relevant files to download and re-generate the
      scene in Connectome Workbench.

    Note: For BOLD data there is also an SNR txt output if specified.

    Note: For raw NIFTI QC outputs are generated in:
    <sessions_folder>/<case>/nii/slicesdir

    Parameters:
        --sessionsfolder (str):
            Path to study folder that contains sessions.
        --sessions (str):
            Comma separated list of sessions to run.
        --modality (str):
            Specify the modality to perform QC on.
            Supported: 'rawNII', 'T1w', 'T2w', 'myelin', 'BOLD', 'DWI', 'general',
            'eddyQC'.

            Note: If selecting 'rawNII' this function performs QC for raw NIFTI
            images in <sessions_folder>/<case>/nii It requires NIFTI images in
            <sessions_folder>/<case>/nii/ after either BIDS import of DICOM
            organization.

            Session-specific output: <sessions_folder>/<case>/nii/slicesdir

            Uses FSL's 'slicesdir' script to generate PNGs and an HTML file in the
            above directory.

            Note: If using 'general' modality, then visualization is
            $TOOLS/$QUNEXREPO/qx_library/data/scenes/qc/template_general_qc.wb.scene

            This will work on any input file within the
            session-specific data hierarchy.
        --datapath (str):
            Required ==> Specify path for input path relative to the
            <sessions_folder> if scene is 'general'.
        --datafile (str):
            Required ==> Specify input data file name if scene is 'general'.
        --batchfile (str):
            Absolute path to local batch file with pre-configured processing
            parameters.

            Note: It can be used in combination with --sessions to select only
            specific cases to work on from the batch file. If --sessions is
            omitted, then all cases from the batch file are processed. It can also
            used in combination with --bolddata to select only specific BOLD runs
            to work on from the batch file. If --bolddata is omitted (see below),
            all BOLD runs in the batch file will be processed.
        --overwrite (str, default 'no'):
            Delete prior QC run: yes/no.
        --hcp_suffix (str, default ''):
            Allows user to specify session id suffix if running HCP preprocessing
            variants. E.g. ~/hcp/sub001 & ~/hcp/sub001-run2 ==> Here 'run2' would be
            specified as --hcp_suffix='-run2'
        --scenetemplatefolder (str, default '${TOOLS}/${QUNEXREPO}/qx_library/data/scenes/qc'):
            Specify the absolute path name of the template folder.

            Note: relevant scene template data has to be in the same folder as the
            template scenes.
        --outpath (str, default '<path_to_study_sessions_folder>/QC/<input_modality_for_qc>'):
            Specify the absolute path name of the QC folder you wish the individual
            images and scenes saved to. If --outpath is unspecified then files are
            saved to: '<path_to_study_sessions_folder>/QC/<input_modality_for_qc>'.
        --scenezip (str, default 'yes'):
            Yes or no. Generates a ZIP file with the scene and all relevant files
            for Connectome Workbench visualization.
            Note: If scene zip set to yes, then relevant scene files will be zipped
            with an updated relative base folder.
            All paths will be relative to this base -->
            <path_to_study_sessions_folder>/<session_id>/hcp/<session_id>
            The scene zip file will be saved to:
            <path_for_output_file>/<session_id>.<input_modality_for_qc>.QC.wb.zip
        --userscenefile (str, default ''):
            User-specified scene file name. --modality info is still required to
            ensure correct run. Relevant data needs to be provided.
        --userscenepath (str, default ''):
            Path for user-specified scene and relevant data in the same location.
            --modality info is still required to ensure correct run.
        --timestamp ():
            Allows user to specify unique time stamp or to parse a time stamp from
            QuNex bash wrapper.
        --suffix (str, default '<session_id>_<timestamp>'):
            Allows user to specify unique suffix or to parse a time stamp from QuNex
            bash wrapper.

    Specific parameters:
        --dwipath (str):
            Specify the input path for the DWI data (may differ across studies; e.g.
            'Diffusion' or 'Diffusion' or 'Diffusion_DWI_dir74_AP_b1000b2500').
        --dwidata (str):
            Specify the file name for DWI data (may differ across studies; e.g.
            'data' or 'DWI_dir74_AP_b1000b2500_data').
        --dtifitqc (str):
            Specify if dtifit visual QC should be completed (e.g. 'yes' or 'no').
        --bedpostxqc (str):
            Specify if BedpostX visual QC should be completed (e.g. 'yes' or 'no').
        --eddyqcstats (str):
            Specify if EDDY QC stats should be linked into QC folder and motion
            report generated (e.g. 'yes' or 'no').
        --dwilegacy (str):
            Specify if DWI data was processed via legacy pipelines (e.g. 'yes' or
            'no').
        --boldprefix (str):
            Specify the prefix file name for BOLD dtseries data (may differ across
            studies depending on processing; e.g. 'BOLD' or 'TASK' or 'REST').
            Note: If unspecified then QC script will assume that folder names
            containing processed BOLDs are named numerically only (e.g. 1, 2, 3).
        --boldsuffix (str):
            Specify the suffix file name for BOLD dtseries data (may differ across
            studies depending on processing; e.g. 'Atlas' or 'MSMAll').
        --skipframes (str):
            Specify the number of initial frames you wish to exclude from the BOLD
            QC calculation.
        --snronly (str, default 'no'):
            Specify if you wish to compute only SNR BOLD QC calculation and skip
            image generation ('yes'/'no').
        --bolddata (str):
            Specify BOLD data numbers separated by comma or pipe. E.g.
            --bolddata='1,2,3,4,5'. This flag is interchangeable with --bolds or
            --boldruns to allow more redundancy in specification.

            Note: If --bolddata is unspecified, a batch file must be provided in
            --batchfile or an error will be reported. If --bolddata is empty and
            --batchfile is provided, by default QuNex will use the information in
            the batch file to identify all BOLDS to process.
        --boldfc (str, default ''):
            Specify if you wish to compute BOLD QC for FC-type BOLD results.
            Supported: pscalar or pconn.
            Requires --boldfc='<pconn or pscalar>', --boldfcinput=<image_input>,
            --bolddata or --boldruns or --bolds.
        --boldfcpath (str, default '<study_folder>/sessions/<session_id>/images/functional'):
            Specify path for input FC data.
            Requires --boldfc='<pconn or pscalar>', --boldfcinput=<image_input>,
            --bolddata or --boldruns or --bolds.
        --boldfcinput ():
            Required. If no --boldfcpath is provided then specify only data input
            name after bold<Number>_ which is searched for in
            '<sessions_folder>/<session_id>/images/functional'.

            pscalar FC
               Atlas_hpss_res-mVWMWB_lpss_CAB-NP-718_r_Fz_GBC.pscalar.nii
            pconn FC
               Atlas_hpss_res-mVWMWB_lpss_CAB-NP-718_r_Fz.pconn.nii

            Requires --boldfc='<pconn or pscalar>', --boldfcinput=<image_input>,
            --bolddata or --boldruns or --bolds.
        --processcustom (str, default 'no'):
            Either 'yes' or 'no'. If set to 'yes' then the script looks into:
            ~/<study_path>/processing/scenes/QC/ for additional custom QC scenes.

            Note: The provided scene has to conform to QuNex QC template
            standards.xw

            See $TOOLS/$QUNEXREPO/qx_library/data/scenes/qc/ for example templates.
            The qc path has to contain relevant files for the provided scene.
        --omitdefaults (str, default 'no'):
            Either 'yes' or 'no'. If set to 'yes' then the script omits defaults.

    Examples:
        Run directly via:

        >>> ${TOOLS}/${QUNEXREPO}/bash/qx_utilities/run_qc.sh \\
            --<parameter1> --<parameter2> --<parameter3> ... --<parameterN>

        NOTE: --scheduler is not available via direct script call.

        Run via:

        >>> qunex run_qc --<parameter1> --<parameter2> ... --<parameterN>

        NOTE: scheduler is available via qunex call.

        --scheduler
            A string for the cluster scheduler (e.g. LSF, PBS or SLURM) followed by
            relevant options.

        For SLURM scheduler the string would look like this via the qunex call::

            --scheduler='SLURM,jobname=<name_of_job>,time=<job_duration>,ntasks=<number_of_tasks>,cpus-per-task=<cpu_number>,mem-per-cpu=<memory>,partition=<queue_to_send_job_to>'

        raw NII QC:

        >>> qunex run_qc \\
            --sessionsfolder='<path_to_study_sessions_folder>' \\
            --sessions='<comma_separated_list_of_cases>' \\
            --modality='rawNII'

        T1w QC:

        >>> qunex run_qc \\
            --sessionsfolder='<path_to_study_sessions_folder>' \\
            --sessions='<comma_separated_list_of_cases>' \\
            --outpath='<path_for_output_file> \\
            --scenetemplatefolder='<path_for_the_template_folder>' \\
            --modality='T1w' \\
            --overwrite='yes'

        T2w QC:

        >>> qunex run_qc \\
            --sessionsfolder='<path_to_study_sessions_folder>' \\
            --sessions='<comma_separated_list_of_cases>' \\
            --outpath='<path_for_output_file> \\
            --scenetemplatefolder='<path_for_the_template_folder>' \\
            --modality='T2w' \\
            --overwrite='yes'

        Myelin QC:

        >>> qunex run_qc \\
            --sessionsfolder='<path_to_study_sessions_folder>' \\
            --sessions='<comma_separated_list_of_cases>' \\
            --outpath='<path_for_output_file> \\
            --scenetemplatefolder='<path_for_the_template_folder>' \\
            --modality='myelin' \\
            --overwrite='yes'

        DWI QC:

        >>> qunex run_qc \\
            --sessionsfolder='<path_to_study_sessions_folder>' \\
            --sessions='<comma_separated_list_of_cases>' \\
            --scenetemplatefolder='<path_for_the_template_folder>' \\
            --modality='DWI' \\
            --outpath='<path_for_output_file> \\
            --dwilegacy='yes' \\
            --dwidata='<file_name_for_dwi_data>' \\
            --dwipath='<path_for_dwi_data>' \\
            --overwrite='yes'

        BOLD QC (for a specific BOLD run):

        >>> qunex run_qc \\
            --sessionsfolder='<path_to_study_sessions_folder>' \\
            --sessions='<comma_separated_list_of_cases>' \\
            --outpath='<path_for_output_file> \\
            --scenetemplatefolder='<path_for_the_template_folder>' \\
            --modality='BOLD' \\
            --bolddata='1' \\
            --boldsuffix='Atlas' \\
            --overwrite='yes'

        BOLD QC (search for all available BOLD runs):

        >>> qunex run_qc \\
            --sessionsfolder='<path_to_study_sessions_folder>' \\
            --sessions='<comma_separated_list_of_cases>' \\
            --batchfile='<path_to_batch_file>' \\
            --outpath='<path_for_output_file> \\
            --scenetemplatefolder='<path_for_the_template_folder>' \\
            --modality='BOLD' \\
            --boldsuffix='Atlas' \\
            --overwrite='yes'

        BOLD FC QC [pscalar or pconn]:

        >>> qunex run_qc \\
            --overwritestep='yes' \\
            --sessionsfolder='<path_to_study_sessions_folder>' \\
            --sessions='<comma_separated_list_of_cases>' \\
            --modality='BOLD' \\
            --boldfc='<pscalar_or_pconn>' \\
            --boldfcinput='<data_input_for_bold_fc>' \\
            --bolddata='1' \\
            --overwrite='yes'
    """


def run_turnkey():
    """
    ``run_turnkey``

    This function implements QuNex Suite workflows as a turnkey function.
    It operates on a local server or cluster or within the XNAT Docker engine.

    Parameters:
        --turnkeytype (str, default 'xnat'):
            Specify type turnkey run. Options are: 'local' or 'xnat'.
        --path (str, default '/output/xnatprojectid'):
            Path where study folder is located. If empty default is for XNAT run.
        --sessions (str):
            Sessions to run locally on the file system if not an XNAT run.
        --sessionids (str):
            Comma separated list of session IDs to select for a run via gMRI engine
            from the batch file.
        --turnkeysteps (str):
            Specify specific turnkey steps you wish to run:
            Supported: TODO
        --turnkeycleanstep (str):
            Specify specific turnkey steps you wish to clean up intermediate files
            for.
            Supported: TODO
        --batchfile (str):
            Batch file with pre-configured header specifying processing parameters.

            Note: This file needs to be created *manually* prior to starting
            runTurnkey.

            - IF executing a 'local' run then provide the absolute path to the file
              on the local file system:
              If no file name is given then by default QuNex RunTurnkey will exit
              with an error.
            - IF executing a run via the XNAT WebUI then provide the name of the
              file. This file should be created and uploaded manually as the
              project-level resource on XNAT.

        --mappingfile (str):
            File for mapping NIFTI files into the desired QuNex file structure (e.g.
            'hcp', 'fMRIPrep' etc.)

            Note: This file needs to be created *manually* prior to starting
            runTurnkey.

            - IF executing a 'local' run then provide the absolute path to the file
              on the local file system:
              If no file name is given then by default QuNex RunTurnkey will exit
              with an error.
            - IF executing a run via the XNAT WebUI then provide the name of the
              file. This file should be created and uploaded manually as the
              project-level resource on XNAT.

    Specific parameters:
        --acceptancetest (str, default 'no'):
            Specify if you wish to run a final acceptance test after each unit of
            processing.

            If --acceptancetest='yes', then --turnkeysteps must be provided and will
            be executed first.

            If --acceptancetest='<turnkey_step>', then acceptance test will be run
            but step won't be executed.
        --xnathost (str):
            Specify the XNAT site hostname URL to push data to.
        --xnatprojectid (str):
            Specify the XNAT site project id. This is the Project ID in XNAT and not
            the Project Title.
        --xnatuser (str):
            Specify XNAT username.
        --xnatpass (str):
            Specify XNAT password.
        --xnatsubjectid (str):
            ID for subject across the entire XNAT database.
            Required or --xnatsubjectlabel needs to be set.
        --xnatsubjectlabel (str):
            Label for subject within a project for the XNAT database.
            Required or --xnatsubjectid needs to be set.
        --xnataccsessionid (str):
            ID for subject-specific session within the XNAT project.
            Derived from XNAT but can be set manually.
        --xnatsessionlabel (str):
            Label for session within XNAT project.
            Note: may be general across multiple subjects (e.g. rest). Required.
        --xnatstudyinputpath (str, default 'input/RESOURCES/qunex_study'):
            The path to the previously generated session data as mounted for the
            container.
        --dataformat (str, default 'DICOM'):
            Specify the format in which the data is. Acceptable values are:

            - 'DICOM' ... datasets with images in DICOM format
            - 'BIDS'  ... BIDS compliant datasets
            - 'HCPLS' ... HCP Life Span datasets
            - 'HCPYA' ... HCP Young Adults (1200) dataset.

        --hcp_filename (str):
            Specify how files and folders should be named using HCP processing:

            - 'automated'   ... files should be named using QuNex automated naming
              (e.g. BOLD_1_PA)
            - 'userdefined' ... files should be named using user defined names (e.g.
              rfMRI_REST1_AP)
            - 'standard'    ... default

            Note that the filename to be used has to be provided in the
            session_hcp.txt file or the standard naming will be used. If not
            provided the default 'standard' will be used.
        --bidsformat (str, default 'no'):
            Note: this parameter is deprecated and is kept for backward
            compatibility.

            If set to 'yes', it will set --dataformat to BIDS. If left undefined or
            set to 'no', the --dataformat value will be used. The specification of
            the parameter follows ...

            Specify if input data is in BIDS format (yes/no). Default is [no]. If
            set to yes, it overwrites the --dataformat parameter.

            Note:

            - If --bidsformat='yes' and XNAT run is requested then
              --xnatsessionlabel is required.
            - If --bidsformat='yes' and XNAT run is NOT requested
              then BIDS data expected in <sessions_folder/inbox/BIDS.

        --bidsname (str, default detailed below):
            The name of the BIDS dataset. The dataset level information that does
            not pertain to a specific session will be stored in
            <projectname>/info/bids/<bidsname>. If bidsname is not provided, it
            will be deduced from the name of the folder in which the BIDS database
            is stored or from the zip package name.
        --rawdatainput (str, default ''):
            If --turnkeytype is not XNAT then specify location of raw data on the
            file system for a session. Default is '' for the XNAT type run as host
            is used to pull data.
        --workingdir (str, default '/output'):
            Specify where the study folder is to be created or resides.
        --projectname (str):
            Specify name of the project on local file system if XNAT is not
            specified.
        --overwritestep (str, default 'no'):
            Specify 'yes' or 'no' for delete of prior workflow step.
        --overwritesession (str, default 'no'):
            Specify 'yes' or 'no' for delete of prior session run.
        --overwriteproject (str, default 'no'):
            Specify 'yes' or 'no' for delete of entire project prior to run.
        --overwriteprojectxnat (str, default 'no'):
            Specify 'yes' or 'no' for delete of entire XNAT project folder prior to
            run.
        --cleanupsession (str, default 'no'):
            Specify 'yes' or 'no' for cleanup of session folder after steps are
            done.
        --cleanupproject (str, default 'no'):
            Specify 'yes' or 'no' for cleanup of entire project after steps are
            done.
        --cleanupoldfiles (str, default 'no'):
            Specify <yes> or <no> for cleanup of files that are older than start of
            run (XNAT run only).
        --bolds (str, default 'all'):
            For commands that work with BOLD images this flag specifies which
            specific BOLD images to process. The list of BOLDS has to be specified
            as a comma or pipe '|' separated string of bold numbers or bold tags as
            they are specified in the session_hcp.txt or batch.txt file.

            Example: '--bolds=1,2,rest' would process BOLD run 1, BOLD run 2 and any
            other BOLD image that is tagged with the string 'rest'.

            If the parameter is not specified, the default value 'all' will be used.
            In this scenario every BOLD image that is specified in the group
            batch.txt file for that session will be processed.

            **Note**: This parameter takes precedence over the 'bolds' parameter in
            the batch.txt file. Therefore when RunTurnkey is executed and this
            parameter is ommitted the '_bolds' specification in the batch.txt file
            never takes effect, because the default value 'all' will take
            precedence.
        --customqc (str, default 'no'):
            Either 'yes' or 'no'. If set to 'yes' then the script ooks into:
            ~/<study_path>/processing/scenes/QC/ for additional custom QC scenes.

            Note: The provided scene has to conform to QuNex QC template
            standards.xw

            See /opt/qunex/qx_library/data/scenes/qc/ for example templates.

            The qc path has to contain relevant files for the provided scene.
        --qcplotimages (str):
            Absolute path to images for general_plot_bold_timeseries. See
            'qunex general_plot_bold_timeseries' for help.

            Only set if general_plot_bold_timeseries is requested then this is a
            required setting.
        --qcplotmasks (str)
            Absolute path to one or multiple masks to use for extracting BOLD data.
            See 'qunex general_plot_bold_timeseries' for help.

            Only set if general_plot_bold_timeseries is requested then this is a
            required setting.
        --qcplotelements (str):
            Plot element specifications for general_plot_bold_timeseries. See
            'qunex general_plot_bold_timeseries' for help.

            Only set if general_plot_bold_timeseries is requested. If not set then
            the default is: TODO

    Notes:
        List of Turnkey Steps:
            Most turnkey steps have exact matching qunex commands with several
            exceptions that fall into two categories:

            * `map_raw_data`  step is only relevant to `run_turnkey`, which maps
              files on a local filesystem or in XNAT to the study folder.
            * `run_qc*` and `compute_bold_fc*`  are two groups of turnkey steps that
              have qunex commands as their prefixes. The suffixes of these commands
              are options of the corresponding qunex command.

            A complete list of turnkey commands:

            * create_study
            * map_raw_data
            * import_dicom
            * run_qc_rawnii
            * create_session_info
            * setup_hcp
            * create_batch
            * export_hcp
            * hcp_pre_freesurfer
            * hcp_freesurfer
            * hcp_post_freesurfer
            * run_qc_t1w
            * run_qc_t2w
            * run_qc_myelin
            * hcp_fmri_volume
            * hcp_fmri_surface
            * run_qc_bold
            * hcp_diffusion
            * run_qc_dwi
            * dwi_legacy
            * run_qc_dwi_legacy
            * dwi_eddy_qc
            * run_qc_dwi_eddy
            * dwi_dtifit
            * run_qc_dwi_dtifit
            * dwi_bedpostx_gpu
            * run_qc_dwi_process
            * run_qc_dwi_bedpostx
            * dwi_probtrackx_dense_gpu
            * dwi_pre_tractography
            * dwi_parcellate
            * dwi_seed_tractography_dense
            * run_qc_custom
            * map_hcp_data
            * create_bold_brain_masks
            * compute_bold_stats
            * create_stats_report
            * extract_nuisance_signal
            * preprocess_bold
            * preprocess_conc
            * general_plot_bold_timeseries
            * parcellate_bold
            * parcellate_bold
            * compute_bold_fc_seed
            * compute_bold_fc_gbc
            * run_qc_bold_fc.

    Examples:
        Run directly via:

         >>> ${TOOLS}/${QUNEXREPO}/bash/qx_utilities/run_turnkey.sh \\
             --<parameter1> --<parameter2> --<parameter3> ... --<parameterN>

        Run via:

        >>> qunex runTurnkey --<parameter1> --<parameter2> ... --<parameterN>

        --scheduler
            A string for the cluster scheduler (e.g. LSF, PBS or SLURM) followed
            by relevant options.

        For SLURM scheduler the string would look like this via the qunex call::

            --scheduler='SLURM,jobname=<name_of_job>,time=<job_duration>,ntasks=<number_of_tasks>,cpus-per-task=<cpu_number>,mem-per-cpu=<memory>,partition=<queue_to_send_job_to>'

        >>> run_turnkey.sh \\
            --turnkeytype=<turnkey_run_type> \\
            --turnkeysteps=<turnkey_worlflow_steps> \\
            --batchfile=<batch_file> \\
            --overwritestep=yes \\
            --mappingfile=<mapping_file> \\
            --xnatsubjectlabel=<XNAT_SUBJECT_LABEL> \\
            --xnatsessionlabel=<XNAT_SESSION_LABEL> \\
            --xnatprojectid=<name_of_xnat_project_id> \\
            --xnathostname=<XNAT_site_URL> \\
            --xnatuser=<xnat_host_user_name> \\
            --xnatpass=<xnat_host_user_pass>
    """


def pre_tractography():
    """
    ``pre_tractography``

    This function runs the Pretractography Dense trajectory space generation.

    Note that this is a very quick function to run (less than 5min) so no
    overwrite options exist.

    It explicitly assumes the Human Connectome Project folder structure for
    preprocessing and completed diffusion and bedpostX processing.

    DWI data needs to be in the following folder::

        <study_folder>/<session>/hcp/<session>/T1w/Diffusion

    BedpostX output data needs to be in the following folder::

        <study_folder>/<case>/hcp/<case>/T1w/Diffusion.bedpostX

    Parameters:
        --sessionsfolder (str):
            Path to study folder that contains sessions.
        --sessions (str):
            Comma separated list of sessions to run.
        --scheduler (str):
            A string for the cluster scheduler (e.g. LSF, PBS or SLURM) followed by
            relevant options e.g. for SLURM the string would look like this::

                --scheduler='SLURM,jobname=<name_of_job>,time=<job_duration>,ntasks=<numer_of_tasks>,cpus-per-task=<cpu_number>,mem-per-cpu=<memory>,partition=<queue_to_send_job_to>'

    Examples:
        >>> qunex pretractography_dense --sessionsfolder='<path_to_study_sessions_folder>' \\
                  --sessions='<comma_separarated_list_of_cases>' \\
                  --scheduler='<name_of_scheduler_and_options>'

        Direct usage::

            $0 <StudyFolder> <Session> <MSMflag>

        T1w and MNINonLinear folders are expected within
        <StudyFolder>/<Session>.

        MSMflag=0 uses the default surfaces, MSMflag=1 uses the MSM surfaces
        defined in make_trajectory_space_mni.sh.
    """