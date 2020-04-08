from numpy.random import normal, lognormal, binomial, exponential, poisson, gamma
from numpy.random import seed


from snowfakery.plugins import SnowfakeryPlugin


def wrap(distribution):
    "Wrap a numpy function to make it 1-dimensional and seedable"

    def _distribution_wrapper(self, **params):
        random_seed = params.pop("seed", None)
        seed(random_seed)
        return float(distribution(**params, size=1).astype(float)[0])

    return _distribution_wrapper


class StatisticalDistributions(SnowfakeryPlugin):
    class Functions:
        pass


for distribution in [normal, lognormal, binomial, exponential, poisson, gamma]:
    func_name = distribution.__name__
    setattr(StatisticalDistributions.Functions, func_name, wrap(distribution))
