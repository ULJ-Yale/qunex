
record <- data.frame(read.csv('RedCapExport/RedCapExport_all_record.csv'), stringsAsFactors = FALSE)     
metadata <- data.frame(read.csv('RedCapExport/RedCapExport_all_metadata.csv'), stringsAsFactors = FALSE) 

#todo: update arg script for eventmapping
eventmap <- data.frame(read.csv('eventMapping.csv'),stringsAsFactors = FALSE)                       

events <- sort(as.matrix(unique(record["redcap_event_name"])))                 

# get N3 IDs for all subjects that have general records filled out
allSubjects <- (subset(record, redcap_event_name == "0_general_informat_arm_1")["anticeviclab_id"])
allSubjects <- as.vector(allSubjects[,1])

# initialize dataframe and variables
N <- length(allSubjects)
headersize <- 4
allData <- data.frame(matrix(NA, nrow=N+headersize, ncol=(nrow(metadata)*length(events))))
nfields <- 0
fieldnames <- 0
formfields <- 0
formnames <- 0
eventnames <- 0
for (k in 1:nrow(eventmap["form"])){ # read each event in eventmap and build column for every field for event in metadata
  fieldnames <- as.matrix((subset(metadata, form_name == eventmap[k,3]))[1])
  fieldnames <- as.vector(fieldnames)
  fieldlabels <- as.matrix((subset(metadata, form_name == eventmap[k,3]))[5])
  fieldlabels <- as.matrix(fieldlabels)
  formfields <- length(fieldnames)
  formnames <-  as.vector(rep((eventmap[k,3]), formfields))
  eventnames <- as.vector(rep((eventmap[k,2]), formfields))
  nfields <- nfields + formfields
  formstart <- nfields - formfields
  for ( z in 1:formfields){
    print(c("building dataframe...field:", fieldnames[z]))
    allData[1,(formstart + z)] <- eventnames[z]
    allData[2,(formstart + z)] <- formnames[z]
    allData[3,(formstart + z)] <- fieldnames[z]
    allData[4,(formstart + z)] <- fieldlabels[z]
  }
}

header <- append("LABEL", allSubjects)
header <- append("FIELD", header)
header <- append("FORM", header)
header <- append("EVENT", header)
rownames(allData) <- header

# populate allData from records
for (subject in allSubjects){
  #for every column, find matching data in record
  for (s in 1:(sum(!is.na( allData["EVENT",])))){
    if (is.element((allData["FIELD", s]), colnames(record)) == TRUE) {
      if ((sum(!is.na(subset(record, anticeviclab_id == subject & redcap_event_name == (allData["EVENT",s]))))) == 0) {
        allData[subject, s] <- allData[subject, s]
      } else {
        allData[subject, s] <- as.vector(subset(record, anticeviclab_id == subject & redcap_event_name == (allData["EVENT",s]))[,(allData["FIELD", s])])
      }
    } else {
      allData[subject, s] <- "#not-exported"
    }
   print(c("populating dataframe ---subject:",subject, "event: ",(allData["EVENT", s]) ," field: ", (allData["FIELD", s])))
  }
}

write.csv(allData, file="redcap_organized_output.csv")

