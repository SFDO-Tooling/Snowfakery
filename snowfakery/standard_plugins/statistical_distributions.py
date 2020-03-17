from numpy.random import normal, lognormal, binomial, exponential, poisson, gamma
from numpy.random import seed


from snowfakery.plugins import SnowfakeryPlugin


def wrap(distribution):
    def _do_distribution(self, **params):
        random_seed = params.pop("seed", None)
        seed(random_seed)
        return float(distribution(**params, size=1).astype(float)[0])
        # except (TypeError, DataGenValueError, DataGenError):
        #     raise DataGenError(
        #         f"Incorrect parameters {params} for {distribution.__name__} distribution.",
        #         None, None,
        #     )

    return _do_distribution


class StatisticalDistributions(SnowfakeryPlugin):
    class Functions:
        pass


for distribution in [normal, lognormal, binomial, exponential, poisson, gamma]:
    func_name = distribution.__name__
    setattr(StatisticalDistributions.Functions, func_name, wrap(distribution))
