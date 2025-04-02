import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import csv
from scipy.stats import truncnorm

# Uncomment the following line if you experience backend issues (e.g., in PyCharm)
# matplotlib.use('TkAgg')  # or 'Qt5Agg'

# --- Simulation Parameters ---
n_ticks = 20
start_price = 10.0
tick_change = 0.50


# Transition probabilities for the Markov chain:
#   If previous movement was Up:   P(up)=0.90, P(down)=0.10
#   If previous movement was Down: P(up)=0.10, P(down)=0.90
def simulate_markov_chain(n_ticks, start_price, tick_change):
    prices = [start_price]
    # Choose initial direction unbiasedly
    prev_state = np.random.choice([1, 0], p=[0.5, 0.5])  # 1 = Up, 0 = Down
    for _ in range(1, n_ticks + 1):
        if prev_state == 1:
            state = np.random.choice([1, 0], p=[0.90, 0.10])
        else:
            state = np.random.choice([1, 0], p=[0.10, 0.90])
        if state == 1:
            new_price = prices[-1] + tick_change
        else:
            new_price = prices[-1] - tick_change
        prices.append(new_price)
        prev_state = state
    return prices

'''
# Noise distribution (discrete):
#   20% chance of ±0.40, 20% chance of ±0.60, 10% chance of ±0.80
noise_values = [0.40, -0.40, 0.60, -0.60, 0.80, -0.80]
noise_probs = [0.20, 0.20, 0.20, 0.20, 0.10, 0.10]
'''

# Truncated normal distribution
a, b = -0.80, 0.80
mu, sigma = 0, 1
trunc_dist = truncnorm(a, b, loc=mu, scale=sigma)

samples = trunc_dist.rvs(1000)

plt.hist(samples, bins=30, density=True, alpha=0.6, color='skyblue', edgecolor='black')
plt.title("Truncated Normal Distribution")
plt.xlabel("Value")
plt.ylabel("Density")
plt.show()

# Define the detection threshold for observed price movement (per tick)
trend_threshold = 0.80

# Generate and save 6 different paths
for i in range(1, 7):
    # Set a distinct random seed for reproducibility
    np.random.seed(42 + i)

    # 1) Generate the underlying price (no noise)
    underlying_prices = simulate_markov_chain(n_ticks, start_price, tick_change)

    # 2) Sample noise and create the observed price series
    # noise = np.random.choice(noise_values, size=n_ticks, p=noise_probs)
    noise = trunc_dist.rvs(n_ticks)  # Sample from the truncated normal distribution
    observed_prices = [underlying_prices[0]]
    for t in range(1, len(underlying_prices)):
        observed_prices.append(underlying_prices[t] + noise[t - 1])

    # 3) Identify ticks where the observed and underlying direction disagree
    opposite_ticks = []
    for t in range(1, n_ticks + 1):
        under_diff = underlying_prices[t] - underlying_prices[t - 1]
        obs_diff = observed_prices[t] - observed_prices[t - 1]
        if np.sign(under_diff) != np.sign(obs_diff):
            opposite_ticks.append(t)

    # 4) Identify "detectable" ticks based on observed price change (from previous tick)
    detectable_ticks = [t for t in range(1, n_ticks + 1)
                        if abs(observed_prices[t] - observed_prices[t - 1]) > trend_threshold]
    # If a tick is both "detectable" and "opposite", we'll show it as black (opposite dots override detectable dots)
    detectable_only = [t for t in detectable_ticks if t not in opposite_ticks]

    # 5) Plot and save the figure
    ticks = np.arange(n_ticks + 1)
    plt.figure(figsize=(12, 6))

    # Left subplot: Underlying price (no noise)
    plt.subplot(1, 2, 1)
    plt.plot(ticks, underlying_prices, marker='o', linestyle='-', label='Underlying Price')
    plt.title("Underlying Price Evolution (No Noise)")
    plt.xlabel("Tick")
    plt.ylabel("Price ($)")
    plt.grid(True)
    plt.legend()

    # Right subplot: Observed price (with noise)
    plt.subplot(1, 2, 2)
    plt.plot(ticks, observed_prices, marker='o', linestyle='-', color='red', label='Observed Price')
    # Mark opposite ticks (black dots)
    if opposite_ticks:
        plt.scatter(opposite_ticks, [observed_prices[t] for t in opposite_ticks],
                    marker='o', color='black', s=100, label='Opposite Movement')
    # Mark detectable (but not opposite) ticks (green dots)
    if detectable_only:
        plt.scatter(detectable_only, [observed_prices[t] for t in detectable_only],
                    marker='o', color='green', s=100, label='Detectable Movement')

    plt.title("Observed Price Evolution (With Noise)")
    plt.xlabel("Tick")
    plt.ylabel("Price ($)")
    plt.grid(True)
    plt.legend()

    plt.tight_layout()
    plt.savefig(f"graph{i}.png")
    plt.close()

    # 6) Save the data (underlying + observed) to a CSV file
    with open(f"data{i}.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Tick", "UnderlyingPrice", "ObservedPrice"])
        for t in range(n_ticks + 1):
            writer.writerow([t, underlying_prices[t], observed_prices[t]])

    print(f"Generated graph{i}.png and data{i}.csv")
