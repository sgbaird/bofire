import pandas as pd
import pytest

import bofire.surrogates.api as surrogates
from bofire.data_models.domain.api import Inputs, Outputs
from bofire.data_models.features.api import ContinuousInput, ContinuousOutput
from bofire.data_models.surrogates.api import SingleTaskGPSurrogate
from bofire.surrogates.diagnostics import metrics
from bofire.surrogates.feature_importance import (
    combine_permutation_importances,
    permutation_importance,
    permutation_importance_hook,
)


def get_model_and_data():
    inputs = Inputs(
        features=[
            ContinuousInput(
                key=f"x_{i+1}",
                bounds=(-4, 4),
            )
            for i in range(3)
        ]
    )
    outputs = Outputs(features=[ContinuousOutput(key="y")])
    experiments = inputs.sample(n=20)
    experiments.eval("y=((x_1**2 + x_2 - 11)**2+(x_1 + x_2**2 -7)**2)", inplace=True)
    experiments["valid_y"] = 1
    model = SingleTaskGPSurrogate(
        inputs=inputs,
        outputs=outputs,
    )
    model = surrogates.map(model)
    return model, experiments


def test_permutation_importance_invalid():
    model, experiments = get_model_and_data()
    X = experiments[model.inputs.get_keys()]
    y = experiments[["y"]]
    model.fit(experiments=experiments)
    with pytest.raises(AssertionError):
        permutation_importance(model=model, X=X, y=y, n_repeats=1)
    with pytest.raises(AssertionError):
        permutation_importance(model=model, X=X, y=y, n_repeats=2, seed=-1)


def test_permutation_importance():
    model, experiments = get_model_and_data()
    X = experiments[model.inputs.get_keys()]
    y = experiments[["y"]]
    model.fit(experiments=experiments)
    results = permutation_importance(model=model, X=X, y=y, n_repeats=5)
    assert isinstance(results, dict)
    assert len(results) == len(metrics)
    for m in metrics.keys():
        assert m.name in results.keys()
        assert isinstance(results[m.name], pd.DataFrame)
        assert list(results[m.name].columns) == model.inputs.get_keys()
        assert list(results[m.name].index) == ["mean", "std"]


@pytest.mark.parametrize("use_test", [True, False])
def test_permutation_importance_hook(use_test):
    model, experiments = get_model_and_data()
    X = experiments[model.inputs.get_keys()]
    y = experiments[["y"]]
    model.fit(experiments=experiments)
    results = permutation_importance_hook(
        model=model, X_train=X, y_train=y, X_test=X, y_test=y, use_test=use_test
    )
    assert isinstance(results, dict)
    assert len(results) == len(metrics)
    for m in metrics.keys():
        assert m.name in results.keys()
        assert isinstance(results[m.name], pd.DataFrame)
        assert list(results[m.name].columns) == model.inputs.get_keys()
        assert list(results[m.name].index) == ["mean", "std"]


@pytest.mark.parametrize("n_folds", [5, 3])
def test_combine_permutation_importances(n_folds):
    model, experiments = get_model_and_data()
    _, _, pi = model.cross_validate(
        experiments,
        folds=n_folds,
        hooks={"pemutation_importance": permutation_importance_hook},
    )
    for m in metrics.keys():
        importance = combine_permutation_importances(
            importances=pi["pemutation_importance"], metric=m
        )
        list(importance.columns) == model.inputs.get_keys()
        assert len(importance) == n_folds
