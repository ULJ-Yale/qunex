
# set params
studyFolder     <- "/gpfs/project/fas/n3/Studies/BlackThorn/subjects/" 
event           <- "4_blackthorn_arm_1"  
acqForm         <- "blackthorn_fmri"
scanField       <- "wmr_scan_bt"
acqLogFile      <-  paste(studyFolder, "acquisition.log.", acqForm, ".csv", sep="")


#### Aqcuisition Logs #############################################################################################################
# --> write redcap mri forms to acquisition logs for each study
###################################################################################################################################

# function to parse Organized Database by Event, Form and Field
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
acqLog <- data.frame(parseDB(event, acqForm, "all"))
# select only rows with in which a scanID is recorded
includeRows <- as.vector(which(!is.na(parseDB(event, acqForm, scanField))[,1], arr.ind = TRUE))
acqLog <- acqLog[includeRows,]
colnames(acqLog) <- (1:ncol(acqLog))  

# remove line breaks and commas within each cell (otherwise turnkey.sh will fail)
for (i in 1:nrow(acqLog)){
  for (j in 1:ncol(acqLog)){
    acqLog[i,j] <- as.vector(gsub("[','\r\n]", ". ", acqLog[i,j]))
  }
}

# save acquisition log in studyFolder 
write.table(acqLog, file = acqLogFile, sep=",", col.names=FALSE, row.names = FALSE)


