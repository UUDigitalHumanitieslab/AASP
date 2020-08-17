####################################################################################################
#
#   Functional Data Analysis (FDA)
#
#	Michele Gubian (PhD)
#	Centre for Language and Speech Technology
#	Radboud University Nijmegen
#	email: m.gubian@let.ru.nl, michele.gubian@gmail.com
#	website on FDA: http://lands.let.ru.nl/FDA
#
#	Licensed under GPLv3 (See http://www.gnu.org/licenses/gpl-3.0.html)
#
#   Modified by DigialHumanitiesLab, Utrecht University, 2020
####################################################################################################



library(fda)
library(lattice)
library(ggplot2)

root_dir = '/Users/janss089/git/aasp/'
plots_dir = paste(root_dir,'plots/',sep='')
data_dir =  paste(root_dir,'input_data/',sep='')
scripts_dir =  paste(root_dir,'scripts/',sep='')

# use pca.fd version from package fda_2.2.5.tar.gz or earlier (you find a copy in the scripts/ dir)
source(paste(scripts_dir,'pca.fd.R',sep=''))
# this is a modified version of the landmarkreg() command 
source(paste(scripts_dir,'landmarkreg.nocurve.R',sep=''))
# this is a slightly modified version of the plot.pca.fd() command,
# but you can also use the standard one.
source(paste(scripts_dir,'plot.pca.fd.corr.R',sep=''))


# filename, speaker, class, durations ('DH' stands for diphthong-hiatus) 
# DH_data = read.csv(file = paste(data_dir,"DH_data.csv",sep=''))
data = read.csv(file = paste(own_dir,"data_with_dois.csv",sep=''))
n_items = dim(data)[1]
speakers = unique(data$spk) 

# f0 data frames
len_f0 = c() # number of samples 
dur_f0 = c() # in ms
all_data <- data.frame()

for (i in 1:n_items) {
    item <- read.csv(paste(own_dir,data$filename[i],".pitch",sep=''),h=T)
    sample = item[item$time>=data$doi_start_time[i]&item$time<=data$doi_end_time[i]&item$f0>0.1,]
    sample$id <- i
    sample$time_zero <- sample$time - sample$time[1]
    sample$f0_log <- 12 * logb(sample$f0, base = 2)
    sample$f0_norm <- sample$f0_log / mean(sample$f0_log)
    sample$filename <- data$filename[i]
    all_data <- rbind(all_data, sample)
    len_f0 <- cbind(len_f0, nrow(sample))
    dur_f0 <- cbind(dur_f0, tail(sample$time,1)-head(sample$time,1))
}

################## Smoothing ######################################

mean_dur_f0 = mean(dur_f0)
min_dur_f0 = min(dur_f0)

# GCV for smoothing

n_knots_vec <- seq(4,trunc(median(len_f0)/2),4) # explore from 4 knots up to around half the number of samples
loglam_vec <- seq(-4,10,2) # explore lambda from 10^(-4) to 10^10
if (length(unique(all_data$id)) > 5) {
  sampled_ids <- sample(unique(all_data$id),5) # a data subset, to save computation time
} else {
  sampled_ids <- unique(all_data$id)
}

gcv_err_frame <- data.frame()

# compute GCV error for all (n_knots, lambda) combinations on the i_sample curves, store it in gcv_err (may take some minutes)
for (k in n_knots_vec) {
    for (l in loglam_vec) {
        gcv_err <- c()
        norm_rng <- c(0,min_dur_f0)
        knots <- seq(0,min_dur_f0,length.out = k) # this means that for shorter files than average, last knot will fall out of file....
        Lfdobj <- 3 # 2 + order of derivative expected to be used. We need velocity to apply Xu's principle, thus order = 1
        norder <- 5 # 2 + Lfdobj 
        nbasis <- length(knots) + norder - 2 # a fixed relation about B-splines
        basis <- create.bspline.basis(norm_rng, nbasis, norder, knots)
        fdPar_Obj <- fdPar(basis, Lfdobj, 10^(l))
        for (id in sampled_ids) {
            # apply linear time normalization
            t_norm <- (all_data$f0_norm[all_data$id==id] / dur_f0[id]) * mean_dur_f0
            gcv_err <- cbind(gcv_err, smooth.basis(t_norm,all_data$f0_norm[all_data$id==id],fdPar_Obj)$gcv)
            gcv_log_err <- log(median(gcv_err, na.rm = T))
            gcv_err_frame <- rbind(gcv_err_frame, c(k, l, gcv_log_err))
        }
    }
}    

colnames(gcv_err_frame) <- c('knots', 'lambda', 'gcv_err')

# plot using ggplot2
png(paste(plots_dir,'GCV_log_err_f0.png',sep=''))
ggplot(gcv_err_frame, aes(knots, lambda, fill=gcv_err)) +
  geom_tile() +
  scale_x_continuous("Knots", breaks=c(4,8)) +
  scale_y_continuous("Lambda", breaks=c(-4, -2, 0, 2, 4, 6, 8, 10), minor_breaks=NULL)
dev.off()

# min GCV error is in:
minerr <- min(gcv_err_frame$gcv_err)
argmin <- gcv_err_frame[gcv_err_frame$gcv_err==minerr,] # rows are lambda indices, cols are n_knots indices
# arg min log lambda is:
argmin$lambda
# arg min n_knots is:
argmin$knots

# Inspection of gcv_log_err for f0 shows that:
# min estimated gcv error is obtained basically at the highest number of knots and at low lambda.
# However, the captured detail looks too much (overfitting) for the forthcoming analysis.
# So, lambda and n_knots will be chosen by combining eye inspection of some curves (code below) and the guidance of the GCV figure (above).
# (See the paper for details)

id <- sample(sampled_ids, 1) # select random data item
for (l in loglam_vec) {
  for (k in n_knots_vec) {
		lambda = 10^(l) 
		norm_rng <- c(0,mean_dur_f0)
		knots <- seq(0,mean_dur_f0,length.out = k)
		Lfdobj <- 3
		norder <- 5
		nbasis <- length(knots) + norder - 2
		basis <- create.bspline.basis(norm_rng, nbasis, norder, knots)
		fdPar_Obj <- fdPar(basis, Lfdobj,lambda)
		t_norm <- (all_data$time_zero[all_data$id==id] / dur_f0[id]) * mean_dur_f0
		y_fd <- smooth.basis(t_norm,all_data$f0_norm[all_data$id==id],fdPar_Obj)$fd
		png(paste(plots_dir,'f0_fit_loglam',l,'n_knots',k,'.png',sep=''))
		
		plot(y_fd,xlab='time (ms)',ylab='F0 (norm. semitones)',main = '',las=1,cex.axis=1.5,cex.lab=1.5,col='red',lwd=3,ylim=c(-3,5))
		points(t_norm,all_data$f0_norm[all_data$id==id],pch=20)
	  dev.off()
  }
}