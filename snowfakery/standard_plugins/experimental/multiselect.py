import random
import builtins

from snowfakery import SnowfakeryPlugin


# This is experimental primarily because it hard-codes the separator.
# It would be superior for the output stream to select the separator.

# Also not thrilled that it cannot accept a list as input.


class Multiselect(SnowfakeryPlugin):
    class Functions:
        def random_choices(
            self,
            choices: str,
            min: int = 1,
            max: int = None,
            with_replacement: bool = False,
            separator=";",
        ):
            choices = choices.split(",")
            max = max or len(choices)
            num_choices = random.randint(min, builtins.min(max, len(choices)))
            if with_replacement:
                return ";".join(random.choices(choices, k=num_choices))
            else:
                return ";".join(random.sample(choices, k=num_choices))
