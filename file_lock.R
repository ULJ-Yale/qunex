lock <- function(filename, identifier="R process", delay=1) {
  lock_file <- paste0(filename, ".lock")
  
  # wait while file exists
  while (TRUE) {
    if (!file.exists(lock_file))
    {
      # create lock file
      file.create(lock_file)
      cat(paste0("LOCKED BY ", identifier), file=lock_file)
      break
    }
    Sys.sleep(delay)
  }
}

clear_lock <- function(filename) {
  lock_file <- paste0(filename, ".lock")
  
  if (file.exists(lock_file)) {
    unlink(lock_file)
  }
}

lock_and_write <- function(string, filename, delay=1) {
  # lock
  lock(filename, delay=delay)
  
  # open file
  opened_file <- file(filename, "a")
  
  # write
  cat(string, file=opened_file)
  
  # close file
  close(opened_file)
  
  # unlock
  clear_lock(filename)
  
  return(1)
}