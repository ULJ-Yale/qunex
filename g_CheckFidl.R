#!/usr/bin/Rscript

library(ggplot2)

fidlfile <- FALSE
plotfile <- FALSE
fidlfolder <- FALSE
allcodes <- FALSE

args <- commandArgs(TRUE)

for (arg in args){
    if (grepl("-fidlfile=", arg)) fidlfile <- sub("-fidl=(.*)", "\\1", arg)
    if (grepl("-fidlfolder=", arg)) fidlfolder <- sub("-folder=(.*)", "\\1", arg)
    if (grepl("-plotfile=", arg)) plotfile <- sub("-plot=(.*)", "\\1", arg)
    if (grepl("-allcodes", arg)) allcodes <- TRUE
}

if (fidlfolder==FALSE) fidlfolder <- "."

if (fidlfile==FALSE){
    flist <- dir(path=fidlfolder, pattern="*\\.fidl$")
    nruns <- length(flist)
    plotfile <- FALSE
    tfolder <- file.path(fidlfolder, 'fidlplots')
    dir.create(tfolder, showWarnings = FALSE)
} else {
    flist <- c(fidlfile)
}


for (fidl in flist) {

    # ------- read header

    h <- read.delim(fidl, nrows=1, header=FALSE, blank.lines.skip=TRUE, sep="")

    TR <- h[1]
    codes <- h[2:length(h)]
    ncodes <- length(codes)


    # ------- read data

    d <- read.delim(fidl, skip=1, header=FALSE, blank.lines.skip=TRUE, sep="")

    cnames <- c('time','code','duration')
    cols <- dim(d)[2]

    if (cols > 3){
        for (b in 4:cols){
            cnames <- c(cnames, paste('B', as.character(b-3), sep=''))
        }
    }

    names(d) <- cnames

    # ------- add codes

    ecodes <- unique(d$code)
    ecodes <- ecodes[ecodes > 0]
    labels <- c(t(codes))
    labels <- labels[ecodes]

    d$event <- factor(d$code, levels=c(0:(length(codes)-1)), labels=c(t(codes)))
    if (allcodes) {
        d$rank <- d$code
    } else {
        d$rank <- as.numeric(factor(d$code))-1
    }

    #ggplot(d, aes(xmin=time, xmax=time+duration,ymin=code,ymax=code+1, color=event, fill=event)) + geom_rect(alpha=0.7, size=0) + geom_point(aes(x=time, y=0), color='black', size=0.5)
    fplot <- ggplot(d, aes(xmin=time, xmax=time+duration,ymin=-rank,ymax=-(rank+1), color=event, fill=event)) + geom_rect(alpha=0.7, size=0) + geom_rect(aes(xmin=time, xmax=time+0.5, ymin=0, ymax=0.5), size=0) + theme(axis.text.y=element_blank(), axis.ticks.y = element_blank()) + scale_y_continuous(breaks=c(0:-ncodes), minor_breaks=NULL) + geom_hline(x=0, color='darkgray')
    #ggplot(d, aes(xmin=time, xmax=time+duration,ymin=code,ymax=code+1, color=event, fill=event)) + geom_rect(alpha=0.7, size=0) + geom_rect(aes(xmin=time, xmax=time+duration, ymin=-0.5, ymax=0), size=0, alpha=0.5) + theme(axis.text.y=element_blank()) + scale_y_continuous(breaks=c(0:ncodes), minor_breaks=NULL)

    if (plotfile==FALSE) {
        tfile <- sub("\\.fidl", "-fidlplot.pdf", fidl)
        tfile <- file.path(tfolder, tfile)
    } else {
        tfile <- file.path(tfolder, plotfile)
    }

    if (allcodes){
        height <- ncodes/2.5
    } else {
        height <- length(ecodes)/2.5
    }

    pdf(file=tfile, width=15, height=height)
    print(fplot)
    dev.off()

}