### Pigeonhole multiplayer - colliding users #'

library(ggplot2)

N <- seq(2, 15, by=1) # users 
M <- seq(2, 15, by=1) # arms

len_N <- length(N)
len_M <- length(M)

len1 <- len_N * len_M

per_round_reward_df <- data.frame(
  num_users = rep(-1, len1),
  num_arms = rep(-1, len1),
  per_round_reward = rep(-1, len1)
)

ctr <- 1

for (n in N) {
  for (m in M) {
    
    fv <- floor(n / m)
    
    if (fv == 0) { # num users < num arms
      reward <- 1 # per user per round
      tot_reward <- reward * N
    } else if (fv > 1) {
      reward <- 0
      tot_reward <- 0
    } else if (fv == 1) {
      if (m == n) {
        reward <- 1
        tot_reward <- reward * N
      } else {
        reward <- 1
        tot_reward <- reward * (m - m + m * fv)
      }
    }
    
    per_round_reward_df[ctr,1] <- n
    per_round_reward_df[ctr,2] <- m
    per_round_reward_df[ctr,3] <- tot_reward
    
    ctr <- ctr + 1
    
  }
}

