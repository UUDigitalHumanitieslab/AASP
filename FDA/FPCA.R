library(fda)
library(lattice)

load('fdaEnvironment.RData')

######## Smoothing
# selected values:
lambda <- 10^(6)
n_knots <- 8
# build global f0 fd object
norm_rng <- c(0,mean_dur_f0)
knots <- seq(0,mean_dur_f0,length.out = n_knots)
Lfdobj <- 3
norder <- 5
nbasis <- length(knots) + norder - 2
basis <- create.bspline.basis(norm_rng, nbasis, norder, knots)
fdPar <- fdPar(basis, Lfdobj,lambda)
# convenient aliases
basis_f0 <- basis
fdPar_f0 <- fdPar
# smooth.basis() does not accept different time samples for different curves.
# Thus we create smooth curves one by one on the same basis, store the spline coefficients and compose an fd object at the end.
f0_coefs <- matrix(nrow = nbasis, ncol = n_items)
for (id in ids) {
  t_norm <- (all_data$time_zero[all_data$id==id] / dur_f0[id]) * mean_dur_f0
  f0_coefs[,id] <- c(smooth.basis(t_norm,all_data$f0_norm[all_data$id==id],fdPar)$fd$coefs)
}
f0_fd <- fd(coef=f0_coefs, basisobj=basis)
# curves are linearly time normalized, their duration is mean_dur_f0

# plot the curves
png(paste(plots_dir,'f0_lin.png',sep=''))
plot(c(0,mean_dur_f0),c(-4,6),type='n',xlab='time (ms)',ylab='F0 (norm. semitones)',main = '',las=1,cex.axis=1.5,cex.lab=1.5)
for (id in ids) {
  lines(f0_fd[id])
}
dev.off()


# this is how the B-spline basis looks
basis_fd <- fd(diag(1,nbasis),basis)
png(paste(plots_dir,'B-splines.png',sep=''))
plot(norm_rng,c(0,1),type='n',xlab='time (s)', ylab = '', las=1,cex.axis=1.3,cex.lab=1.3)
for (b in 1:nbasis) {
  lines(basis_fd[b],col='red',lty=2)
}
points(knots,rep(0,n_knots),pch=19,col='blue')
dev.off()


# let us use these B-splines to represent the i-th curve
id <- sample(ids, 1) # select here a random curve
t_norm <- seq(0,mean_dur_f0,length.out = length(all_data$f0_norm[all_data$id==id])) 
y <- all_data$f0_norm[all_data$id==id]
y_fd <- smooth.basis(t_norm,y,fdPar)$fd
# this is how the splines combine (sum) to approximate the given curve samples
png(paste(plots_dir,'B-splines_smoothing.png',sep=''))
plot(y_fd,lwd=2,col='red',xlab='time (s)', ylab = 'norm. st', las=1,cex.axis=1.3,cex.lab=1.3)
points(t_norm,y,pch=20,col='black')
for (b in 1:nbasis) {
  lines(y_fd$coefs[b] * basis_fd[b],col='red', lty=2)
}
dev.off()


################## Functional PCA on f0 contours ########################
if (landmark) {
  y_fd <- f0reg_fd # alias
} else {
  y_fd <- f0_fd
}

# usually a good solution is obtained by setting the same lambda and knots (thus basis) used for smoothing
lambda_pca <- lambda
pcafdPar <- fdPar(basis_f0, 2, lambda_pca)
f0_pcafd <- pca.fd(y_fd, nharm=3, pcafdPar) # first three PCs

# Invert the sign of PC2, in order to facilitate global analysis, i.e. all features will increase from D to H.
# This is not necessary in general, but it can help interpreting results when multiple dimensions are involved.
# (Functional) PCA sings can always be inverted, since they have no intrinsic meaning.
f0_pcafd$harmonics$coefs[,2] <- - f0_pcafd$harmonics$coefs[,2]
f0_pcafd$scores[,2] <- - f0_pcafd$scores[,2]

# plot PC curves
if (landmark==True) {
  plot.pca.fd.corr(f0_pcafd,xlab = 'time (ms)',ylab='F0 (norm. semitones)',land = reg$land , nx=40,plots_dir = plots_dir, basename = 'PCA_f0reg_',height=480) 
} else {
  plot.pca.fd.corr(f0_pcafd,xlab = 'time (ms)',ylab='F0 (norm. semitones)', nx=40,plots_dir = plots_dir, basename = 'PCA_f0reg_',height=480) 
}

# store PC scores in data_FDA, write out to csv
data_FDA <- data
data_FDA$f0_s1 <- f0_pcafd$scores[,1]
data_FDA$f0_s2 <- f0_pcafd$scores[,2]
write.csv(paste(plots_dir, 'fpca_scores.csv'))


## FPCA-based reconstruction example (6 plots)

png(paste(plots_dir,'mean','.png',sep=''))
plot(f0_pcafd$meanfd,xlab='time (ms)',ylab='F0 (norm. semitones)',main = '',las=1,cex.axis=1.5,cex.lab=1.5,col='black',lwd=3,ylim=c(-4,5))
#abline(v=reg$land[2],lty=2,col='black',lwd=1)
#axis(3,tick=F,at=at_land, labels=landlab,cex.axis=1.5)
dev.off()


png(paste(plots_dir,'PC1','.png',sep=''))
plot(f0_pcafd$harmonics[1],xlab='time (ms)',ylab='F0 (norm. semitones)',main = '',las=1,cex.axis=1.5,cex.lab=1.5,col='black',lwd=3,)
#abline(v=reg$land[2],lty=2,col='black',lwd=1)
#axis(3,tick=F,at=at_land, labels=landlab,cex.axis=1.5)
dev.off()


png(paste(plots_dir,'PC2','.png',sep=''))
plot(f0_pcafd$harmonics[2],xlab='time (ms)',ylab='F0 (norm. semitones)',main = '',las=1,cex.axis=1.5,cex.lab=1.5,col='black',lwd=3,)
#abline(v=reg$land[2],lty=2,col='black',lwd=1)
#axis(3,tick=F,at=at_land, labels=landlab,cex.axis=1.5)
dev.off()

id <- sample(ids, 1)
png(paste(plots_dir,'reconstr_mean','.png',sep=''))
plot(f0_pcafd$meanfd,xlab='time (ms)',ylab='F0 (norm. semitones)',main = '',las=1,cex.axis=1.5,cex.lab=1.5,col='black',lwd=3,ylim=c(-4,5))
lines(y_fd[id],lwd=2, lty=2)
#abline(v=reg$land[2],lty=2,col='black',lwd=1)
#axis(3,tick=F,at=at_land, labels=landlab,cex.axis=1.5)
legend('topleft',legend=c('original','reconstruction'),lty=c(2,1),lwd=c(2,3))
dev.off()



png(paste(plots_dir,'reconstr_mean_PC1','.png',sep=''))
plot(f0_pcafd$meanfd + f0_pcafd$scores[id,1] * f0_pcafd$harmonics[1] ,xlab='time (ms)',ylab='F0 (norm. semitones)',main = '',las=1,cex.axis=1.5,cex.lab=1.5,col='black',lwd=3,ylim=c(-4,5))
lines(y_fd[id],lwd=2, lty=2)
#abline(v=reg$land[2],lty=2,col='black',lwd=1)
#axis(3,tick=F,at=at_land, labels=landlab,cex.axis=1.5)
legend('topleft',legend=c('original','reconstruction'),lty=c(2,1),lwd=c(2,3))
dev.off()


png(paste(plots_dir,'reconstr_mean_PC1_PC2','.png',sep=''))
plot(f0_pcafd$meanfd + f0_pcafd$scores[id,1] * f0_pcafd$harmonics[1] + f0_pcafd$scores[id,2] * f0_pcafd$harmonics[2],xlab='time (ms)',ylab='F0 (norm. semitones)',main = '',las=1,cex.axis=1.5,cex.lab=1.5,col='black',lwd=3,ylim=c(-4,5))
lines(y_fd[id],lwd=2, lty=2)
#abline(v=reg$land[2],lty=2,col='black',lwd=1)
#axis(3,tick=F,at=at_land, labels=landlab,cex.axis=1.5)
legend('topleft',legend=c('original','reconstruction'),lty=c(2,1),lwd=c(2,3))
dev.off()
