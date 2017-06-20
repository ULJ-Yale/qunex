#!/usr/bin/env Rscript

library(RCurl)

outpath <- "/gpfs/project/fas/n3/Studies/DataDrop/RedCapExport/"

# user-specific API token must be initially created through RedCap website (https://poa-redcap.med.yale.edu/redcap_v6.17.2/) 
userToken <- as.vector(read.table('~/.redcapAPI/APItoken')[1,1])

# set output filenames 
fileRecord <- paste(outpath, 'RedCapExport_record.csv', sep="")
fileMetadata <- paste(outpath, 'RedCapExport_metadata.csv', sep="")
fileEventmap <- paste(outpath, 'RedCapExport_formEventMapping.csv', sep="")
fileOutput <- paste(outpath, 'RedCapExport_OrganizedDatabase.csv', sep="")

# export all records via RedCap API
result <- postForm(content='record', uri='https://poa-redcap.med.yale.edu/api/', token=userToken, format='csv', type='flat', rawOrLabel='raw', rawOrLabelHeaders='raw', returnFormat='csv')
write.table(result, file = fileRecord, append = FALSE, quote = FALSE, sep = ",", eol = "\n", na = "NA", dec = ".", row.names = FALSE, col.names = FALSE) 
record <- data.frame(read.csv(fileRecord, stringsAsFactors = FALSE))
# export data dictionary 
result <- postForm( content='metadata', uri='https://poa-redcap.med.yale.edu/api/', token=userToken, format='csv', returnFormat='csv')
write.table(result, file = fileMetadata, append = FALSE, quote = FALSE, sep = ",", eol = "\n", na = "NA", dec = ".", row.names = FALSE, col.names = FALSE) 
metadata <- data.frame(read.csv(fileMetadata, stringsAsFactors = FALSE))
# export form->event mapping table
result <- postForm(content='formEventMapping', uri='https://poa-redcap.med.yale.edu/api/', token=userToken, format='csv', returnFormat='csv' )
write.table(result, file = fileEventmap, append = FALSE, quote = FALSE, sep = ",", eol = "\n", na = "NA", dec = ".", row.names = FALSE, col.names = FALSE)
eventmap <- data.frame(read.csv(fileEventmap, stringsAsFactors = FALSE))

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
  rownames(df2)[(headersize + 1):(nrow(df2))] <- (1:(length(allSubjects)))
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

# remove unused columns
dropIndices <- as.vector(which( dfAll[1,] == "99999", arr.ind = TRUE)[,2])
dfFinal <- dfAll
dfFinal[, dropIndices] <- list(NULL)
rownames(dfFinal) <- rownames(df2)

# save output
write.csv(dfFinal, file = fileOutput)


