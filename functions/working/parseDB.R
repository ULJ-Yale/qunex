#### Database User Functions ######################################################################################################
# --> create function 'pasreDB' to select subset of database columns by event, form, and field (optional)
###################################################################################################################################

args = commandArgs(trailingOnly=TRUE)
if (length(args) < 3) {
  stop("must provide three arguments: (1) Event, (2) Form, (3) Field or \"all\" to return entire form", call.=FALSE)
} 

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

parseDB(args[1],args[2],args[3])