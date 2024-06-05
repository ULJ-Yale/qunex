#!/usr/bin/env Rscript

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

#   ``bold_stats``
#
#   Plots movement data, creates movement reports and information for data
#   scrubbing.
#
#   Parameters:
#       --folder, -f (str, default '.'):
#           The folder to look for .dat data.
#
#       --mreport, -mr (str, default 'none'):
#           The file to write movement report to.
#
#       --preport, -pr (str, default 'none'):
#           The file to write movement report after scrubbing to.
#
#       --sreport, -sr (str, default 'none'):
#           The file to write scrubbing report to.
#
#       --session, -s (str, default 'none'):
#           Session id to use in plots and reports.
#
#       --dvars, -d (numeric, default 3):
#           Threshold to use for computing dvars rejections.
#
#       --dvarsme, -e (numeric, default 1.5):
#           Threshold to use for computing dvarsme rejections.
#
#       --movement, -m (numeric, default 0.5):
#           Threshold to use for computing frame-to-frame movement rejections.
#
#       --radius, -rd (numeric, default 50):
#           Radius (in mm) from center of head to cortex to estimate rotation
#           size.
#
#       --tr (numeric, default 2.5):
#           TR to be used when generating .fidl files.
#
#       --fidl (str, default 'none'):
#           Whether to output and what to base fild on ('fd', 'dvars',
#           'dvarsme', 'udvars', 'udvarsme', 'idvars', 'idvarsme', 'none').
#
#       --plotr (str, default 'mov_report'):
#           Root name of the plot file, 'none' to omit plotting.
#
#       --post (str, default 'none'):
#           Whether to create report of scrubbing effect and what to base it on
#           ('fd', 'dvars', 'dvarsme', 'udvars', 'udvarsme', 'idvars',
#           'idvarsme', 'none').
#
#       --bolds (str, default ''):
#           Vertical line | separated list of bold indeces for which to do the
#           stat report.
#
#       --pref (str, default ''):
#           Prefix for the reports.
#
#       --verbose, -v (bool, default TRUE):
#           Be talkative when running the script.
#
#       --plot(bool, default FALSE):
#           Whether to plot.
#
#       --rname (str, default 'bold'):
#           Root name for the bold files.
#
#       --bold_tail (str, default ''):
#           Tail of bold files.
#
#   Notes:
#       (c) Grega Repovs
#       2011-07-26 -> First complete version of the script
#       2012-09-20 -> Added reporting of stats after scrubbing
#       2013-12-22 -> Dumbed down to just print the reports
#       2015-07-05 -> Changed to deal with alternative root bold names
#       2019-04-25 -> Changed subject to session
#
#       (c) Jure Demsar
#       2019-07-31 -> Added file locking mechanism
#       2019-21-04 -> Improved file locking mechanism
#


# ---> file locking library

library(filelock)


# ---> defaults

folder    <- "."
mreport   <- ""
preport   <- ""
sreport   <- ""
session   <- ""
dvarst    <- 3.0
dvarsmet  <- 1.5
movt      <- 0.5
plotr     <- "mov_report"
radius    <- 50
TR        <- 2.5
fidl      <- "none"
post      <- "none"
bolds     <- ""
pref      <- ""
verbose   <- TRUE
plot      <- FALSE
rname     <- "bold"
bold_tail <- ''

# ---> processing commands

args <- commandArgs(TRUE)

for (arg in args){
    if (grepl("-f=", arg))        folder     <- sub("-f=(.*)", "\\1", arg)
    if (grepl("-folder=", arg))   folder     <- sub("-folder=(.*)", "\\1", arg)
    if (grepl("-mr=", arg))       mreport    <- sub("-mr=(.*)", "\\1", arg)
    if (grepl("-mreport=", arg))  mreport    <- sub("-mreport=(.*)", "\\1", arg)
    if (grepl("-sr=", arg))       sreport    <- sub("-sr=(.*)", "\\1", arg)
    if (grepl("-sreport=", arg))  sreport    <- sub("-sreport=(.*)", "\\1", arg)
    if (grepl("-pr=", arg))       preport    <- sub("-pr=(.*)", "\\1", arg)
    if (grepl("-preport=", arg))  preport    <- sub("-preport=(.*)", "\\1", arg)
    if (grepl("-s=", arg))        session    <- sub("-s=(.*)", "\\1", arg)
    if (grepl("-session=", arg))  session    <- sub("-session=(.*)", "\\1", arg)
    if (grepl("-d=", arg))        dvarst     <- as.numeric(sub("-d=(.*)", "\\1", arg))
    if (grepl("-dvars=", arg))    dvarst     <- as.numeric(sub("-dvars=(.*)", "\\1", arg))
    if (grepl("-e=", arg))        dvarsmet   <- as.numeric(sub("-e=(.*)", "\\1", arg))
    if (grepl("-dvarsme=", arg))  dvarsmet   <- as.numeric(sub("-dvarsme=(.*)", "\\1", arg))
    if (grepl("-m=", arg))        movt       <- as.numeric(sub("-m=(.*)", "\\1", arg))
    if (grepl("-movement=", arg)) movt       <- as.numeric(sub("-movement=(.*)", "\\1", arg))
    if (grepl("-rd=", arg))       radius     <- as.numeric(sub("-rd=(.*)", "\\1", arg))
    if (grepl("-radius=", arg))   radius     <- as.numeric(sub("-radius=(.*)", "\\1", arg))
    if (grepl("-tr=", arg))       TR         <- as.numeric(sub("-tr=(.*)", "\\1", arg))
    if (grepl("-verbose", arg))   verbose    <- TRUE
    if (grepl("-v", arg))         verbose    <- TRUE
    if (grepl("-fidl=", arg))     fidl       <- sub("-fidl=(.*)", "\\1", arg)
    if (grepl("-post=", arg))     post       <- sub("-post=(.*)", "\\1", arg)
    if (grepl("-plot=", arg))     plotr      <- sub("-plot=(.*)", "\\1", arg)
    if (grepl("-bolds=", arg))    bolds      <- sub('-bolds="?([0-9|]*)"?', "\\1", arg)
    if (grepl("-pref=", arg))     pref       <- sub("-pref=(.*)", "\\1", arg)
    if (grepl("-rname=", arg))    rname      <- sub("-rname=(.*)", "\\1", arg)
    if (grepl("-bold_tail=", arg)) bold_tail <- sub("-bold_tail=(.*)", "\\1", arg)
}


# ---> creating list of files to process

if (verbose) cat("Starting BOLD Movement and Statistics Report\n")
if (verbose) cat("Working with data in folder: ", folder, "\n", sep="")

bolds <- strsplit(bolds, "[|]")[[1]]
nruns <- length(bolds)

if (nruns == 0){
    print("ERROR: No BOLD files were specified for processing! Please check the relevant batch.txt file and create_stats_report log.")
    quit()
}



# ---> loading library

if (plotr != "") {
    plot = TRUE
    library(ggplot2)
    library(reshape2)
    library(scales)
}


# ---> opening movement report file

if (mreport != ""){
    if (verbose) cat("\n---> opening movement report file [", mreport, "]", sep="")
    msummary <- TRUE
    if (!file.exists(mreport)){
        header = TRUE
    } else {
        header = FALSE
    }
    
    # lock movement report file
    mreportlockfile <- paste0(mreport, ".lck")
    mreportlock <- lock(mreportlockfile)
    
    mrfile <- file(mreport, "a")

    if (header){
        cat("session", "run", "stat", "dx", "dy", "dz", "X", "Y", "Z", "\n", file=mrfile, sep="\t")
    }
} else {
    msummary <- FALSE
}


# ---> opening post scrubbing report file

if (preport != ""){
    if (verbose) cat("\n---> opening post scrubbing report file [", preport, "]", sep="")
    psummary <- TRUE
    if (!file.exists(preport)){
        header = TRUE
    } else {
        header = FALSE
    }
    
    # lock post scrubbing report file
    preportlockfile <- paste0(preport, ".lck")
    preportlock <- lock(preportlockfile)
    
    prfile <- file(preport, "a")

    if (header){
        cat("session", "run", "stat", "dx", "dy", "dz", "X", "Y", "Z", "\n", file=prfile, sep="\t")
    }
} else {
    psummary <- FALSE
}


# ---> opening scrubbing report file

if (sreport != ""){
    if (verbose) cat("\n---> opening scrubbing report file [", sreport, "]", sep="")
    ssummary <- TRUE
    if (!file.exists(sreport)){
        header = TRUE
    } else {
        header = FALSE
    }
    
    # lock scrubbing report file
    sreportlockfile <- paste0(sreport, ".lck")
    sreportlock <- lock(sreportlockfile)
    
    srfile <- file(sreport, "a")

    if (header){
        cat("session", "run", "mov", "dvars", "dvarsme", "idvars", "idvarsme", "udvars", "udvarsme", "%mov", "%dvars", "%dvarsme", "%idvars", "%idvarsme", "%udvars", "%udvarsme", "\n", file=srfile, sep="\t")
    }
} else {
    ssummary <- FALSE
}


# ---> processing files

first <- TRUE
dvfirst <- TRUE
nframes <- 0
boldnames <- c()
for (b in bolds){
    m <- paste(rname, b, bold_tail, sep='')
    boldnames <- c(boldnames, m)

    if (verbose) cat("\n\nBOLD", b, "\n---> reading data")

    # ---> READ DATA
    #
    # dat    --- frame    dx(mm)    dy(mm)    dz(mm)    X(deg)    Y(deg)    Z(deg)     scale
    # scrub  --- frame  mov dvars   dvarsme idvars  idvarsme    udvars  udvarsme
    # bstats --- frame  n   m   min max var sd  dvars   dvarsm  dvarsme

    t  <- read.table(paste(folder, paste(rname, b, '_mov.dat',   sep=''), sep="/"))
    if (verbose) cat("\n     ... ", paste(rname, b, '_mov.dat',   sep=''), sep="")
    sc <- read.delim(paste(folder, paste(rname, b, bold_tail, '.scrub',     sep=''), sep="/"), comment.char = "#", sep="")
    if (verbose) cat("\n     ... ", paste(rname, b, bold_tail, '.scrub',   sep=''), sep="")
    dv <- read.delim(paste(folder, paste(rname, b, bold_tail, '.bstats',    sep=''), sep="/"), comment.char = "#", sep="")
    if (verbose) cat("\n     ... ", paste(rname, b, bold_tail, '.bstats',   sep=''), sep="")

    if (verbose) cat("\n---> processing")

    names(t)  <- c('frame', 'dx', 'dy', 'dz', 'X', 'Y', 'Z')

    t$dx <- t$dx - t$dx[1]
    t$dy <- t$dy - t$dy[1]
    t$dz <- t$dz - t$dz[1]
    t$Z  <- t$Z  - t$Z[1]
    t$Y  <- t$Y  - t$Y[1]
    t$X  <- t$X  - t$X[1]

    nframes <- length(t$X)

    # --- compute per frame correction (dx)

    td <- as.matrix(t)
    td <- diff(td)
    td <- data.frame(td)
    td <- rbind(0, td)
    names(td) <- c('frame', 'dx', 'dy', 'dz', 'X', 'Y', 'Z')
    td$frame <- c(1:dim(td)[1])

    # --- convert degrees to mm

    td$Xm <- radius * tan(td$X*2*pi/360)
    td$Ym <- radius * tan(td$Y*2*pi/360)
    td$Zm <- radius * tan(td$Z*2*pi/360)

    # --- compute framewise displacement

    td$fd <- abs(td$dx) + abs(td$dy) + abs(td$dz) + abs(td$Zm) + abs(td$Ym) + abs(td$Xm)
    td$ad <- sqrt(td$dx^2 + td$dy^2 + td$dz^2 + td$Zm^2 + td$Ym^2 + td$Xm^2)

    # ---- let's check if we also have dvars data

    dodv <- FALSE

    # ---- print summary report

    if (msummary){
        if (verbose) cat("\n---> printing summary report")

        cat(session, m, "mean", mean(t$dx), mean(t$dy), mean(t$dz), mean(t$X), mean(t$Y), mean(t$Z), "\n", file=mrfile, sep="\t")
        cat(session, m, "sd", sd(t$dx), sd(t$dy), sd(t$dz), sd(t$X), sd(t$Y), sd(t$Z), "\n", file=mrfile, sep="\t")
        cat(session, m, "span", max(t$dx)-min(t$dx), max(t$dy)-min(t$dy), max(t$dz)-min(t$dz), max(t$X)-min(t$X), max(t$Y)-min(t$Y), max(t$Z)-min(t$Z), "\n", file=mrfile, sep="\t")
        cat(session, m, "max", max(abs(td$dx)), max(abs(td$dy)), max(abs(td$dz)), max(abs(td$X)), max(abs(td$Y)), max(abs(td$Z)), "\n", file=mrfile, sep="\t")
        cat(session, m, "md", mean(abs(td$dx)), mean(abs(td$dy)), mean(abs(td$dz)), mean(abs(td$X)), mean(abs(td$Y)), mean(abs(td$Z)), "\n", file=mrfile, sep="\t")
        cat(session, m, "med", median(abs(td$dx)), median(abs(td$dy)), median(abs(td$dz)), median(abs(td$X)), median(abs(td$Y)), median(abs(td$Z)), "\n", file=mrfile, sep="\t")
        cat(session, m, "md2_max", mean(abs(td$dx))^2/max(td$dx), mean(abs(td$dy))^2/max(td$dy), mean(abs(td$dz))^2/max(td$dz), mean(abs(td$X))^2/max(td$X), mean(abs(td$Y))^2/max(td$Y), mean(abs(td$Z))^2/max(td$Z), "\n", file=mrfile, sep="\t")

        cat(session, m, "frame_dspl", mean(td$fd), median(td$fd), max(td$fd), sd(td$fd), "\n", file=mrfile, sep="\t")

        if(dodv){
            cat(session, m, "mean_dvars", mean(dv$dvars), mean(dv$dvarsm), mean(dv$dvarsme), "\n", file=mrfile, sep="\t")
        }
    }

    # ---- print post summary report

    if (psummary){
        if (verbose) cat("\n---> printing post scrubbing report")
        if (post != "none"){
            ts  <- sc[[post]]
            pt  <- t[ts==0,]
            ptd <- td[ts==0,]
            pdv <- dv[ts==0,]
        } else {
            pt  <- t
            ptd <- td
            pdv <- dv
        }

        cat(session, m, "mean", mean(pt$dx), mean(pt$dy), mean(pt$dz), mean(pt$X), mean(pt$Y), mean(pt$Z), "\n", file=prfile, sep="\t")
        cat(session, m, "sd", sd(pt$dx), sd(pt$dy), sd(pt$dz), sd(pt$X), sd(pt$Y), sd(pt$Z), "\n", file=prfile, sep="\t")
        cat(session, m, "span", max(pt$dx)-min(pt$dx), max(pt$dy)-min(pt$dy), max(pt$dz)-min(pt$dz), max(pt$X)-min(pt$X), max(pt$Y)-min(pt$Y), max(pt$Z)-min(pt$Z), "\n", file=prfile, sep="\t")
        cat(session, m, "max", max(abs(ptd$dx)), max(abs(ptd$dy)), max(abs(ptd$dz)), max(abs(ptd$X)), max(abs(ptd$Y)), max(abs(ptd$Z)), "\n", file=prfile, sep="\t")
        cat(session, m, "md", mean(abs(ptd$dx)), mean(abs(ptd$dy)), mean(abs(ptd$dz)), mean(abs(ptd$X)), mean(abs(ptd$Y)), mean(abs(ptd$Z)), "\n", file=prfile, sep="\t")
        cat(session, m, "med", median(abs(ptd$dx)), median(abs(ptd$dy)), median(abs(ptd$dz)), median(abs(ptd$X)), median(abs(ptd$Y)), median(abs(ptd$Z)), "\n", file=prfile, sep="\t")
        cat(session, m, "md2_max", mean(abs(ptd$dx))^2/max(ptd$dx), mean(abs(ptd$dy))^2/max(ptd$dy), mean(abs(ptd$dz))^2/max(ptd$dz), mean(abs(ptd$X))^2/max(ptd$X), mean(abs(ptd$Y))^2/max(ptd$Y), mean(abs(ptd$Z))^2/max(ptd$Z), "\n", file=prfile, sep="\t")

        cat(session, m, "frame_dspl", mean(ptd$fd), median(ptd$fd), max(ptd$fd), sd(ptd$fd), "\n", file=prfile, sep="\t")

        if(dodv){
            cat(session, m, "mean_dvars", mean(pdv$dvars), mean(pdv$dvarsm), mean(pdv$dvarsme), "\n", file=prfile, sep="\t")
        }
    }


    # --- prepare data for figures

    if (plot) {

        if (verbose) cat("\n---> preparing plotting data")

        # --- convert bad data to long form

        badm  <- melt(sc, id=c("frame"), measure=c('mov', 'dvars'))
        badme <- melt(sc, id=c("frame"), measure=c('mov', 'dvarsme'))

        tfd <- melt(td, id=c('frame'), measure=c('fd'))
        tad <- melt(td, id=c('frame'), measure=c('ad'))

        t  <- melt(t,  id=c('frame'), measure=c('dx', 'dy', 'dz', 'X', 'Y', 'Z'))
        td <- melt(td, id=c('frame'), measure=c('dx', 'dy', 'dz', 'X', 'Y', 'Z'))

        t$run <- m
        td$run <- m
        tfd$run <- m
        tad$run <- m
        badm$run <- m
        badme$run <- m

        if (first){
            d <- t
            dd <- td
            dfd <- tfd
            dad <- tad
            dbadm <- badm
            dbadme <- badme
            first <- FALSE
        } else {
            d <- rbind(d, t)
            dd <- rbind(dd, td)
            dfd <- rbind(dfd, tfd)
            dad <- rbind(dad, tad)
            dbadm <- rbind(dbadm, badm)
            dbadme <- rbind(dbadme, badme)
        }

        # --- dvars data

        dvm  <- melt(dv, id=c('frame'), measure=c('dvarsm'))
        dvme <- melt(dv, id=c('frame'), measure=c('dvarsme'))

        dvm$run  <- m
        dvme$run <- m

        if (dvfirst){
            ddvm <- dvm
            ddvme <- dvme
            dvfirst <- FALSE
        } else {
            ddvm <- rbind(ddvm, dvm)
            ddvme <- rbind(ddvme, dvme)
        }

    }

    # --- print per frame scrubbing reports

    if (ssummary){
        if (verbose) cat("\n---> printing per frame report")
        cat(session, m, sum(sc$mov), sum(sc$dvars), sum(sc$dvarsme), sum(sc$idvars), sum(sc$idvarsme), sum(sc$udvars), sum(sc$udvarsme), sprintf("%.1f\t%.1f\t%.1f\t%.1f\t%.1f\t%.1f\t%.1f", sum(sc$mov)/nframes*100, sum(sc$dvars)/nframes*100, sum(sc$dvarsme)/nframes*100, sum(sc$idvars)/nframes*100, sum(sc$idvarsme)/nframes*100, sum(sc$udvars)/nframes*100, sum(sc$udvarsme)/nframes*100),"\n", file=srfile, sep="\t")
    }

    # --- print fidl report

    if (fidl != "none"){

        if (verbose) cat("\n---> creating fidl scrubbing file ", paste(rname, b, bold_tail, '_scrub.fidl', sep=''), sep="")

        # --- open file and print header

        ffile <- file(paste(folder, paste(rname, b, bold_tail, '_scrub.fidl', sep=''), sep='/'), "w")
        cat(TR, "\n", file=ffile, sep="\t")
        ts <- sc[[fidl]]

        # --- identify starts and ends of frames to ignore

        tsd <- diff(ts)
        ion <- which(tsd==1)
        ioff <- which(tsd==-1)

        # --- check for first and last frames to ignore

        if (ts[1] == 1) ion <- append(0, ion)
        if (ts[nframes] == 1) ioff <- append(ioff, nframes)

        # --- compute ignore lengths

        ilen <- ioff-ion

        # --- print frames to ignore in fidl format

        if(length(ion)>0){
            for (n in 1:length(ion)){
                cat(ion[n]*TR, -ilen[n], "\n", file=ffile, sep="\t")
            }
        }

        # --- close file

        close(ffile)
    }

}

# --- close and unlock files

if (msummary) { 
    close(mrfile)
    unlock(mreportlock)
}
if (psummary) {
    close(prfile)
    unlock(preportlock)
}
if (ssummary) {
    close(srfile)
    unlock(sreportlock)
}

if (plot) {
    if (verbose) cat("\n\n---> plotting figures")
    major <- (nframes %/% 300 + 2) * 10

    if (verbose) cat("\n     ... _cor.pdf")
    pdf(file=paste(folder, paste(rname, bold_tail, '_', pref, plotr, "_cor.pdf", sep=""), sep="/"), width=10, height=3.3*nruns)
    d$run <- factor(as.character(d$run), levels=boldnames, labels=boldnames, ordered=TRUE)
    with(d, levels(run))
    print(qplot(frame, value, data = d, colour=variable, fill=variable, geom="line") + facet_grid(run ~ .) + labs(title=paste("Movement correction parameters", session, sep=" ")) + scale_x_continuous("frame",  breaks=seq(0,500,major), minor_breaks= seq(0,500,1), expand=c(0,0.5)) + ylab("mm / deg"))
    dev.off()
    if (verbose) cat(" ... ok")

    # pdf(file=paste(folder, "mov-size-report.pdf", sep="/"), width=10, height=3.3*nruns)
    # qplot(frame, abs(value), data = dd, colour=variable, fill=variable, geom="line") + facet_grid( run ~ .) + labs(title=dtitle) + scale_x_continuous("frame",  breaks=seq(0,500,major), minor_breaks= seq(0,500,1), expand=c(0,0.5)) + ylab("mm / deg")
    # dev.off()

    dad <- rbind(dfd, ddvme)
    dfd <- rbind(dfd, ddvm)

    if (verbose) cat("\n     ... _dvars.pdf")
    pdf(file=paste(folder, paste(rname, bold_tail, '_', pref, plotr, "_dvars.pdf", sep=""), sep="/"), width=10, height=2*nruns)
    dbadm <- dbadm[dbadm$value > 0, ]
    ylim <- max(dfd$value)
    ylim <- 10
    dfd$run <- factor(as.character(dfd$run), levels=boldnames, labels=boldnames, ordered=TRUE)    
    dbadm$run <- factor(as.character(dbadm$run), levels=boldnames, labels=boldnames, ordered=TRUE)
    with(dfd, levels(run))
    with(dbadm, levels(run))
    p <- qplot(frame, abs(value), data=dfd, colour=variable, fill=variable, geom="line") + facet_grid(run ~ .) + labs(title=paste("Movement and signal change (dvars) across frames", session, sep=" ")) + scale_x_continuous("frame",  breaks=seq(0,500,major), minor_breaks= seq(0,500,1), expand=c(0,0.5)) + ylab("") + geom_hline(aes(yintercept=movt), color="black", alpha=0.3) + geom_hline(aes(yintercept=dvarst), color="black", alpha=0.3)
    if (dim(dbadm)[1] > 0){
        print(p + geom_rect(aes(xmin = frame-0.5, xmax = frame + 0.5, ymin = 0, ymax = value/value*dvarst), data=dbadm, colour=alpha("blue", alpha=0), fill=alpha("blue", alpha=0.3)) + scale_y_continuous("", limits=c(0,ylim)))
    } else {
        print(p + scale_y_continuous("", limits=c(0, ylim)))
    }
    dev.off()
    if (verbose) cat(" ... ok")

    if (verbose) cat("\n     ... _dvarsme.pdf")
    pdf(file=paste(folder, paste(rname, bold_tail, '_', pref, plotr, "_dvarsme.pdf", sep=""), sep="/"), width=10, height=2*nruns)
    dbadme <- dbadme[dbadme$value > 0, ]
    ylim <- max(dad$value)
    ylim <- 6
    dad$run <- factor(as.character(dad$run), levels=boldnames, labels=boldnames, ordered=TRUE)
    dbadme$run <- factor(as.character(dbadme$run), levels=boldnames, labels=boldnames, ordered=TRUE)
    with(dad, levels(run))
    with(dbadme, levels(run))
    p <- qplot(frame, value, data=dad, colour=variable, fill=variable, geom="line") + facet_grid(run ~ .) + labs(title=paste("Movement and signal change (dvarme) across frames", session, sep=" ")) + scale_x_continuous("frame",  breaks=seq(0,500,major), minor_breaks= seq(0,500,1), expand=c(0,0.5)) + ylab("") + geom_hline(aes(yintercept=movt), color="black", alpha=0.3) + geom_hline(aes(yintercept=dvarsmet), color="black", alpha=0.3)
    if (dim(dbadme)[1] > 0){
        print(p + geom_rect(aes(xmin = frame-0.5, xmax = frame + 0.5, ymin = 0, ymax = value/value*dvarsmet), data=dbadme, colour=alpha("blue", alpha=0), fill=alpha("blue", alpha=0.3)) + scale_y_continuous("", limits=c(0, ylim)))
    } else {
        print(p + scale_y_continuous("", limits=c(0, ylim)))
    }
    dev.off()
    if (verbose) cat(" ... ok")
}

# --- report all ok!

if (verbose) cat("\n\n---> DONE\n\n")
ok <- file(paste(folder, '.r.ok', sep="/"), 'w')
cat("ok", file=ok)
close(ok)

# --- done!
