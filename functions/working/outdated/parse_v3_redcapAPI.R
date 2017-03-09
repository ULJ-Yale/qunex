
# read data exported by args_redcapAPI.sh and run_redcapAPI.php
record <- data.frame(read.csv('RedCapExport/RedCapExport_all_record.csv'), stringsAsFactors = FALSE)
metadata <- data.frame(read.csv('RedCapExport/RedCapExport_all_metadata.csv'), stringsAsFactors = FALSE) 
eventmap <- data.frame(read.csv('RedCapExport/RedCapExport_all_formEventMapping.csv'),stringsAsFactors = FALSE)                       

# list unique events
events <- sort(as.matrix(unique(record["redcap_event_name"])))                 

# list N3 IDs for all subjects 
allSubjects <- sort(as.matrix(unique(record["anticeviclab_id"])))

# initialize data frame to hold results
headersize <- 4
dfAll <- data.frame(matrix(NA, ncol=(length(events)*ncol(record)), nrow=(length(allSubjects)) + headersize))
  
# separate record by event and concatante horizontally, with one row per subject
for (i in 1:length(events)){
  
  # find subset of records containing event data
  df <- subset(record, redcap_event_name == events[i])
  # list subjects for whom event is empty
  emptySubjects <- data.frame(setdiff(allSubjects,((df[,1]))))
  
  # sort full and empty records into standardized dataframe for all subjects 
  orderedSubjects <- data.frame(matrix(NA, ncol=ncol(record), nrow=length(allSubjects)))
  orderedSubjects[(1:(nrow(df))),] <- as.matrix(df)
  orderedSubjects[((nrow(df)+1)):(length(allSubjects)),1] <- as.matrix(emptySubjects) 
  orderedSubjects <- orderedSubjects[order(orderedSubjects[1]),]
  rownames(orderedSubjects) <- orderedSubjects[,1]
  
  # populate data frame header from data dictionary
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
    mdIndex <- as.integer(which(metadata[,"field_name"] == field, arr.ind = TRUE))
    emIndex <- as.integer(which(subset(eventmap, unique_event_name == event)[,"form"] == as.vector(metadata[mdIndex,"form_name"]), arr.ind = TRUE))
    if ((length(mdIndex) > 0) && (length(emIndex) > 0)) {
      df2["FORM", k] <- as.vector(metadata[mdIndex,"form_name"])
      df2["LABEL", k] <- as.vector(metadata[mdIndex,"field_label"])
      print(c(event, field))
    } else {
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
write.csv(dfFinal, file="redcap_organized_v3.csv")


