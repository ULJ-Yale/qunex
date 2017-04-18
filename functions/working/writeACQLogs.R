
#### Aqcuisition Logs #############################################################################################################
# --> write redcap mri forms to acquisition logs for each study
###################################################################################################################################

# set params
study_folder           <- "/gpfs/project/fas/n3/Studies/BlackThorn/subjects/" 
event                  <- "4_blackthorn_arm_1"  
acq_formname           <- "blackthorn_fmri"
acq_logfile            <-  paste(study_folder, "acquisition.log.", acq_formname, ".csv", sep="")
scanID_fieldname       <- "wmr_scan_bt"

# parseDB function
parseDB <- function(selectEvent, selectForm, selectField){
  # read RedCapExport_OrganizedDatabase.csv
  input <- "/gpfs/project/fas/n3/Studies/DataDrop/RedCapExport/RedCapExport_OrganizedDatabase.csv"
  #input <- "~/Desktop/redcap_api_test/RedCapExport/RedCapExport_OrganizedDatabase.csv"
  DB <- data.frame(read.csv(input, stringsAsFactors = FALSE))
  # find columns of organized database corresponding to each criteria
  indEvent <- which(DB[1,] == selectEvent, arr.ind = TRUE)[,2]
  indForm <- which(DB[2,] == selectForm, arr.ind = TRUE)[,2]
  indField <- which(DB[4,] == selectField, arr.ind = TRUE)[,2]
  # select subset of database matching all criteria -- if arg3="all" all fields are returned
  if (selectField == "all"){ 
    inds <- intersect(indEvent, indForm)
  } else {
    inds <- intersect(indEvent, indForm)
    inds <- intersect(inds, indField)
  }
  # output results as data frame
  return(data.frame(DB[,inds]))
} 

# create acquisiton log for all scanned subjects 
acq_log <- data.frame(parseDB(event, acq_formname, "all"))
# select only rows with in which a scanID is recorded
includeRows <- as.vector(which(!is.na(parseDB(event, acq_formname, scanID_fieldname))[,1], arr.ind = TRUE))
acq_log <- acq_log[includeRows,]
colnames(acq_log) <- (1:ncol(acq_log))  
# save acquisition log in study_folder 
write.table(acq_log, file = acq_logfile, sep=",", col.names=FALSE, row.names = FALSE)


