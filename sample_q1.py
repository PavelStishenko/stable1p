from time import time
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view
from scipy.stats import levy_stable, kstest,  ecdf, describe
from scipy.interpolate import PchipInterpolator
import seaborn as sns
import matplotlib.pylab as plt


def quantile() -> float:
    """
    Returns a 0.01 quantile of a random sample of 10-days overlapping proportional returns
    """
    n = 750  # number of 1-day returns
    r = levy_stable.rvs(1.7, 0, loc=1, scale=1, size=(n,))  # 1-day returns

    # 10-days overlapping proportional returns
    r10 = np.prod(sliding_window_view(r + 1, 10), axis=1) - 1.0
    r10_ecdf = ecdf(r10).cdf # empirical CDF
    
    # monotonic interpolation of CDF from ECDF
    r10_icdf = PchipInterpolator(r10_ecdf.probabilities, r10_ecdf.quantiles)

    result = r10_icdf(0.01) 
    return result

def quantile_sample(size: int) -> np.ndarray[float]:
    """
    Generates `size` samples of 10-days overlapping proportional returns and
    returns their 0.01 quantiles
    Arguments:
            size: number of samples
    Returns:
            0.01 quantiles
    """
    return np.array([quantile() for i in range(size)])

def main():
    np.random.seed(1234)
    # Stage 1. Mean value estimaion
    N = 1000
    print("Estimating 0.01 quantile value by Monte Carlo sampling")
    print(f"Size of samples: {N}")
    print(f"Sample average   Sample stdev  Est. stdev of average   95% confidence interval ")
    for i in range(10):
        s = quantile_sample(N)
        mean_est = np.mean(s)           # sample mean
        std_est = np.std(s)             # sample std
        mean_std_est = std_est / (N**0.5)   # estimation of mean std
        print(f"{mean_est:14.2f} {std_est:14.2f} {mean_std_est:22.2f}    ({mean_est - 2*mean_std_est:.2f}, {mean_est + 2*mean_std_est:.2f})" )
    sns.histplot(s, stat="density")

    # Stage 2. 1-sided K-S test against fitted stable distribution
    x_grid = np.linspace(np.min(s), np.max(s), 1000) # x grid for PDF plot
    for n_fit in [10,  30,  100, 300, 1000, 3000, 10000]:
        s = quantile_sample(n_fit)
        print("Fitting...")
        t0 = time()
        params = levy_stable.fit(s)
        print(f"Fitting...done in {time()-t0:.2f} sec\n    params:", params)
        res = kstest(s, levy_stable.cdf, args=params)
        print(f"    K-S test for {n_fit=}: p-value={res.pvalue:.4} statistic={res.statistic:.4}")
        plt.plot(x_grid, levy_stable(*params).pdf(x_grid), label=f'{n_fit=} p-value={res.pvalue:.2} max CDF error={res.statistic:.2}')

    print("Plotting...")    
    plt.legend()
    plt.xlim( (mean_est - 3 * std_est, 0) )
    plt.savefig('hist_fit.svg')
    plt.show()

    # Stage 3. 2-sided K-S test
    np.random.seed(1234)
    for n_fit in [10,  30,  100, 300, 1000, 3000, 10000, 30_000, 100_000]:
        s1 = quantile_sample(n_fit)
        s2 = quantile_sample(n_fit)
        res = kstest(s1, s2)
        print(f"    K-S test for {n_fit=}: p-value={res.pvalue:.4} statistic={res.statistic:.4}")



if __name__ == "__main__":
    main()
