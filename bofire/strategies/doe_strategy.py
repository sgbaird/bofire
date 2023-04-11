import pandas as pd
from pydantic.types import PositiveInt

import bofire.data_models.strategies.api as data_models
from bofire.strategies.doe.design import find_local_max_ipopt
from bofire.strategies.strategy import Strategy


class DoEStrategy(Strategy):
    """Strategy for design of experiments. This strategy is used to generate a set of
    experiments for a given domain.
    The experiments are generated via minimization of the D-optimality criterion.

    """

    def __init__(
        self,
        data_model: data_models.DoEStrategy,
        **kwargs,
    ):
        super().__init__(data_model=data_model, **kwargs)
        self.formula = data_model.formula
        self.domain = data_model.domain

    def _ask(self, candidate_count: PositiveInt) -> pd.DataFrame:
        _fixed_experiments = self.candidates
        _domain = self.domain

        design = find_local_max_ipopt(
            _domain,
            self.formula,
            n_experiments=candidate_count,
            fixed_experiments=_fixed_experiments,
        )
        return design  # type: ignore

    def has_sufficient_experiments(
        self,
    ) -> bool:
        """Abstract method to check if sufficient experiments are available.

        Returns:
            bool: True if number of passed experiments is sufficient, False otherwise
        """
        return True

    def set_candidates(self, candidates: pd.DataFrame):
        """Set candidates of the strategy. Overwrites existing ones.

        Args:
            experiments (pd.DataFrame): Dataframe with candidates.
        """
        candidates = self.domain.validate_candidates(candidates, only_inputs=True)
        self._candidates = candidates
