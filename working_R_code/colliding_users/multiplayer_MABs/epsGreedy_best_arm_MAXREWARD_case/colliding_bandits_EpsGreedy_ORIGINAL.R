# Simple N bandit problem - with N levers #

# Premise : Think of the musical chair bandits paper and a neater model


# All users have access to the same N levers (arms)
# At each time step, a users pushes one of N arms ; its payoff is the number of colliding users in
# the following way : if k users choose an action, payoff = 1/k for that action for those users

# What happens in the long term?

require(dplyr)
require(ggplot2)
require(readr)
require(purrr)
require(tidyverse)

decsort <- function(x) {sort(x, decreasing = TRUE)}

incsort <- function(x) {sort(x)}

maxpos <- function(x) {
  candidates <- which(x == max(x))
  # if there is more than one best arm, we pick randomly
  
  if (length(candidates) > 1) {
    best <- sample(candidates, 1, replace = F)
  } else {
    best <- candidates
  }
  return(best)
  
}

best_arms <- function(perf_t) {
  ba <- apply(perf_t, 1, maxpos) # for every user -- which arm fared the best?
  return(ba)
}

best_arms_metrics <- function(ba) {
  bat <- as_tibble(ba)
  
  ba_counts <- bat %>%
    group_by(value) %>%
    summarise(n = n())
  
  return(ba_counts)
}

explore <- function(n_users, n_arms, explore_phase) {
  
  m <- matrix(rep(0.0, n_users*n_arms), ncol = n_arms)
  
  mdf <- as.data.frame(m)
  
  perf_t <- as_tibble(mdf)
  
  # for fun, we SHUFFLE arm numbers
  #perf_t <- as_tibble(perf_df)
  
  # keep a tally of what arms were picked in this phase
  
  #chosen_arms <- numeric(length = n_users*explore_phase)
  
  for (explore_time in 1:explore_phase) {
    
    cat("explore time :", explore_time, "\n")
    # kill the chance of biases by shuffling arms string every single time
    choices <- sample(sample(n_arms, n_arms, replace = F), n_users, replace = T) # for each user -- sample from the set of arms
    
    #chosen_arms[(explore_time-1)*n_arms+1:(explore_time-1)*n_arms+n_arms] <- choices
    
    choices_t<- as_tibble(choices)
    
    payoff <- choices_t %>%
      group_by(value) %>%
      summarise(n = n()) %>%
      mutate(pay = 1.0 / n) # our payoff is simply inversely proportional to the number of colliding users
    
    join1 <- inner_join(choices_t, payoff, by=c("value"))
    
    for (u in 1:n_users) {
      update_arm <- as.numeric(join1[u,1]) # the value
      pay_arm <- as.numeric(join1[u,3]) #the pay
      
      perf_t[u,update_arm] <- perf_t[u,update_arm] + pay_arm
    }
    
  } # exploration phase 
  
  # done with exploration -- we should return the full perf tibble
  
  #l <- list(perf_t = perf_t, chosen_arms = chosen_arms)
  l <- list(perf_t = perf_t)
  
  return(l)
}

epsgreedy <- function(n_users, n_arms, tot_tries, perf_t, ba, eps) { # the performance for each user, arm pair
  # and each user's best arm
  
  seq_arms <- c(1:n_arms)
  n_arms_1 <- n_arms - 1
  prob_exploit <- 1.0 - eps
  
  proba_list <- list()
  
  for (u in 1:n_users) {
    proba <- rep(0, n_arms)
    proba[ba[u]] <- prob_exploit # we pick our best arm with this probability
    proba[proba != prob_exploit] <- eps / (n_arms_1) # or explore all other arms with an equal probability
    proba_list[[u]] <- proba # store in a list
  }
  
  m <- matrix(rep(0, n_arms*tot_tries), ncol = n_arms)
  
  arm_dist_df <- as.data.frame(m)
  
  for (t in 1:tot_tries) {
    
    cat("eps greedy time :", t, "\n")
    
    # get the arm for each user
    
    choices <- rep(0, n_users) 
    
    for (u in 1:n_users) {
      choices[u] <- sample(n_arms, 1, replace = F, prob = proba_list[[u]])  
    }
    
#    choices <- sample(n_arms, n_users, replace = T) # for each user -- sample from the set of arms
    
    choices_t<- as_tibble(choices)
    
    payoff <- choices_t %>%
      group_by(value) %>%
      summarise(n = n()) %>%
      mutate(pay = 1.0 / n) # our payoff is simply inversely proportional to the number of colliding users
    
    pv <- as.numeric(payoff$value)
    #pn <- as.numeric(payoff$n)
    for (j in pv) {
    arm_dist_df[t,j] <-  as.numeric(payoff$n[payoff$value == j])# look at arm distributions now
    }
    
    join1 <- inner_join(choices_t, payoff, by=c("value"))
    
    for (u in 1:n_users) {
      update_arm <- as.numeric(join1[u,1]) # the value
      pay_arm <- as.numeric(join1[u,3]) #the pay
      
      perf_t[u,update_arm] <- perf_t[u,update_arm] + pay_arm
    }
    
  } # exploration phase 
  
  arm_dist_t <- as_tibble(arm_dist_df)
  
  # done with exploration -- we should return the full perf tibble and the arm distributions at each step
  l <- list(perf_t = perf_t, arm_dist_t = arm_dist_t)
  return(l)
}

final_payoffs <- function(final_perf_t) {
  
  payoff <- apply(final_perf_t, 1, max)
  payoff_maxpos <- apply(final_perf_t, 1, maxpos)
  
  df <- data.frame(payoff_maxpos = payoff_maxpos, payoff = payoff)
  dft <- as_tibble(df)
  
  return(dft)
  
}

mean_sd_final_payoffs <- function(final_payoff_t) {
  mean_sd_final_payoff_t <- final_payoff_t %>%
  group_by(payoff_maxpos) %>%
  summarise(m = mean(payoff), s = sd(payoff))
  
  colnames(mean_sd_final_payoff_t)[1] <- c("value")
  
  return(mean_sd_final_payoff_t)
}

compute_join <- function(mean_sd_final_payoff_t, ba_metrics, n_arms, eps) {
  
  join2 <- inner_join(mean_sd_final_payoff_t, ba_metrics, by=c("value"))
  
  join2$n_arms <- n_arms
  
  join2$eps <- eps
  
  return(join2)
  
}

join_plot <- function(join2) {
  join2 %>%
    ggplot(aes(x = n, y = m)) + geom_point(colour = "red") + geom_line(colour = "black")
  
}

initialise <- function(arms_loop, users, exploreph, tries, eps_loop, single_run = TRUE) {
  
  if (single_run) {
    arms <- arms_loop[1]
    eps <- eps_loop[1]
  } else {
    arms <- arms_loop
    eps <- eps_loop
  }
  
  users <- users
  exploreph <- exploreph
  tries <- tries
  
  return(list(arms = arms, eps = eps, users = users, exploreph = exploreph, tries = tries))
  
}

# Initialize
n_users <- 101

explore_phase <- 100

tot_tries <- 1000 # total time = tot_tries + explore_phase

n_arms_loop <- c(5, 10, 20, 30, 40, 50, 100, 200)

#n_arms_loop <- c(5)

#n_arms <- 50
seq_arms <- c(1:n_arms)

eps_loop <- c(0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9)

#eps_loop <- c(0.1)

dfl <- length(eps_loop) * length(n_arms_loop) * n_users

final_join2 <- data.frame(value = rep(NA, dfl),
                          m = rep(NA, dfl),
                          s = rep(NA, dfl),
                          n = rep(NA, dfl),
                          eps = rep(NA, dfl),
                          n_arms = rep(NA, dfl))

final_join2_t <- as_tibble(final_join2)

ctr <- 1
# Main functionality --- #

for (n_arms in n_arms_loop) {

  cat("Num arms : ", n_arms, "\n\n\n")
  
for (eps in eps_loop) {
  
# exploration perf tibble
l11 <- explore(n_users, n_arms, explore_phase)

perf_t <- l11[[1]]
#chosen_arms <- l11[[2]]

# best arms for each user
ba <- best_arms(perf_t)

# metrics around the exploration phase

ba_metrics <- best_arms_metrics(ba)

# epsilon-greedy algo for the next bit

l1 <- epsgreedy(n_users, n_arms, tot_tries, perf_t, ba, eps)

final_perf_t <- l1[[1]]
final_arm_dist_t <- l1[[2]]

# now we are done w/ the eps greedy learning - what are the best arms with their metrics?

final_ba <- best_arms(final_perf_t)
final_ba_metrics <- best_arms_metrics(final_ba)

# what do the total earnings / payoffs per player look like?  

final_payoff_t <- final_payoffs(final_perf_t)

# by arm, compute mean and sd of the payoffs

mean_sd_final_payoff_t <- mean_sd_final_payoffs(final_payoff_t)

# a simple plot -- for the join -- we consider the final metrics on the best arms and their usage
join2 <- compute_join(mean_sd_final_payoff_t, final_ba_metrics, n_arms, eps)

if (ctr == 1) {
  final_join2_t <- rbind(join2)
} else {
  final_join2_t <- rbind(final_join2_t, join2)
}

ctr <- ctr + 1

} # eps loop 

# remove NAs
  
final_join2_t <- final_join2_t[complete.cases(final_join2_t), ]
  
# plot
#final_join2_t %>%
#  ggplot(aes(x = log(n), y = log(m), colour = factor(eps))) + geom_point() + geom_line()

# group by the arm index

#final_join2_t %>%
#  ggplot(aes(x = n, y = m, colour = factor(value))) + geom_point() + geom_line()

cat("DONE WITH num arms : ", n_arms, "\n\n\n")

} # n_arms loop

# comprehesensive plots - by arms, for all eps ; then by eps for all arms

# 1 : by eps

final_join2_t_by_eps <- split(final_join2_t, factor(final_join2_t$eps))

# 2 : by arms

final_join2_t_by_n_arms <- split(final_join2_t, factor(final_join2_t$n_arms))

# Plot ( each plot is a different eps value )

f <- subset(final_join2_t, eps == 0.1)
g <- ggplot(data = f, aes(x = log(n), y = log(m), colour = factor(n_arms))) + 
  geom_point() + geom_line()

#g <- g + facet_wrap(~ factor(eps), nrow  = 2)

print(g)

# to make facet_grid work
f <- final_join2_t
f$f_eps <- factor(f$eps)

final_join2_t$f_eps <- factor(final_join2_t$eps)
final_join2_t$f_n_arms <- factor(final_join2_t$n_arms)

#g <- ggplot(data = final_join2_t, aes(x = n, y = m, colour = factor(n_arms))) + 
#  geom_point() + geom_line()

#g <- g + facet_grid(f_eps ~ .)
#print(g)

# try facet_wrap

g <- ggplot(data = final_join2_t, aes(x = log(n), y = log(m), colour = factor(n_arms))) + 
  geom_point() 

g <- g + facet_wrap(~ f_eps, nrow = 3)
print(g)

g1 <- ggplot(data = final_join2_t, aes(x = log(n), y = log(m), colour = factor(eps))) +
  geom_point()

g1 <- g1 + facet_wrap(~ f_n_arms, nrow = 3)
print(g1)

# save data
write_csv(final_join2_t, "/Users/girishnathan/work/code/R/musical_chair_bandit_variations/101_players_best_arm_rewards_full.csv",
         col_names = T)

# save all plots

pdf("/Users/girishnathan/work/code/R/musical_chair_bandit_variations/101_players_best_arm_rewards_plots_full.pdf")
g <- ggplot(data = final_join2_t, aes(x = log(n), y = log(m), colour = factor(n_arms))) + 
  geom_point() 

g <- g + facet_wrap(~ f_eps, nrow = 3)
print(g)

g1 <- ggplot(data = final_join2_t, aes(x = log(n), y = log(m), colour = factor(eps))) +
  geom_point()

g1 <- g1 + facet_wrap(~ f_n_arms, nrow = 3)
print(g1)
dev.off()

