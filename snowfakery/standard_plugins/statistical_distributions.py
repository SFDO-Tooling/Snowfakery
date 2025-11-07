from numpy.random import normal, lognormal, binomial, exponential, poisson, gamma
from numpy.random import seed


from snowfakery.plugins import SnowfakeryPlugin
from snowfakery.utils.validation_utils import resolve_value


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

    class Validators:
        """Validators for StatisticalDistributions plugin functions."""

        @staticmethod
        def _validate_seed(sv, context, kwargs):
            """Validate seed parameter (common to all distributions)."""
            if "seed" in kwargs:
                seed_val = resolve_value(kwargs["seed"], context)

                if seed_val is not None and not isinstance(seed_val, int):
                    context.add_error(
                        f"{sv.function_name}: 'seed' must be an integer, got {type(seed_val).__name__}",
                        getattr(sv, "filename", None),
                        getattr(sv, "line_num", None),
                    )

        @staticmethod
        def validate_normal(sv, context):
            """Validate StatisticalDistributions.normal(loc=0.0, scale=1.0, seed=None)"""
            kwargs = getattr(sv, "kwargs", {})

            # Validate loc
            if "loc" in kwargs:
                loc_val = resolve_value(kwargs["loc"], context)

                if loc_val is not None and not isinstance(loc_val, (int, float)):
                    context.add_error(
                        f"StatisticalDistributions.normal: 'loc' must be numeric, got {type(loc_val).__name__}",
                        getattr(sv, "filename", None),
                        getattr(sv, "line_num", None),
                    )

            # Validate scale
            if "scale" in kwargs:
                scale_val = resolve_value(kwargs["scale"], context)

                if scale_val is not None:
                    if not isinstance(scale_val, (int, float)):
                        context.add_error(
                            f"StatisticalDistributions.normal: 'scale' must be numeric, got {type(scale_val).__name__}",
                            getattr(sv, "filename", None),
                            getattr(sv, "line_num", None),
                        )
                    elif scale_val <= 0:
                        context.add_error(
                            "StatisticalDistributions.normal: 'scale' must be positive",
                            getattr(sv, "filename", None),
                            getattr(sv, "line_num", None),
                        )

            # Validate seed
            StatisticalDistributions.Validators._validate_seed(sv, context, kwargs)

            # WARNING: Unknown parameters
            valid_params = {"loc", "scale", "seed"}
            unknown = set(kwargs.keys()) - valid_params
            if unknown:
                context.add_warning(
                    f"StatisticalDistributions.normal: Unknown parameter(s): {', '.join(unknown)}",
                    getattr(sv, "filename", None),
                    getattr(sv, "line_num", None),
                )

        @staticmethod
        def validate_lognormal(sv, context):
            """Validate StatisticalDistributions.lognormal(mean=0.0, sigma=1.0, seed=None)"""
            kwargs = getattr(sv, "kwargs", {})

            # Validate mean
            if "mean" in kwargs:
                mean_val = resolve_value(kwargs["mean"], context)

                if mean_val is not None and not isinstance(mean_val, (int, float)):
                    context.add_error(
                        f"StatisticalDistributions.lognormal: 'mean' must be numeric, got {type(mean_val).__name__}",
                        getattr(sv, "filename", None),
                        getattr(sv, "line_num", None),
                    )

            # Validate sigma
            if "sigma" in kwargs:
                sigma_val = resolve_value(kwargs["sigma"], context)

                if sigma_val is not None:
                    if not isinstance(sigma_val, (int, float)):
                        context.add_error(
                            f"StatisticalDistributions.lognormal: 'sigma' must be numeric, got {type(sigma_val).__name__}",
                            getattr(sv, "filename", None),
                            getattr(sv, "line_num", None),
                        )
                    elif sigma_val <= 0:
                        context.add_error(
                            "StatisticalDistributions.lognormal: 'sigma' must be positive",
                            getattr(sv, "filename", None),
                            getattr(sv, "line_num", None),
                        )

            # Validate seed
            StatisticalDistributions.Validators._validate_seed(sv, context, kwargs)

            # WARNING: Unknown parameters
            valid_params = {"mean", "sigma", "seed"}
            unknown = set(kwargs.keys()) - valid_params
            if unknown:
                context.add_warning(
                    f"StatisticalDistributions.lognormal: Unknown parameter(s): {', '.join(unknown)}",
                    getattr(sv, "filename", None),
                    getattr(sv, "line_num", None),
                )

        @staticmethod
        def validate_binomial(sv, context):
            """Validate StatisticalDistributions.binomial(n, p, seed=None)"""
            kwargs = getattr(sv, "kwargs", {})

            # ERROR: Required parameters
            if "n" not in kwargs:
                context.add_error(
                    "StatisticalDistributions.binomial: Missing required parameter 'n'",
                    getattr(sv, "filename", None),
                    getattr(sv, "line_num", None),
                )
            if "p" not in kwargs:
                context.add_error(
                    "StatisticalDistributions.binomial: Missing required parameter 'p'",
                    getattr(sv, "filename", None),
                    getattr(sv, "line_num", None),
                )

            # Validate n
            if "n" in kwargs:
                n_val = resolve_value(kwargs["n"], context)

                if n_val is not None:
                    if not isinstance(n_val, int):
                        context.add_error(
                            f"StatisticalDistributions.binomial: 'n' must be an integer, got {type(n_val).__name__}",
                            getattr(sv, "filename", None),
                            getattr(sv, "line_num", None),
                        )
                    elif n_val <= 0:
                        context.add_error(
                            "StatisticalDistributions.binomial: 'n' must be positive",
                            getattr(sv, "filename", None),
                            getattr(sv, "line_num", None),
                        )

            # Validate p
            if "p" in kwargs:
                p_val = resolve_value(kwargs["p"], context)

                if p_val is not None:
                    if not isinstance(p_val, (int, float)):
                        context.add_error(
                            f"StatisticalDistributions.binomial: 'p' must be numeric, got {type(p_val).__name__}",
                            getattr(sv, "filename", None),
                            getattr(sv, "line_num", None),
                        )
                    elif not (0.0 <= p_val <= 1.0):
                        context.add_error(
                            f"StatisticalDistributions.binomial: 'p' must be between 0.0 and 1.0, got {p_val}",
                            getattr(sv, "filename", None),
                            getattr(sv, "line_num", None),
                        )

            # Validate seed
            StatisticalDistributions.Validators._validate_seed(sv, context, kwargs)

            # WARNING: Unknown parameters
            valid_params = {"n", "p", "seed"}
            unknown = set(kwargs.keys()) - valid_params
            if unknown:
                context.add_warning(
                    f"StatisticalDistributions.binomial: Unknown parameter(s): {', '.join(unknown)}",
                    getattr(sv, "filename", None),
                    getattr(sv, "line_num", None),
                )

        @staticmethod
        def validate_exponential(sv, context):
            """Validate StatisticalDistributions.exponential(scale=1.0, seed=None)"""
            kwargs = getattr(sv, "kwargs", {})

            # Validate scale
            if "scale" in kwargs:
                scale_val = resolve_value(kwargs["scale"], context)

                if scale_val is not None:
                    if not isinstance(scale_val, (int, float)):
                        context.add_error(
                            f"StatisticalDistributions.exponential: 'scale' must be numeric, got {type(scale_val).__name__}",
                            getattr(sv, "filename", None),
                            getattr(sv, "line_num", None),
                        )
                    elif scale_val <= 0:
                        context.add_error(
                            "StatisticalDistributions.exponential: 'scale' must be positive",
                            getattr(sv, "filename", None),
                            getattr(sv, "line_num", None),
                        )

            # Validate seed
            StatisticalDistributions.Validators._validate_seed(sv, context, kwargs)

            # WARNING: Unknown parameters
            valid_params = {"scale", "seed"}
            unknown = set(kwargs.keys()) - valid_params
            if unknown:
                context.add_warning(
                    f"StatisticalDistributions.exponential: Unknown parameter(s): {', '.join(unknown)}",
                    getattr(sv, "filename", None),
                    getattr(sv, "line_num", None),
                )

        @staticmethod
        def validate_poisson(sv, context):
            """Validate StatisticalDistributions.poisson(lam, seed=None)"""
            kwargs = getattr(sv, "kwargs", {})

            # ERROR: Required parameter
            if "lam" not in kwargs:
                context.add_error(
                    "StatisticalDistributions.poisson: Missing required parameter 'lam'",
                    getattr(sv, "filename", None),
                    getattr(sv, "line_num", None),
                )
                return

            # Validate lam
            lam_val = resolve_value(kwargs["lam"], context)

            if lam_val is not None:
                if not isinstance(lam_val, (int, float)):
                    context.add_error(
                        f"StatisticalDistributions.poisson: 'lam' must be numeric, got {type(lam_val).__name__}",
                        getattr(sv, "filename", None),
                        getattr(sv, "line_num", None),
                    )
                elif lam_val <= 0:
                    context.add_error(
                        "StatisticalDistributions.poisson: 'lam' must be positive",
                        getattr(sv, "filename", None),
                        getattr(sv, "line_num", None),
                    )

            # Validate seed
            StatisticalDistributions.Validators._validate_seed(sv, context, kwargs)

            # WARNING: Unknown parameters
            valid_params = {"lam", "seed"}
            unknown = set(kwargs.keys()) - valid_params
            if unknown:
                context.add_warning(
                    f"StatisticalDistributions.poisson: Unknown parameter(s): {', '.join(unknown)}",
                    getattr(sv, "filename", None),
                    getattr(sv, "line_num", None),
                )

        @staticmethod
        def validate_gamma(sv, context):
            """Validate StatisticalDistributions.gamma(shape, scale, seed=None)"""
            kwargs = getattr(sv, "kwargs", {})

            # ERROR: Required parameters
            if "shape" not in kwargs:
                context.add_error(
                    "StatisticalDistributions.gamma: Missing required parameter 'shape'",
                    getattr(sv, "filename", None),
                    getattr(sv, "line_num", None),
                )
            if "scale" not in kwargs:
                context.add_error(
                    "StatisticalDistributions.gamma: Missing required parameter 'scale'",
                    getattr(sv, "filename", None),
                    getattr(sv, "line_num", None),
                )

            # Validate shape
            if "shape" in kwargs:
                shape_val = resolve_value(kwargs["shape"], context)

                if shape_val is not None:
                    if not isinstance(shape_val, (int, float)):
                        context.add_error(
                            f"StatisticalDistributions.gamma: 'shape' must be numeric, got {type(shape_val).__name__}",
                            getattr(sv, "filename", None),
                            getattr(sv, "line_num", None),
                        )
                    elif shape_val <= 0:
                        context.add_error(
                            "StatisticalDistributions.gamma: 'shape' must be positive",
                            getattr(sv, "filename", None),
                            getattr(sv, "line_num", None),
                        )

            # Validate scale
            if "scale" in kwargs:
                scale_val = resolve_value(kwargs["scale"], context)

                if scale_val is not None:
                    if not isinstance(scale_val, (int, float)):
                        context.add_error(
                            f"StatisticalDistributions.gamma: 'scale' must be numeric, got {type(scale_val).__name__}",
                            getattr(sv, "filename", None),
                            getattr(sv, "line_num", None),
                        )
                    elif scale_val <= 0:
                        context.add_error(
                            "StatisticalDistributions.gamma: 'scale' must be positive",
                            getattr(sv, "filename", None),
                            getattr(sv, "line_num", None),
                        )

            # Validate seed
            StatisticalDistributions.Validators._validate_seed(sv, context, kwargs)

            # WARNING: Unknown parameters
            valid_params = {"shape", "scale", "seed"}
            unknown = set(kwargs.keys()) - valid_params
            if unknown:
                context.add_warning(
                    f"StatisticalDistributions.gamma: Unknown parameter(s): {', '.join(unknown)}",
                    getattr(sv, "filename", None),
                    getattr(sv, "line_num", None),
                )


for distribution in [normal, lognormal, binomial, exponential, poisson, gamma]:
    func_name = distribution.__name__
    setattr(StatisticalDistributions.Functions, func_name, wrap(distribution))
