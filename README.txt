# README File for Processing Pipelines

Background
==========
This is a general purpose analytic pipeline that handles flexible directory inputs and subject lists. The objective is to streamline functions pre and post HCP pipelines and dofcMRI code. The pipeline supports data organization, QA, building lists, various wb_command tools, etc. The pipeline is flexible and can be updated by adding functions developed around other tools. 

Descriptions of functions
=====================
List of functions can be obtained by running the following command from the terminal: 

AnalysisPipeline help

Example Usage
=============

The function takes a sequential list of 3 parameters: 

AnalysisPipeline function_name study_folder 'list of cases'

1. Function name needs to be entered without quotations or brackets 
2. Point to relevant 'subjects' folder absolute path (e.g. /Volumes/syn1/Studies/Connectome/subjects)
3. List of cases in single or double quotes

	Example: AnalysisPipeline dicomsort /Volumes/syn1/Studies/Connectome/subjects '100307 100408'

Different functions will generate command line prompts to allow flexible input by the user. 

Note: the functions expect the data to be organized as for the Human Connectome Project. 

References
==========

Glasser MF, Sotiropoulos SN, Wilson JA, Coalson TS, Fischl B, Andersson JL, Xu J, Jbabdi S, Webster M, Polimeni JR, Van Essen DC, Jenkinson M; WU-Minn HCP Consortium. The minimal preprocessing pipelines for the Human Connectome Project. Neuroimage. 2013 Oct 15;80:105-24. doi: 10.1016/j.neuroimage.2013.04.127. Epub 2013 May 11. PubMed PMID: 23668970; PubMed Central PMCID: PMC3720813.

