import gpytorch.kernels
import pytest
import torch
from pydantic import parse_obj_as

from bofire.models.gps.kernels import (
    AdditiveKernel,
    AnyKernel,
    LinearKernel,
    MaternKernel,
    MultiplicativeKernel,
    RBFKernel,
    ScaleKernel,
)
from bofire.models.gps.priors import (
    GammaPrior,
    botorch_lengthcale_prior,
    botorch_scale_prior,
)
from tests.bofire.domain.utils import get_invalids

EQUIVALENTS = {
    RBFKernel: gpytorch.kernels.RBFKernel,
    MaternKernel: gpytorch.kernels.MaternKernel,
    LinearKernel: gpytorch.kernels.LinearKernel,
    ScaleKernel: gpytorch.kernels.ScaleKernel,
    AdditiveKernel: gpytorch.kernels.AdditiveKernel,
    MultiplicativeKernel: gpytorch.kernels.ProductKernel,
}

VALID_RBF_SPEC = {
    "type": "RBFKernel",
    "ard": True,
    "lenghtscale_prior": botorch_lengthcale_prior(),
}
VALID_MATERN_SPEC = {
    "type": "MaternKernel",
    "ard": True,
    "nu": 2.5,
    "lenghtscale_prior": botorch_lengthcale_prior(),
}
VALID_LINEAR_SPEC = {"type": "LinearKernel"}

VALID_SCALE_SPEC = {"type": "ScaleKernel", "base_kernel": RBFKernel()}

VALID_ADDITIVE_SPEC = {"type": "AdditiveKernel", "kernels": [RBFKernel(), RBFKernel()]}

VALID_MULTIPLICATIVE_SPEC = {
    "type": "MultiplicativeKernel",
    "kernels": [RBFKernel(), RBFKernel()],
}

KERNEL_SPECS = {
    RBFKernel: {
        "valids": [
            VALID_RBF_SPEC,
        ],
        "invalids": [
            *get_invalids(VALID_RBF_SPEC),
        ],
    },
    MaternKernel: {
        "valids": [
            VALID_MATERN_SPEC,
        ],
        "invalids": [
            *get_invalids(VALID_MATERN_SPEC),
        ],
    },
    LinearKernel: {
        "valids": [
            VALID_LINEAR_SPEC,
        ],
        "invalids": [
            *get_invalids(VALID_LINEAR_SPEC),
        ],
        ScaleKernel: {
            "valids": [VALID_SCALE_SPEC],
            "invalids": [
                *get_invalids(VALID_SCALE_SPEC),
            ],
        },
        MultiplicativeKernel: {
            "valids": [VALID_MULTIPLICATIVE_SPEC],
            "invalids": [
                *get_invalids(VALID_SCALE_SPEC),
            ],
        },
    },
}


@pytest.mark.parametrize(
    "cls, spec",
    [(cls, valid) for cls, data in KERNEL_SPECS.items() for valid in data["valids"]],
)
def test_valid_kernel_specs(cls, spec):
    res = cls(**spec)
    assert isinstance(res, cls)
    assert isinstance(res.__str__(), str)
    gkernel = res.to_gpytorch(
        batch_shape=torch.Size(), ard_num_dims=10, active_dims=list(range(5))
    )
    assert isinstance(gkernel, EQUIVALENTS[cls])
    res2 = parse_obj_as(AnyKernel, res.dict())
    assert res == res2


def test_scale_kernel():
    kernel = ScaleKernel(
        base_kernel=RBFKernel(), outputscale_prior=botorch_scale_prior()
    )
    k = kernel.to_gpytorch(
        batch_shape=torch.Size(),
        ard_num_dims=10,
        active_dims=list(range(5)),
    )
    assert hasattr(k, "outputscale_prior")
    assert isinstance(k.outputscale_prior, gpytorch.priors.GammaPrior)
    kernel = ScaleKernel(base_kernel=RBFKernel())
    k = kernel.to_gpytorch(
        batch_shape=torch.Size(),
        ard_num_dims=10,
        active_dims=list(range(5)),
    )
    assert hasattr(k, "outputscale_prior") is False


@pytest.mark.parametrize(
    "kernel, ard_num_dims, active_dims, expected_kernel",
    [
        (
            RBFKernel(
                ard=False, lengthscale_prior=GammaPrior(concentration=2.0, rate=0.15)
            ),
            10,
            list(range(5)),
            gpytorch.kernels.RBFKernel,
        ),
        (
            RBFKernel(ard=False),
            10,
            list(range(5)),
            gpytorch.kernels.RBFKernel,
        ),
        (RBFKernel(ard=True), 10, list(range(5)), gpytorch.kernels.RBFKernel),
        (
            MaternKernel(
                ard=False, lengthscale_prior=GammaPrior(concentration=2.0, rate=0.15)
            ),
            10,
            list(range(5)),
            gpytorch.kernels.MaternKernel,
        ),
        (MaternKernel(ard=False), 10, list(range(5)), gpytorch.kernels.MaternKernel),
        (MaternKernel(ard=True), 10, list(range(5)), gpytorch.kernels.MaternKernel),
        (
            MaternKernel(ard=False, nu=2.5),
            10,
            list(range(5)),
            gpytorch.kernels.MaternKernel,
        ),
        (
            MaternKernel(ard=True, nu=1.5),
            10,
            list(range(5)),
            gpytorch.kernels.MaternKernel,
        ),
        (LinearKernel(), 10, list(range(5)), gpytorch.kernels.LinearKernel),
    ],
)
def test_continuous_kernel(kernel, ard_num_dims, active_dims, expected_kernel):
    k = kernel.to_gpytorch(
        batch_shape=torch.Size(), ard_num_dims=ard_num_dims, active_dims=active_dims
    )
    assert isinstance(k, expected_kernel)
    if isinstance(kernel, LinearKernel):
        return
    if kernel.lengthscale_prior is not None:
        assert hasattr(k, "lengthscale_prior")
        assert isinstance(k.lengthscale_prior, gpytorch.priors.GammaPrior)
    else:
        assert hasattr(k, "lengthscale_prior") is False

    if kernel.ard is False:
        assert k.ard_num_dims is None
    else:
        assert k.ard_num_dims == len(active_dims)
    assert torch.eq(k.active_dims, torch.tensor(active_dims, dtype=torch.int64)).all()

    if isinstance(kernel, gpytorch.kernels.MaternKernel):
        assert kernel.nu == k.nu