import pytest
import torch
import torch.nn as nn
from botorch.models.transforms.input import InputStandardize, Normalize

from bofire.benchmarks.single import Himmelblau
from bofire.domain.feature import CategoricalInput, ContinuousInput, ContinuousOutput
from bofire.domain.features import InputFeatures, OutputFeatures
from bofire.models.nns.mlp import (
    MLP,
    MLPEnsemble,
    RegressionDataSet,
    _MLPEnsemble,
    fit_mlp,
)
from bofire.utils.enum import ScalerEnum
from bofire.utils.torch_tools import tkwargs


@pytest.mark.parametrize(
    "activation, expected",
    [
        ["relu", nn.modules.activation.ReLU],
        ["logistic", nn.modules.activation.Sigmoid],
        ["tanh", nn.modules.activation.Tanh],
    ],
)
def test_mlp_activation(activation, expected):
    mlp = MLP(input_size=2, output_size=1, activation=activation)
    assert isinstance(mlp.layers[1], expected)


def test_mlp_activation_invalid():
    with pytest.raises(ValueError):
        MLP(input_size=2, output_size=1, activation="mama")


@pytest.mark.parametrize("output_size", [1, 2])
def test_mlp_input_size(output_size):
    mlp = MLP(input_size=2, output_size=output_size)
    assert mlp.layers[-1].out_features == output_size


def test_mlp_hidden_layer_sizes():
    mlp = MLP(input_size=2, output_size=1, hidden_layer_sizes=(8, 4, 2))
    assert len(mlp.layers) == 7
    assert mlp.layers[0].in_features == 2
    assert mlp.layers[0].out_features == 8
    assert mlp.layers[2].in_features == 8
    assert mlp.layers[2].out_features == 4
    assert mlp.layers[4].in_features == 4
    assert mlp.layers[4].out_features == 2
    assert mlp.layers[6].in_features == 2
    assert mlp.layers[6].out_features == 1
    assert isinstance(mlp.layers[1], nn.modules.activation.ReLU)
    assert isinstance(mlp.layers[3], nn.modules.activation.ReLU)
    assert isinstance(mlp.layers[5], nn.modules.activation.ReLU)


def test_mlp_dropout():
    mlp = MLP(input_size=2, output_size=1, hidden_layer_sizes=(8, 4, 2), dropout=0.2)
    assert len(mlp.layers) == 10
    assert mlp.layers[0].in_features == 2
    assert mlp.layers[0].out_features == 8
    assert isinstance(mlp.layers[1], nn.modules.activation.ReLU)
    assert isinstance(mlp.layers[2], nn.modules.Dropout)
    assert mlp.layers[2].p == 0.2
    assert mlp.layers[3].in_features == 8
    assert isinstance(mlp.layers[4], nn.modules.activation.ReLU)
    assert isinstance(mlp.layers[5], nn.modules.Dropout)
    assert mlp.layers[3].out_features == 4
    assert mlp.layers[6].in_features == 4
    assert mlp.layers[6].out_features == 2
    assert isinstance(mlp.layers[7], nn.modules.activation.ReLU)
    assert isinstance(mlp.layers[8], nn.modules.Dropout)
    assert mlp.layers[9].in_features == 2
    assert mlp.layers[9].out_features == 1


def test_RegressionDataSet():
    X = torch.randn(10, 3)
    y = torch.randn(10, 1)
    dset = RegressionDataSet(X=X, y=y)
    assert len(dset) == 10
    xi, yi = dset[3]
    assert torch.allclose(xi, X[3].to(**tkwargs))
    assert torch.allclose(yi, y[3].to(**tkwargs))


@pytest.mark.parametrize(
    "mlp, weight_decay, n_epoches, lr, shuffle",
    [
        [
            MLP(input_size=2, output_size=1, hidden_layer_sizes=(8, 4, 2), dropout=0.2),
            0,
            10,
            1e-4,
            True,
        ],
        [
            MLP(input_size=2, output_size=1, hidden_layer_sizes=(8, 4, 2), dropout=0.2),
            0.1,
            5,
            1e-3,
            False,
        ],
    ],
)
def test_fit_mlp(mlp, weight_decay, n_epoches, lr, shuffle):
    benchmark = Himmelblau()
    samples = benchmark.domain.inputs.sample(10)
    experiments = benchmark.f(candidates=samples, return_complete=True)
    X, y = torch.from_numpy(experiments[["x_1", "x_2"]].values), torch.from_numpy(
        experiments[["y"]].values
    )
    dset = RegressionDataSet(X=X, y=y)
    fit_mlp(
        mlp=mlp,
        dataset=dset,
        weight_decay=weight_decay,
        n_epoches=n_epoches,
        lr=lr,
        shuffle=shuffle,
    )


def test_mlp_ensemble_no_mls():
    with pytest.raises(ValueError):
        _MLPEnsemble(mlps=[])


def test_mlp_ensemble_not_matching_models():
    mlp1 = MLP(input_size=2, output_size=1)
    mlp2 = MLP(input_size=3, output_size=1)
    with pytest.raises(AssertionError):
        _MLPEnsemble(mlps=[mlp1, mlp2])
    mlp1 = MLP(input_size=3, output_size=1)
    mlp2 = MLP(input_size=3, output_size=2)
    with pytest.raises(AssertionError):
        _MLPEnsemble(mlps=[mlp1, mlp2])


def test_mlp_ensemble_num_outputs():
    mlp1 = MLP(input_size=3, output_size=1)
    mlp2 = MLP(input_size=3, output_size=1)
    ens = _MLPEnsemble(mlps=[mlp1, mlp2])
    assert ens.num_outputs == 1


def test_mlp_ensemble_forward():
    bench = Himmelblau()
    samples = bench.domain.inputs.sample(10)
    experiments = bench.f(samples, return_complete=True)
    mlp1 = MLP(input_size=2, output_size=1)
    mlp2 = MLP(input_size=2, output_size=1)
    ens = _MLPEnsemble(mlps=[mlp1, mlp2])
    pred = ens.forward(torch.from_numpy(experiments[["x_1", "x_2"]].values))
    assert pred.shape == torch.Size((2, 10, 1))
    # test with batches
    batch = torch.from_numpy(experiments[["x_1", "x_2"]].values).unsqueeze(0)
    pred = ens.forward(batch)
    assert pred.shape == torch.Size((1, 2, 10, 1))


@pytest.mark.parametrize("scaler", [ScalerEnum.NORMALIZE, ScalerEnum.STANDARDIZE])
def test_mlp_ensemble_fit(scaler):
    bench = Himmelblau()
    samples = bench.domain.inputs.sample(10)
    experiments = bench.f(samples, return_complete=True)
    ens = MLPEnsemble(
        input_features=bench.domain.input_features,
        output_features=bench.domain.output_features,
        size=2,
        n_epochs=5,
        scaler=scaler,
    )
    ens.fit(experiments=experiments)
    assert isinstance(
        ens.model.input_transform,
        Normalize if scaler == ScalerEnum.NORMALIZE else InputStandardize,
    )


@pytest.mark.parametrize("scaler", [ScalerEnum.NORMALIZE, ScalerEnum.STANDARDIZE])
def test_mlp_ensemble_fit_categorical(scaler):
    input_features = InputFeatures(
        features=[
            ContinuousInput(key=f"x_{i+1}", lower_bound=-4, upper_bound=4)
            for i in range(2)
        ]
        + [CategoricalInput(key="x_cat", categories=["mama", "papa"])]
    )
    output_features = OutputFeatures(features=[ContinuousOutput(key="y")])
    experiments = input_features.sample(n=10)
    experiments.eval("y=((x_1**2 + x_2 - 11)**2+(x_1 + x_2**2 -7)**2)", inplace=True)
    experiments.loc[experiments.x_cat == "mama", "y"] *= 5.0
    experiments.loc[experiments.x_cat == "papa", "y"] /= 2.0
    experiments["valid_y"] = 1

    ens = MLPEnsemble(
        input_features=input_features,
        output_features=output_features,
        size=2,
        n_epochs=5,
        scaler=ScalerEnum.STANDARDIZE,
    )
    ens.fit(experiments=experiments)
    assert isinstance(
        ens.model.input_transform,
        InputStandardize,
    )
    assert torch.eq(
        ens.model.input_transform.indices, torch.tensor([0, 1], dtype=torch.int64)
    ).all()
