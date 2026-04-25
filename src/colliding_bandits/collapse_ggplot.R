args <- commandArgs(trailingOnly = TRUE)

if (length(args) < 2) {
  stop("Usage: Rscript collapse_ggplot.R <input_csv> <output_prefix>")
}

input_csv <- args[[1]]
output_prefix <- args[[2]]

suppressPackageStartupMessages({
  library(ggplot2)
  library(readr)
  library(dplyr)
})

df <- read_csv(input_csv, show_col_types = FALSE)
df <- df %>%
  filter(n > 0, m > 0, m_per_player > 0) %>%
  mutate(
    f_eps = factor(epsilon),
    f_n_arms = factor(arms),
    f_scaled_1 = factor(scaled_1),
    f_arms_over_players = factor(arms_over_players),
    f_players_over_epsilon = factor(players_over_epsilon),
    f_rho_over_epsilon = factor(rho_over_epsilon),
    f_arms_over_players_epsilon = factor(arms_over_players_epsilon),
    f_n_users = factor(players)
  )

df_binned <- df %>%
  group_by(scaled_1, epsilon, n) %>%
  summarise(
    mean_m = mean(m),
    sd_m = sd(m),
    mean_mp = mean(m_per_player),
    sd_mp = sd(m_per_player),
    repeats = n(),
    .groups = "drop"
  ) %>%
  mutate(
    se_m = if_else(repeats > 1, sd_m / sqrt(repeats), 0.0),
    se_mp = if_else(repeats > 1, sd_mp / sqrt(repeats), 0.0),
    lower_m = pmax(mean_m - 1.96 * se_m, 1e-9),
    upper_m = mean_m + 1.96 * se_m,
    lower_mp = pmax(mean_mp - 1.96 * se_mp, 1e-9),
    upper_mp = mean_mp + 1.96 * se_mp,
    f_eps = factor(epsilon),
    f_scaled_1 = factor(scaled_1)
  )

g <- ggplot(data = df, aes(x = log(n), y = log(m), colour = factor(arms))) +
  geom_point()
g <- g + facet_wrap(~ f_eps, nrow = 3)

g1 <- ggplot(data = df, aes(x = log(n), y = log(m), colour = factor(epsilon))) +
  geom_point()
g1 <- g1 + facet_wrap(~ f_n_arms, nrow = 3)

g2 <- ggplot(data = df, aes(x = log(n), y = log(m), colour = factor(epsilon))) +
  geom_point() +
  ggtitle("Numbers are arms / epsilon")
g2 <- g2 + facet_wrap(~ f_scaled_1, nrow = 8)

g3 <- ggplot(data = df, aes(x = log(n), y = log(m / players), colour = factor(epsilon))) +
  geom_point() +
  ggtitle("Numbers are arms / epsilon")
g3 <- g3 + facet_wrap(~ f_scaled_1, nrow = 8)

g4 <- ggplot(data = df_binned, aes(x = log(n), y = log(mean_m), colour = factor(epsilon), fill = factor(epsilon))) +
  geom_ribbon(aes(ymin = log(lower_m), ymax = log(upper_m)), alpha = 0.18, colour = NA) +
  geom_line() +
  geom_point(size = 1.4) +
  ggtitle("Numbers are arms / epsilon")
g4 <- g4 + facet_wrap(~ f_scaled_1, nrow = 8)

g5 <- ggplot(data = df_binned, aes(x = log(n), y = log(mean_mp), colour = factor(epsilon), fill = factor(epsilon))) +
  geom_ribbon(aes(ymin = log(lower_mp), ymax = log(upper_mp)), alpha = 0.18, colour = NA) +
  geom_line() +
  geom_point(size = 1.4) +
  ggtitle("Numbers are arms / epsilon")
g5 <- g5 + facet_wrap(~ f_scaled_1, nrow = 8)

g6 <- ggplot(data = df, aes(x = log(n), y = log(m), colour = factor(epsilon))) +
  geom_point() +
  ggtitle("Numbers are arms / players")
g6 <- g6 + facet_wrap(~ f_arms_over_players, nrow = 8)

g7 <- ggplot(data = df, aes(x = log(n), y = log(m), colour = factor(arms))) +
  geom_point() +
  ggtitle("Numbers are players / epsilon")
g7 <- g7 + facet_wrap(~ f_players_over_epsilon, nrow = 8)

g8 <- ggplot(data = df, aes(x = log(n), y = log(m), colour = factor(epsilon))) +
  geom_point() +
  ggtitle("Numbers are rho / epsilon")
g8 <- g8 + facet_wrap(~ f_rho_over_epsilon, nrow = 8)

g9 <- ggplot(data = df, aes(x = log(n), y = log(m), colour = factor(epsilon))) +
  geom_point() +
  ggtitle("Numbers are arms / (players * epsilon)")
g9 <- g9 + facet_wrap(~ f_arms_over_players_epsilon, nrow = 8)

ggsave(paste0(output_prefix, "_collapse_by_epsilon_ggplot.pdf"), plot = g, width = 12, height = 8)
ggsave(paste0(output_prefix, "_collapse_by_arms_ggplot.pdf"), plot = g1, width = 12, height = 8)
ggsave(paste0(output_prefix, "_collapse_scaled_ggplot.pdf"), plot = g2, width = 14, height = 18)
ggsave(paste0(output_prefix, "_collapse_scaled_per_player_ggplot.pdf"), plot = g3, width = 14, height = 18)
ggsave(paste0(output_prefix, "_collapse_scaled_binned_ggplot.pdf"), plot = g4, width = 14, height = 18)
ggsave(paste0(output_prefix, "_collapse_scaled_per_player_binned_ggplot.pdf"), plot = g5, width = 14, height = 18)
ggsave(paste0(output_prefix, "_collapse_arms_over_players_ggplot.pdf"), plot = g6, width = 14, height = 18)
ggsave(paste0(output_prefix, "_collapse_players_over_epsilon_ggplot.pdf"), plot = g7, width = 14, height = 18)
ggsave(paste0(output_prefix, "_collapse_rho_over_epsilon_ggplot.pdf"), plot = g8, width = 14, height = 18)
ggsave(paste0(output_prefix, "_collapse_arms_over_players_epsilon_ggplot.pdf"), plot = g9, width = 14, height = 18)

ggsave(paste0(output_prefix, "_collapse_by_epsilon_ggplot.png"), plot = g, width = 12, height = 8, dpi = 180)
ggsave(paste0(output_prefix, "_collapse_by_arms_ggplot.png"), plot = g1, width = 12, height = 8, dpi = 180)
ggsave(paste0(output_prefix, "_collapse_scaled_ggplot.png"), plot = g2, width = 14, height = 18, dpi = 180)
ggsave(paste0(output_prefix, "_collapse_scaled_per_player_ggplot.png"), plot = g3, width = 14, height = 18, dpi = 180)
ggsave(paste0(output_prefix, "_collapse_scaled_binned_ggplot.png"), plot = g4, width = 14, height = 18, dpi = 180)
ggsave(paste0(output_prefix, "_collapse_scaled_per_player_binned_ggplot.png"), plot = g5, width = 14, height = 18, dpi = 180)
ggsave(paste0(output_prefix, "_collapse_arms_over_players_ggplot.png"), plot = g6, width = 14, height = 18, dpi = 180)
ggsave(paste0(output_prefix, "_collapse_players_over_epsilon_ggplot.png"), plot = g7, width = 14, height = 18, dpi = 180)
ggsave(paste0(output_prefix, "_collapse_rho_over_epsilon_ggplot.png"), plot = g8, width = 14, height = 18, dpi = 180)
ggsave(paste0(output_prefix, "_collapse_arms_over_players_epsilon_ggplot.png"), plot = g9, width = 14, height = 18, dpi = 180)

pdf(paste0(output_prefix, "_ggplot_bundle.pdf"), width = 14, height = 10)
print(g)
print(g1)
print(g2)
print(g3)
print(g4)
print(g5)
print(g6)
print(g7)
print(g8)
print(g9)
dev.off()
