from typing import List, Optional, Sequence, Tuple, Type

import numpy as np
import pandas as pd
import torch
from pydantic.types import NonNegativeFloat, PositiveInt
from sklearn.ensemble import RandomForestRegressor

from bofire.domain.constraints import Constraint
from bofire.domain.features import _CAT_SEP, CategoricalInput, Feature
from bofire.domain.objectives import Objective
from bofire.strategies.random import RandomStrategy
from bofire.strategies.strategy import PredictiveStrategy
from bofire.utils.enum import CategoricalEncodingEnum


class RandomForest(PredictiveStrategy):
    """Surrogate-assisted optimization with RandomForests.

    The algorithm can handle constrained mixed variable problems with single and multiple objectives.
    It is intended as a cheap alternative to ENTMOOT.

    Description:
    - Model: RandomForest with a distance-based uncertainty measure.
    - Proposals: BayesOpt with random Chebyshef scalarization and optimistic confidence bound.
    - Optimization: Brute-force.
    - Pareto approximation: Not implemented.
    """

    models: Optional[Sequence[RandomForestRegressor]]

    def _fit(self, experiments: pd.DataFrame) -> None:

        Xt = self.domain.inputs.transform(
            experiments, specs=self.input_preprocessing_specs
        )

        # Fit a model for each target variable
        self.models = []
        for y_name in self.domain.outputs.get_keys():
            y = experiments[y_name].to_numpy()
            self.models.append(RandomForestRegressor().fit(Xt, y))

        self.is_fitted = True
        return None

    def make_random_candidates(self, Ncands: PositiveInt) -> pd.DataFrame:
        return RandomStrategy(domain=self.domain).ask(Ncands)

    def _min_distance(
        self, X1: pd.DataFrame, X2: pd.DataFrame, p: NonNegativeFloat = 1.0
    ) -> torch.Tensor:
        """Vector of minimum L1-norm-distances between each point in X1 and all in X2

        Args:
            X1 (pd.DataFrame): Set of points for which min distances to X2 are required
            X2 (pd.DataFrame): Set of reference or training points. X1 and X2 should
                have the same column names.
            p (NonNegativeFloat): p value for the p-norm distance to calculate between
                each vector pair. The default of 1 corresponds to the L-1 norm.

        Returns:
            torch.Tensor of length X1.shape[0], ie, number of rows in X1. Each entry is
                the minimum distance between the corresponding row in X1 and all the rows
                of X2.
        """

        # set all onehot-encode values to 0.5 so that the L1-distance becomes 1
        # since we are working with the transformed data we have to do a bit of
        # work here to find out the names of the columns related to each feature
        if self.domain.get_feature_keys(CategoricalInput) is not None:
            for featname in self.domain.get_feature_keys(CategoricalInput):
                feat = self.domain.get_feature(featname)
                cat_cols = [f"{feat.key}{_CAT_SEP}{c}" for c in feat.categories]
                for cat_colname in cat_cols:
                    if cat_colname in X1.columns:
                        X1[cat_colname] /= 2
                        X2[cat_colname] /= 2

        D = torch.cdist(torch.tensor(X1.values), torch.tensor(X2.values), p=p).numpy()
        return D.min(axis=1)

    def _uncertainty(self, Xquery: pd.DataFrame) -> List[np.ndarray]:
        """Uncertainty estimate ~ distance to the closest data point.

        Each element in the returned list is a vector of length
        Xquery.shape[0] (ie, number of rows in Xquery) giving the scaled minimum
        distance to the nearest datapoint in the training data in self.experiments.
        The length of the returned list is the same as the number of output features
        for prediction and the scaling factor is the range of the output feature values.

        Args:
            Xquery (pd.DataFrame): set of points for which the uncertainties are required

        Returns:
            List[np.ndarray]
        """

        if self.domain.experiments is not None:
            Xtrain = self.domain.inputs.transform(
                experiments=self.domain.experiments,
                specs=self.input_preprocessing_specs,
            )
        else:
            raise Exception(
                "No training data were found for uncertainty estimation in RandomForest._uncertainty"
            )

        min_dist = self._min_distance(Xquery, Xtrain)
        min_dist = min_dist / len(Xtrain.columns)

        # divide by the range of observed target values to make the scale of the uncertainty
        # better match the rest of the acquisition function
        output_keys = self.domain.output_features.get_keys()
        yranges = self.experiments[output_keys].max(
            axis=0, skipna=True
        ) - self.experiments[output_keys].min(axis=0, skipna=True)

        return [np.abs(min_dist / yrange) for yrange in yranges]

    def _predict(self, experiments: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Run predictions for the provided experiments. Only input features have to be provided.

        Args:
            experiments (pd.DataFrame): Experimental data for which predictions should be performed.

        Returns:
            pd.DataFrame: Dataframe with the predicted values.
        """
        if self.models is None:
            raise Exception(
                "RandomForest._predict was called but no models have been fitted yet"
            )
        Xt = experiments  # experiments has already been transformed / preprocessed
        Ym = [model.predict(Xt.to_numpy()) for model in self.models]
        uncert = self._uncertainty(Xt)

        ypred = pd.DataFrame(Ym).T
        yuncert = pd.DataFrame(uncert).T

        return ypred, yuncert

    def calc_acquisition(
        self,
        candidates: pd.DataFrame,
        kappa: NonNegativeFloat,
        predictions: Optional[pd.DataFrame],
    ) -> pd.DataFrame:
        """Calculate the acqusition value for a set of experiments.

        Args:
            candidates (pd.DataFrame): Dataframe with experiments for which the acqf value should be calculated.
            kappa (NonNegativeFloat)): Parameter controlling the exploration/exploitation trade-off. Larger values
                favor uncertainty; setting kappa to zero causes the prediction uncertainty to be ignored.
            predictions (Optional[pd.DataFrame]): The values and uncertainties already predicted for the candidates.
                May be passed here to avoid repeating prediction calculations done by the caller

        Returns:
            pd.DataFrame: Dataframe with the acquisition values.
        """
        if predictions is None:
            predictions = self.predict(candidates)
        acq_values = {}
        for feat in self.domain.outputs.get_by_objective(Objective):
            pred_mean = predictions[f"{feat.key}_pred"].to_numpy()
            pred_sdev = predictions[f"{feat.key}_sd"].to_numpy()
            acq_values[f"{feat.key}_des"] = pred_mean - kappa * pred_sdev
        return pd.DataFrame(acq_values)

    def _ask(
        self,
        candidate_count: Optional[PositiveInt] = None,
        sample_count: PositiveInt = 10000,
        kappa: NonNegativeFloat = 0.5,
    ) -> pd.DataFrame:
        """Draw many random samples and return the best candidate_count ones

        Args:
            candidate_count (PositiveInt, optional): Number of candidates to be generated. Defaults to None.
            sample_count (PositiveInt, optional): Number of random samples from which candidate_count should be selected.
                Larger values will lead to better optima but will be slower and use more memory.
            kappa (NonNegativeFloat)): Parameter controlling the exploration/exploitation trade-off. Larger values
                favor uncertainty; setting kappa to zero causes the prediction uncertainty to be ignored.

        Returns:
            pd.DataFrame: DataFrame with candidates (proposed experiments).
        """
        random_samples = self.make_random_candidates(sample_count)
        samples_predicted = self.predict(random_samples)
        acqf_values = self.calc_acquisition(
            candidates=random_samples, kappa=kappa, predictions=samples_predicted
        )
        proposals = pd.concat([random_samples, samples_predicted, acqf_values], axis=1)

        # bofire.utils.multiobjective.get_pareto_front should help us out here

        # Do the following Nproposals times:
        #     sample a weight vector from the simplex with Nobjs dimensions
        #     get a lot of random samples covering the input space
        #     calculate the acq fun for each random sample
        #     scale the acq function values to makes multiple objectives comparable (Pareto front in unit hypercube)
        #     chebyshev scalarization
        #     choose the best candidate

        return proposals.iloc[:candidate_count, :]

    # def _ask(
    #     self,
    #     n_proposals: Optional[int] = None,
    #     kappa: float = 0.5,
    #     weights: Optional[np.ndarray] = None,
    # ) -> pd.DataFrame:
    #     """Was called propose in brain/bo"""
    #     if n_proposals is None:
    #         n_proposals = 1

    #     if weights is None:
    #         n_objectives = len(self.problem.objectives)
    #         weights = opti.sampling.simplex.sample(n_objectives, n_proposals)
    #     else:
    #         weights = np.atleast_2d(weights)

    #     proposals = []

    #     for w in weights:
    #         X = self.problem.sample_inputs(self.n_samples)
    #         Xt = self.problem.inputs.transform(X, categorical="dummy-encode")
    #         Y_mean = pd.DataFrame(
    #             self.model.predict(Xt.values), columns=self.problem.outputs.names
    #         )
    #         Z_mean = self.problem.objectives(Y_mean)

    #         # take the pending proposals into account for the uncertainty
    #         X_data = self.problem.data[self.problem.inputs.names]
    #         X_data = pd.concat([X_data] + proposals, axis=0)
    #         Y_std = self._uncertainty(X, X_data)
    #         Z_std = Y_std  # may not be true for close-to-target objectives

    #         # optimistic confidence bound
    #         cb = Z_mean.to_numpy() - kappa * Z_std
    #         # normalize so that the Pareto front is in the unit range
    #         s = opti.metric.is_pareto_efficient(cb)
    #         cb_min = cb[s].min(axis=0)
    #         cb_max = cb[s].max(axis=0)
    #         cb = (cb - cb_min) / np.clip(cb_max - cb_min, 1e-7, None)

    #         # weighted max norm
    #         A = np.max(w * cb, axis=1)
    #         best = np.argmin(A)
    #         proposals.append(X.iloc[[best]])

    #     return pd.concat(proposals)

    # def get_model_parameters(self) -> pd.DataFrame:
    #     # get the columns labels for the one-hot encoded inputs in case there are categoricals
    #     cols = self.problem.inputs.transform(
    #         self.problem.data, categorical="dummy-encode"
    #     ).columns

    #     # return the feature importances
    #     m = self.problem.n_outputs
    #     params = pd.DataFrame(
    #         index=self.problem.outputs.names,
    #         data=np.tile(self.model.feature_importances_, reps=(m, 1)),
    #         columns=cols,
    #     )
    #     params.index.name = "output"
    #     return params

    # def to_config(self) -> dict:
    #     return {
    #         "method": "RandomForest",
    #         "problem": self.problem.to_config(),
    #         "parameters": {"n_samples": self.n_samples},
    #     }

    @classmethod
    def is_constraint_implemented(cls, my_type: Type[Constraint]) -> bool:
        """The optimization is based on random sampling here, so whatever constraints
        are ok for the random sampler are ok here too
        """
        return RandomStrategy.is_constraint_implemented(my_type)

    @classmethod
    def is_feature_implemented(cls, my_type: Type[Feature]) -> bool:
        """Method to check if a specific feature type is implemented for the strategy

        Args:
            my_type (Type[Feature]): Feature class

        Returns:
            bool: True if the feature type is valid for the strategy chosen, False otherwise
        """
        return True

    @classmethod
    def is_objective_implemented(cls, my_type: Type[Objective]) -> bool:
        """Method to check if a objective type is implemented for the strategy

        Args:
            my_type (Type[Objective]): Objective class

        Returns:
            bool: True if the objective type is valid for the strategy chosen, False otherwise
        """
        return True

    def _choose_from_pool(self):
        pass

    def has_sufficient_experiments(self):
        return self.models is not None

    @property
    def input_preprocessing_specs(self):
        return {
            key: CategoricalEncodingEnum.DUMMY
            for key in self.domain.inputs.get_keys(CategoricalInput)
        }