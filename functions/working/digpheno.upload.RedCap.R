#!/usr/bin/env Rscript

# load RCurl to integrate with API
library(RCurl)

##################################################### Upload Digpheno Data #########################################################
# --> use RedCap API to upload digital phenotyping data files
####################################################################################################################################

# user-specific API token must be initially created through RedCap website (https://poa-redcap.med.yale.edu/redcap_v6.17.2/) 
userToken <- as.vector(read.table('~/.redcapAPI/APItoken.CTNA.test')[1,1])

file='/gpfs/project/fas/n3/Studies/DataDrop/digpheno/samplefile.txt'

result <- postForm(
    uri='https://poa-redcap.med.yale.edu/api/',
    token=userToken,
    content='file',
    action='import',
    record='1',
    field='upload_here',
    returnFormat='csv',
    file=fileUpload(file)
)
print(result)