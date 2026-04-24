# Plot data #

require(dplyr)
require(ggplot2)

filenames <- list.files("/Users/girishnathan/work/code/R/colliding_bandits",
                       pattern = "*best_arm_rewards_full_2_explore_dep_arms.csv",
                       full.names = T)

listOfFiles <- lapply(filenames, read.csv)

# omit 101 for now

ll <- rbind(listOfFiles[[1]], listOfFiles[[3]])

len_list <- length(listOfFiles)

for (i in 4:len_list) {
  ll <- rbind(ll, listOfFiles[[i]])
}

g3 <- ggplot(data = ll, aes(x = log(n), y = log(m), colour = factor(n_users))) + geom_point() + ggtitle("Numbers are n_arms / eps")
g3 <- g3 + facet_wrap(~ f_scaled_1, nrow = 8)
print(g3)

g4 <- ggplot(data = ll, aes(x = log(n), y = log(m/n_users), colour = factor(n_users))) + geom_point() + ggtitle("Numbers are n_arms / eps")
g4 <- g4 + facet_wrap(~ f_scaled_1, nrow = 8)
print(g4)






