options(error = clean_up(...))

# lock storage
locks = vector()

# cleanup on error
options(error = clean_up(
    for (lock_file in locks) {
      if (file.exists(lock_file)) {
        unlink(lock_file)
      }
    }
  ))

# create a lock file for a certain file
lock <- function(filename, delay=1, identifier="R process") {
  lock_file <- paste0(filename, ".lock")
  
  # wait while file exists
  while (TRUE) {
    if (!file.exists(lock_file))
    {
      # create lock file
      file.create(lock_file)
      cat(paste0("LOCKED BY ", identifier), file=lock_file)
      
      # store lock file
      locks <- append(locks, lock_file)
      break
    }
    Sys.sleep(delay)
  }
}

# remove a lock file for a certain file
unlock <- function(filename) {
  lock_file <- paste0(filename, ".lock")
  
  if (file.exists(lock_file)) {
    unlink(lock_file)
  }
  
  if (lock_file %in% locks) {
    locks <- locks[locks != lock_file]
  }
}

# lock a file, write into it, then unlock it
safe_write <- function(string, filename, delay=1) {
  # lock
  lock(filename, delay=delay)
  
  # open file
  f <- file(filename, "a")
  
  # write
  cat(string, file=f)
  
  # close file
  close(f)
  
  # unlock
  unlock(filename)
  
  return(1)
}
