There are three scripts:
```/gpfs/project/fas/n3/software/mnaptools/mnapcontainer/Examples/MNAPHCPScript.sh
/gpfs/project/fas/n3/software/mnaptools/mnapcontainer/Examples/MNAPSingularityExecute.sh
/gpfs/project/fas/n3/software/mnaptools/mnapcontainer/Examples/MNAPSingularityInitialize.sh```
The three scripts work in lock-step and all the user needs to do is:
• Adjust call in MNAPSingularityExecute.sh
• Provide path for input folder that contains subject folders and batch_parameters.txt file is in the same location.
• Call the following lines from a Singularity-compatible location:
```MNAPScriptPath="/gpfs/project/fas/n3/software/mnaptools/mnapcontainer/Examples"
MNAPScriptPath="/gpfs/project/fas/n3/software/mnaptools/mnapcontainer/Examples"
MNAPContainerPath="/gpfs/project/fas/n3/software/Singularity"
bash ${MNAPScriptPath}/MNAPSingularityInitialize.sh \
--containerpath="${MNAPContainerPath}/mnap_suite-hcp1_test.simg" \
--mnapexecscript="${MNAPScriptPath}/MNAPSingularityExecute.sh"```


# README File for Running the MNAP Singularity via the provided example


Background
==========
---

The provided example is designed to execute a run of the MNAP Singularity container
on HCP-compatible BIDS data. The provided example is implemented using two subjects
from the HCP LifeSpan project:

* HCA1234567
* HCA7654321

Execution 
===============================
---

### Ensure folders with subject data is available on the file system:

```
<path_to_folder>/HCA1234567
<path_to_folder>/HCA7654321
```

### Place the following into a folder on your file system. 

* `MNAPHCPScript.sh` -- Code to run inside the container. 
* `MNAPSingularityExecute.sh` -- Code to execute the MNAP environment correctly. 
* `MNAPSingularityInitialize.sh` -- Code to initialize the MNAP Singularity container image.
* `batch_parameters.txt file` -- File needed for MNAP to execute HCP pipelines. 
* `MNAP Singularity Image` -- Image file for the MNAP singularity container

### Execute the code. 

The three scripts above work in lock-step. To run them the user needs to:

* Adjust call in `MNAPSingularityExecute.sh` as needed for their file system to provide correct paths. 
* Note the example below is configured to run on the Yale Grace cluster with the two subjects.

```
export FSLDIR="/opt/fsl/fsl-5.0.9"
export PATH=${FSLDIR}:${FSLDIR}/bin:${PATH}
TimeStamp=`date +%Y-%m-%d-%H-%M-%S`
ScriptFolder="/gpfs/project/fas/n3/software/mnaptools/mnapcontainer/Examples/"
StudyFolder="/gpfs/project/fas/n3/Studies/HCPLSOutput_$TimeStamp"
InputFolder="/gpfs/project/fas/n3/Studies/HCPLSImport/input"
export PATH=${InputFolder}:${StudyFolder}:${ScriptFolder}:${PATH}

bash ${ScriptFolder}/MNAPHCPScript.sh \
--studyfolder="${StudyFolder}" \
--subjects="HCA1234567,HCA7654321" \
--hcpdatapath="${InputFolder}" \
--parameterfile="${InputFolder}/batch_parameters.txt" \
--fsldir="${FSLDIR}" \
--overwrite="yes"
```

* Call the following lines from a Singularity-compatible node:

```
MNAPScriptPath="/gpfs/project/fas/n3/software/mnaptools/mnapcontainer/Examples"
MNAPScriptPath="/gpfs/project/fas/n3/software/mnaptools/mnapcontainer/Examples"
MNAPContainerPath="/gpfs/project/fas/n3/software/Singularity"
bash ${MNAPScriptPath}/MNAPSingularityInitialize.sh \
--containerpath="${MNAPContainerPath}/mnap_suite-hcp1_test.simg" \
--mnapexecscript="${MNAPScriptPath}/MNAPSingularityExecute.sh"
```


[Mind and Brain Lab]: http://mblab.si
[Anticevic Lab]: http://anticeviclab.yale.edu
