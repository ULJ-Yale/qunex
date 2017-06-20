#!/usr/bin/env Rscript

# load RCurl to integrate with API
library(RCurl)

#### Export RedCap Data ############################################################################################################
# --> use RedCap API to download records and metadata (saved in DataDrop)
####################################################################################################################################
outpath <- "/gpfs/project/fas/n3/Studies/DataDrop/RedCapExport/"
#outpath <- "~/Desktop/redcap_api_test/RedCapExport/"

# user-specific API token must be initially created through RedCap website (https://poa-redcap.med.yale.edu/redcap_v6.17.2/) 
userToken <- as.vector(read.table('~/.redcapAPI/APItoken')[1,1])

# set output filenames 
fileRecord <- paste(outpath, 'RedCapExport_record.csv', sep="")
fileMetadata <- paste(outpath, 'RedCapExport_metadata.csv', sep="")
fileEventmap <- paste(outpath, 'RedCapExport_formEventMapping.csv', sep="")
fileOutput <- paste(outpath, 'RedCapExport_OrganizedDatabase.csv', sep="")

# export all records to outpath/RedCapExport via RedCap API
result <- postForm(content='record', uri='https://poa-redcap.med.yale.edu/api/', token=userToken, format='csv', type='flat', rawOrLabel='raw', rawOrLabelHeaders='raw', returnFormat='csv')
write.table(result, file = fileRecord, append = FALSE, quote = FALSE, sep = ",", eol = "\n", na = "NA", dec = ".", row.names = FALSE, col.names = FALSE) 
record <- data.frame(read.csv(fileRecord, stringsAsFactors = FALSE))
record[which(record == "",  arr.ind = TRUE)] <- NA 
# export data dictionary 
result <- postForm( content='metadata', uri='https://poa-redcap.med.yale.edu/api/', token=userToken, format='csv', returnFormat='csv')
write.table(result, file = fileMetadata, append = FALSE, quote = FALSE, sep = ",", eol = "\n", na = "NA", dec = ".", row.names = FALSE, col.names = FALSE) 
metadata <- data.frame(read.csv(fileMetadata, stringsAsFactors = FALSE))
# export form->event mapping table
result <- postForm(content='formEventMapping', uri='https://poa-redcap.med.yale.edu/api/', token=userToken, format='csv', returnFormat='csv' )
write.table(result, file = fileEventmap, append = FALSE, quote = FALSE, sep = ",", eol = "\n", na = "NA", dec = ".", row.names = FALSE, col.names = FALSE)
eventmap <- data.frame(read.csv(fileEventmap, stringsAsFactors = FALSE))


#### Organize RedCap Database ######################################################################################################
# --> populate an organized table for all studies/events (saved in DataDrop) 
#     one row per subject, with columns designated by event, form, and field (as well as a more reader-friendly field label) 
####################################################################################################################################
# list unique events
events <- sort(as.matrix(unique(record["redcap_event_name"])))                 

# list N3 IDs for all subjects 
allSubjects <- sort(as.matrix(unique(record["anticeviclab_id"])))

# initialize dataframe to hold all results
headersize <- 4
dfAll <- data.frame(matrix(NA, ncol=(length(events)*ncol(record)), nrow=(length(allSubjects)) + headersize))

# separate records by event and concatenate horizontally, with one row per subject
for (i in 1:length(events)){
  # find subset of records containing event data
  df <- subset(record, redcap_event_name == events[i])
  
  # list subjects for whom event is empty
  emptySubjects <- data.frame(setdiff(allSubjects,((df[,1]))))
  
  # sort full and empty records into standardized dataframe for all subjects 
  orderedSubjects <- data.frame(matrix(NA, ncol=ncol(record), nrow=length(allSubjects)))
  orderedSubjects[(1:(nrow(df))),] <- as.matrix(df)
  if ( nrow(emptySubjects) > 0){
    orderedSubjects[((nrow(df)+1)):(length(allSubjects)),1] <- as.matrix(emptySubjects) 
  }
  orderedSubjects <- orderedSubjects[order(orderedSubjects[1]),]
  rownames(orderedSubjects) <- orderedSubjects[,1]
  
  # populate dataframe header from data dictionary
  df2 <- data.frame(matrix(NA, ncol=ncol(record), nrow=(length(allSubjects)) + headersize ))
  rownames(df2)[1:headersize] <- c("EVENT", "FORM", "LABEL", "FIELD")
  rownames(df2)[(headersize + 1):(nrow(df2))] <- allSubjects
  df2["EVENT",] <- events[i]
  df2["FIELD",] <- colnames(df)
  df2[((headersize + 1):(nrow(df2))),] <- as.matrix(orderedSubjects)
  
  # match forms to events, flagging unused columns 
  for (k in 1:ncol(df2)){
    field <- df2["FIELD", k]
    event <- df2["EVENT", k]
    # check if field is in data dictonary
    mdIndex <- as.integer(which(metadata[,"field_name"] == field, arr.ind = TRUE))
    # check if form is in event
    emIndex <- as.integer(which(subset(eventmap, unique_event_name == event)[,"form"] == as.vector(metadata[mdIndex,"form_name"]), arr.ind = TRUE))
    if ((length(mdIndex) > 0) && (length(emIndex) > 0)) {
      df2["FORM", k] <- as.vector(metadata[mdIndex,"form_name"])
      df2["LABEL", k] <- as.vector(metadata[mdIndex,"field_label"])
      print(paste("building dataframe... ", event, "  field:", field))
    } else { # flag columns for deletion if field has no match in data dictionary and/or form has no match in event
      df2[, k] <- "99999"
    }
  }
  # add all events to a single dataframe
  eventOffset <- (1 + (i * ncol(df2) - ncol(df2)))
  eventEnd <- (eventOffset + ncol(df2) -1)
  dfAll[(1:nrow(dfAll)), (eventOffset:eventEnd)] <- as.matrix(df2)
}
# remove unused columns from dataframe
dropColumns <- as.vector(which( dfAll[1,] == "99999", arr.ind = TRUE)[,2])
dfFinal <- dfAll
dfFinal[, dropColumns] <- list(NULL)
rownames(dfFinal) <- rownames(df2)
colnames(dfFinal) <- (1:ncol(dfFinal))

# save output to outpath/RedCapExport/
write.csv(dfFinal, file = fileOutput)


#### Database User Functions ######################################################################################################
# --> create function 'pasreDB' to select subset of database columns by event, form, and field (optional)
###################################################################################################################################
parseDB <- function(selectEvent, selectForm, selectField){
  # find columns of organized database corresponding to each criteria
  indEvent <- which(dfFinal["EVENT",] == selectEvent, arr.ind = TRUE)[,2]
  indForm <- which(dfFinal["FORM",] == selectForm, arr.ind = TRUE)[,2]
  indField <- which(dfFinal["FIELD",] == selectField, arr.ind = TRUE)[,2]
  # select subset of database matching all criteria -- if arg3="all" all fields are returned
  if (selectField == "all"){ 
    inds <- intersect(indEvent, indForm)
  } else {
    inds <- intersect(indEvent, indForm)
    inds <- intersect(inds, indField)
  }
  # output results as data frame
  return(data.frame(dfFinal[,inds]))
} 

#### Turn-Key PreProcessing #######################################################################################################
# --> write redcap mri forms to acquisition logs for each study
#     organize data from DataDrop (raw mri, physio, eyetracking, behavior) and begin MNAP preprocessing of images
#     system("<bash command string>") is used to send commands to bash shell from within R (eg. find, rsync, analysisipeline)
#     TODO: read organization params from file (hard-coded for blackthorn below)
###################################################################################################################################
#for (i in 1:length(events)){
for (i in 5){ # working -- only run for blackthorn. params are hard-coded below... 
 
  # is this event set up for turn-key processing (redcap forms and turn-key script params)
  turnkey_ready <- "yes"
  if (turnkey_ready == "yes"){
    ### set params  (TODO: read from param file) ###
    #study_folder          <- "/gpfs/project/fas/n3/Studies/BlackThorn/subjects/" 
    study_folder           <- "/gpfs/project/fas/n3/Studies/BlackThorn/subject_test/" 
    acq_formname           <- "blackthorn_fmri"
    acq_logfile            <-  paste(study_folder, "acquisition.log.", acq_formname, ".csv", sep="")
    scanID_fieldname       <- "wmr_scan_bt"
    subjectID_fieldname    <- "wmr_subject_bt"
    errors_fieldname       <- "wmr_errors_bt"
    physio_fieldname       <- "wmr_physio_bt"
    physio_search_path     <- "/gpfs/project/fas/n3/Studies/DataDrop/BoxSync_backup/BlackThorn-physio/" 
    eyelink_fieldname      <- "wmr_eyetrack_bt" 
    eyelink_search_path    <- "/gpfs/project/fas/n3/Studies/DataDrop/BoxSync_backup/BlackThorn-fMRI/"
    behavior_search_path   <- "/gpfs/project/fas/n3/Studies/DataDrop/BoxSync_backup/BlackThorn-fMRI/"
    task_version_fieldname <- "wmr_tasks_bt"
    ap_script              <- "/gpfs/project/fas/n3/software/MNAP/general/AnalysisPipeline.sh "
    
    # create acquisiton log for all scanned subjects 
    acq_log <- data.frame(parseDB(events[i], acq_formname, "all"))
    # select only rows with in which a scanID is recorded
    includeRows <- as.vector(which(!is.na(parseDB(events[i], acq_formname, scanID_fieldname))[,1], arr.ind = TRUE))
    acq_log <- acq_log[includeRows,]
    colnames(acq_log) <- (1:ncol(acq_log))  
    # save acquisition log in study_folder 
    write.csv(acq_log, file = acq_logfile)
    
    # organize and process each subject
    for ( n in includeRows){
      if (n > headersize){ 
        ## set subject-specific params
        scanID  <- gsub(" ", "", (as.vector(parseDB(events[i], acq_formname, scanID_fieldname)[n,])))
        subjectID <- gsub(" ", "", (as.vector(parseDB(events[i], acq_formname, subjectID_fieldname)[n,])))
        IDn <-  gsub("[^0-9]", "", subjectID)   
        datadrop_images <- paste("/gpfs/project/fas/n3/Studies/DataDrop/MRRC_transfers/", scanID, "/prismab*/", sep="") 
        subject_dir <-  paste(study_folder, "/", scanID, "/", sep="")
        inbox_dir <- paste(subject_dir, "inbox/", sep="")
        nii_dir <- paste(subject_dir, "nii/", sep="")
        hcp_dir <- paste(subject_dir, "hcp/", sep="")
        dicom_dir <- paste(subject_dir, "dicom/", sep="")
        dicom_report <- paste(dicom_dir, "DICOM-Report.txt", sep="")
        beh_dir <- paste(subject_dir, "behavior/", sep="")
        eyelink_dir <- paste(subject_dir, "eyetracking/", sep="")
        physio_dir <- paste(subject_dir, "physio/", sep="")
        hcp_file <- paste(subject_dir, "subject_hcp.txt", sep="")
        errors_yn <- gsub(" ", "", (as.vector(parseDB(events[i], acq_formname, errors_fieldname)[n,])))
        task_version <- gsub(" ", "", (as.vector(parseDB(events[i], acq_formname, task_version_fieldname)[n,])))
        physio_yn <- gsub(" ", "", (as.vector(parseDB(events[i], acq_formname, physio_fieldname)[n,])))
        eyelink_yn <- gsub(" ", "", (as.vector(parseDB(events[i], acq_formname, eyelink_fieldname)[n,])))
        
        # TODO: find a way to read generic search string from param file
        physio_search_string <- paste("BT-", IDn, ".*", sep="")
        eyelink_search_string <- paste(IDn, "eyelinkData", sep="")
        behavior_search_string <- paste("*-BT_*", IDn, "*.*", sep="")
        
        # check variables
        check <- c(scanID, subjectID, IDn, errors_yn, task_version, study_folder)
        if (sum(is.na(check)) > 0){ # skip subject if missing variables
          print("ERROR: missing variable")
          next   
        }
        
        # sync DICOMS from DataDrop and run dicomsort if not complete
        if ((!file.exists(dicom_report)) || (file.info(dicom_report)["size"] == 0)){ 
          if (!file.exists(dicom_dir)){ # rsync dicoms to inbox if dicomsort has not been started
            system(paste(
              "mkdir -p ", inbox_dir, sep=" "))
            system(paste( 
              "rsync -aWH --progress ", datadrop_images, " ", inbox_dir, sep=""))        
          }
          # run AP dicomsort
          system(paste(ap_script," ", 
                            "--function='dicomsort' ", 
                            "--path='", study_folder, "' ", 
                            "--subjects='", scanID, "' ", 
                            "--runmethod='1' ", 
                            sep=""))
        }
        
        # create subject_hcp.txt files from template for cases w/out errors
        if ((errors_yn == 0) && (!file.exists(hcp_file))){
          template_file <- paste(study_folder, "/inbox/examples/", task_version, "_task.txt", sep="")
          template <- read.table(template_file)
          # populate header info for hcp_filefile
          hcp_fields <- c("id:", "subject:", "dicom:", "raw_data:", "hcp:")
          hcp_info <- c(scanID, scanID, dicom_dir, nii_dir, hcp_dir)
          # build subject file from template
          subject_hcp_out <- data.frame(matrix(NA, ncol=2, nrow=(nrow(template) + length(hcp_fields))))
          subject_hcp_out[1:length(hcp_fields),1] <- hcp_fields[1:length(hcp_fields)]
          subject_hcp_out[1:length(hcp_fields),2] <- hcp_info[1:length(hcp_fields)]
          subject_hcp_out[(length(hcp_fields) + 1):nrow(subject_hcp_out),1:2] <- as.matrix(template[1:nrow(template),1:2])
          # write subject_hcp.txt to study_folder
          write.table(subject_hcp_out, file = hcp_file, append = FALSE, quote = FALSE, sep = " ", eol = "\n", na = " ", dec = ".", row.names = FALSE, col.names = FALSE)
          # run AP setuphcp
          system(paste(ap_script," ", 
                       "--function='setuphcp' ", 
                       "--path='", study_folder, "' ", 
                       "--subjects='", scanID, "' ", 
                       "--runmethod='1' ",
                       sep=""))
        }
        
        # create behavior data directory 
        system(paste(
          "mkdir ", beh_dir, sep=" "))

       # find and rsync files from behavior_search_path matching behavior_search_string
       system(paste(
         "find ", behavior_search_path, "/ ",
         "-maxdepth 2 ","-type f ",
         "-name ", "'", behavior_search_string, "' ",
         "-exec rsync -aWH {} ", beh_dir," \\;",
         sep=""))
        
        # sync physio data from if collected 
        if (physio_yn == 1) { 
          # create physio data directory 
          system(paste(
            "mkdir ", physio_dir, sep=" "))
          # find and rsync files from physio_search_path matching physio_search_string
          system(paste(
            "find ", physio_search_path, "/ ",
            "-maxdepth 1 ","-type f ",
            "-name ", "'", physio_search_string, "' ",
            "-exec rsync -aWH {} ", physio_dir, " \\;",
            sep=""))
        }
        
        # sync eyelink data if collected
        if (eyelink_yn == 1) {  
          # create eyetracking data directory
          system(paste(
            "mkdir ", eyelink_dir, sep=" "))
          # find and rsync files from eyelink_search_path matching eyelink_search_string
          system(paste(
            "find ", eyelink_search_path, "/ ",
            "-maxdepth 3 ","-type d ",
            "-name ", "'", eyelink_search_string, "' ",
            "-exec rsync -aWH  --exclude='*bmp' {} ", eyelink_dir, " \\;",
            sep=""))
        }
      }
    }
  }
} 
  

  

