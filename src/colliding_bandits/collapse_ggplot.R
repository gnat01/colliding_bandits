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
    f_n_users = factor(players)
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

ggsave(paste0(output_prefix, "_collapse_by_epsilon_ggplot.pdf"), plot = g, width = 12, height = 8)
ggsave(paste0(output_prefix, "_collapse_by_arms_ggplot.pdf"), plot = g1, width = 12, height = 8)
ggsave(paste0(output_prefix, "_collapse_scaled_ggplot.pdf"), plot = g2, width = 14, height = 18)
ggsave(paste0(output_prefix, "_collapse_scaled_per_player_ggplot.pdf"), plot = g3, width = 14, height = 18)

ggsave(paste0(output_prefix, "_collapse_by_epsilon_ggplot.png"), plot = g, width = 12, height = 8, dpi = 180)
ggsave(paste0(output_prefix, "_collapse_by_arms_ggplot.png"), plot = g1, width = 12, height = 8, dpi = 180)
ggsave(paste0(output_prefix, "_collapse_scaled_ggplot.png"), plot = g2, width = 14, height = 18, dpi = 180)
ggsave(paste0(output_prefix, "_collapse_scaled_per_player_ggplot.png"), plot = g3, width = 14, height = 18, dpi = 180)

pdf(paste0(output_prefix, "_ggplot_bundle.pdf"), width = 14, height = 10)
print(g)
print(g1)
print(g2)
print(g3)
dev.off()
