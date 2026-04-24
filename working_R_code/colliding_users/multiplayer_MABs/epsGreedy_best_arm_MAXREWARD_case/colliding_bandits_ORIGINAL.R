# Simple N bandit problem - with N levers #

# Premise : Think of the musical chair bandits paper and a neater model

# All users have access to the same N levers (arms)
# At each time step, a users pushes one of N arms ; its payoff is the number of colliding users in
# the following way : if k users choose an action, payoff = 1/k for that action for those users

# What happens in the long term?

decsort <- function(x) {sort(x, decreasing = TRUE)}

incsort <- function(x) {sort(x)}

maxpos <- function(x) {
  candidates <- which(x == max(x))
  # if there is more than one best arm, we pick randomly
  
  best <- sample(candidates, 1, replace = F)
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
  
  for (explore_time in 1:explore_phase) {
    
    cat("explore time :", explore_time, "\n")
    # kill the chance of biases by shuffling arms string every single time
    choices <- sample(sample(n_arms, n_arms, replace = F), n_users, replace = T) # for each user -- sample from the set of arms
    
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
  return(perf_t)
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

final_payoffs <- function(final_perf_t, ba) {
  
  payoff <- apply(final_perf_t, 1, max)
  
  df <- data.frame(ba = ba, payoff = payoff)
  dft <- as_tibble(df)
  
  return(dft)
  
}

mean_sd_final_payoffs <- function(final_payoff_t) {
  mean_sd_final_payoff_t <- final_payoff_t %>%
  group_by(ba) %>%
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

tot_tries <- 900 # total time = tot_tries + explore_phase

n_arms_loop <- c(5, 10, 20, 30, 40, 50, 100, 200)

n_arms <- n_arms_loop[1] # test

seq_arms <- c(1:n_arms)

eps_loop <- c(0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9)

#eps <- eps_loop[1]

dfl <- length(eps_loop) * n_arms

final_join2 <- data.frame(value = rep(NA, dfl),
                          m = rep(NA, dfl),
                          s = rep(NA, dfl),
                          n = rep(NA, dfl),
                          eps = rep(NA, dfl))

final_join2_t <- as_tibble(final_join2)

ctr <- 1
# Main functionality --- #


for (eps in eps_loop) {
  
# exploration perf tibble
perf_t <- explore(n_users, n_arms, explore_phase)

# best arms for each user
ba <- best_arms(perf_t)

# metrics around the exploration phase

ba_metrics <- best_arms_metrics(ba)

# epsilon-greedy algo for the next bit

l1 <- epsgreedy(n_users, n_arms, tot_tries, perf_t, ba, eps)

final_perf_t <- l1[[1]]
final_arm_dist_t <- l1[[2]]

# what do the total earnings / payoffs per player look like?  

final_payoff_t <- final_payoffs(final_perf_t, ba)

# by arm, compute mean and sd of the payoffs

mean_sd_final_payoff_t <- mean_sd_final_payoffs(final_payoff_t)

# a simple plot
join2 <- compute_join(mean_sd_final_payoff_t, ba_metrics, n_arms, eps)

if (ctr == 1) {
  final_join2_t <- rbind(join2)
} else {
  final_join2_t <- rbind(final_join2_t, join2)
}

ctr <- ctr + 1

}

# plot
final_join2_t %>%
  ggplot(aes(x = n, y = m, colour = factor(eps))) + geom_point() + geom_line()

# group by the arm index

final_join2_t %>%
  ggplot(aes(x = n, y = m, colour = factor(value))) + geom_point() + geom_line()

