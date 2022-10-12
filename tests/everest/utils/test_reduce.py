import random

import numpy as np
import pandas as pd
import pytest
from everest.domain import Domain
from everest.domain.constraints import (
    ConcurrencyConstraint,
    Constraint,
    LinearEqualityConstraint,
    LinearInequalityConstraint,
)
from everest.domain.features import (
    CategoricalInputFeature,
    ContinuousInputFeature,
    ContinuousOutputFeature,
    Feature,
)
from everest.utils.reduce import (
    check_domain_for_reduction,
    check_existence_of_solution,
    reduce_domain,
    rref,
)

if1 = ContinuousInputFeature(key="if1", lower_bound=0.0, upper_bound=0.8)

if2 = ContinuousInputFeature(key="if2", lower_bound=0.0, upper_bound=0.8)

cif1 = CategoricalInputFeature(key="cif1", categories=["A", "B"])

cif2 = CategoricalInputFeature(key="cif2", categories=["A", "B"])

of1 = ContinuousOutputFeature(key="of1")

of2 = ContinuousOutputFeature(key="of2")


def test_check_domain_for_reduction():
    # no constraints
    domain = Domain(input_features=[if1, cif1], output_features=[of1, of2])
    assert not check_domain_for_reduction(domain)

    # no linear equality constraints
    domain = Domain(
        input_features=[if1, if2],
        output_features=[of1, of2],
        constraints=[
            LinearInequalityConstraint(
                features=["if1", "if2"], coefficients=[1.0, 1.0], rhs=0.9
            )
        ],
    )
    assert not check_domain_for_reduction(domain)

    # no continuous input
    domain = Domain(input_features=[cif1, cif2], output_features=[of1, of2])
    assert not check_domain_for_reduction(domain)

    # everything okay
    domain = Domain(
        input_features=[if1, if2],
        output_features=[of1, of2],
        constraints=[
            LinearEqualityConstraint(
                features=["if1", "if2"], coefficients=[1.0, 1.0], rhs=1.0
            )
        ],
    )
    assert check_domain_for_reduction(domain) == True


def test_check_existence_of_solution():
    # rk(A) = rk(A_aug) = 1, 3 inputs
    A_aug = np.array([[1, 0, 0, -0.5], [1, 0, 0, -0.5]])
    check_existence_of_solution(A_aug)

    # rk(A) = 1, rk(A_aug) = 2, 3 inputs
    A_aug = np.array([[1, 0, 0, 0.5], [1, 0, 0, -0.5]])
    with pytest.raises(Exception):
        check_existence_of_solution(A_aug)

    # rk(A) = rk(A_aug) = 2, 3 inputs
    A_aug = np.array([[1, 0, 0, -0.5], [0, 1, 0, -0.5]])
    check_existence_of_solution(A_aug)

    # rk(A) = rk(A_aug) = 0, 3 inputs
    A_aug = np.array([[0, 0, 0, 0], [0, 0, 0, 0]])
    check_existence_of_solution(A_aug)

    # rk(A) = rk(A_aug) = 2, 2 inputs
    A_aug = np.array([[1, 0, -0.5], [0, 1, -0.5]])
    with pytest.raises(Exception):
        check_existence_of_solution(A_aug)


def test_reduce_1_independent_linear_equality_constraints():
    # define problem: standard case
    # this is not allowed in everest as it produces one dime constraints
    domain = Domain(
        input_features=[
            ContinuousInputFeature(key="x1", lower_bound=1.0, upper_bound=2.0),
            ContinuousInputFeature(key="x2", lower_bound=-1.0, upper_bound=1.0),
            CategoricalInputFeature(key="x3", categories=["A", "B"]),
            CategoricalInputFeature(key="x4", categories=["A", "B"]),
        ],
        output_features=[ContinuousOutputFeature(key="y1")],
        constraints=[
            LinearEqualityConstraint(features=["x1", "x2"], coefficients=[1, 1], rhs=0),
            LinearEqualityConstraint(
                features=["x1", "x2"], coefficients=[-0.5, -0.5], rhs=0
            ),
            LinearInequalityConstraint(
                features=["x1", "x2"], coefficients=[-1.0, -1.0], rhs=0
            ),
        ],
    )
    _domain, transform = reduce_domain(domain)

    assert len(_domain.input_features) == 3
    assert len(_domain.constraints) == 0
    assert _domain.get_feature("x2").lower_bound == -1.0
    assert _domain.get_feature("x2").upper_bound == -1.0

    # define problem: irreducible problem
    domain = Domain(
        input_features=[
            ContinuousInputFeature(key="x1", lower_bound=1, upper_bound=2.0),
            ContinuousInputFeature(key="x2", lower_bound=-1, upper_bound=1.0),
            CategoricalInputFeature(key="x3", categories=["A", "B"]),
        ],
        output_features=[ContinuousOutputFeature(key="y1")],
    )
    assert domain == reduce_domain(domain)[0]

    # define problem: linear equality constraints can't be fulfilled inside the domain
    domain = Domain(
        input_features=[
            ContinuousInputFeature(key="x1", lower_bound=1, upper_bound=2.0),
            ContinuousInputFeature(key="x2", lower_bound=-500, upper_bound=500.0),
        ],
        output_features=[ContinuousOutputFeature(key="y1")],
        constraints=[
            LinearEqualityConstraint(
                features=["x1", "x2"], coefficients=[1.0, 0.0], rhs=0
            )
        ],
    )
    with pytest.raises(Exception):
        reduce_domain(domain)


def test_reduce_2_independent_linear_equality_constraints():
    # define problem: standard case
    domain = Domain(
        input_features=[
            ContinuousInputFeature(key="x1", lower_bound=-1.0, upper_bound=1.0),
            ContinuousInputFeature(key="x2", lower_bound=-1.0, upper_bound=1.0),
            ContinuousInputFeature(key="x3", lower_bound=-1.0, upper_bound=1.0),
        ],
        output_features=[ContinuousOutputFeature(key="y1")],
        constraints=[
            LinearEqualityConstraint(
                features=["x1", "x2", "x3"], coefficients=[1.0, 1.0, 1.0], rhs=1
            ),
            LinearEqualityConstraint(
                features=["x1", "x2", "x3"], coefficients=[1.0, 2.0, 1.0], rhs=2
            ),
            LinearEqualityConstraint(
                features=["x1", "x2", "x3"], coefficients=[-1.0, -1.0, -1.0], rhs=-1
            ),
        ],
    )
    _domain, transform = reduce_domain(domain)

    assert len(_domain.input_features) == 1
    assert _domain.input_features[0].key == "x3"
    assert _domain.get_feature("x3").lower_bound == -1.0
    assert _domain.get_feature("x3").upper_bound == 1.0

    assert transform.equalities == [("x1", ["x3"], [-1.0, 0.0]), ("x2", [], [1.0])]


def test_reduce_3_independent_linear_equality_constraints():
    # define problem: standard case
    domain = Domain(
        input_features=[
            ContinuousInputFeature(key="x1", lower_bound=-1.0, upper_bound=1.0),
            ContinuousInputFeature(key="x2", lower_bound=-1.0, upper_bound=1.0),
            ContinuousInputFeature(key="x3", lower_bound=-1.0, upper_bound=1.0),
        ],
        output_features=[ContinuousOutputFeature(key="y1")],
        constraints=[
            LinearEqualityConstraint(
                features=["x1", "x2", "x3"], coefficients=[1.0, 1.0, 1.0], rhs=1
            ),
            LinearEqualityConstraint(
                features=["x1", "x2", "x3"], coefficients=[1.0, 2.0, 1.0], rhs=2
            ),
            LinearEqualityConstraint(
                features=["x1", "x2", "x3"], coefficients=[0.0, 0.0, 1.0], rhs=3
            ),
        ],
    )
    with pytest.raises(Exception):
        reduce_domain(domain)


def test_doc_simple():
    domain = Domain()
    domain.add_feature(
        ContinuousInputFeature(key="x1", lower_bound=0.1, upper_bound=1.0)
    )
    domain.add_feature(
        ContinuousInputFeature(key="x2", lower_bound=0.0, upper_bound=0.8)
    )
    domain.add_feature(
        ContinuousInputFeature(key="x3", lower_bound=0.3, upper_bound=0.9)
    )
    domain.add_feature(ContinuousOutputFeature(key="y"))
    domain.add_constraint(
        LinearEqualityConstraint(
            features=["x1", "x2", "x3"], coefficients=[1.0, 1.0, 1.0], rhs=1
        )
    )

    _domain, transform = reduce_domain(domain)

    assert len(_domain.get_features()) == 3
    assert np.allclose(
        [_domain.get_feature("x2").lower_bound, _domain.get_feature("x2").upper_bound],
        [0.0, 0.8],
    )
    assert np.allclose(
        [_domain.get_feature("x3").lower_bound, _domain.get_feature("x3").upper_bound],
        [0.3, 0.9],
    )

    assert len(_domain.constraints) == 2

    assert all(np.array(_domain.constraints[0].features) == np.array(["x2", "x3"]))
    assert np.allclose(_domain.constraints[0].coefficients, [1.0, 1.0])
    assert np.allclose(_domain.constraints[0].rhs, 0.0)

    assert all(np.array(_domain.constraints[1].features) == np.array(["x2", "x3"]))
    assert np.allclose(_domain.constraints[1].coefficients, [-1.0, -1.0])
    assert np.allclose(_domain.constraints[1].rhs, -0.9)


def test_doc_complex():
    domain = Domain()

    domain.add_feature(
        ContinuousInputFeature(key="A1", lower_bound=0.0, upper_bound=0.9)
    )
    domain.add_feature(
        ContinuousInputFeature(key="A2", lower_bound=0.0, upper_bound=0.8)
    )
    domain.add_feature(
        ContinuousInputFeature(key="A3", lower_bound=0.0, upper_bound=0.9)
    )
    domain.add_feature(
        ContinuousInputFeature(key="A4", lower_bound=0.0, upper_bound=0.9)
    )

    domain.add_feature(
        ContinuousInputFeature(key="B1", lower_bound=0.3, upper_bound=0.9)
    )
    domain.add_feature(
        ContinuousInputFeature(key="B2", lower_bound=0.0, upper_bound=0.8)
    )
    domain.add_feature(
        ContinuousInputFeature(key="B3", lower_bound=0.1, upper_bound=1.0)
    )

    domain.add_feature(
        CategoricalInputFeature(key="Process", categories=["p1", "p2", "p3"])
    )
    domain.add_feature(
        CategoricalInputFeature(key="Discrete", categories=["a1", "a2", "a3"])
    )

    domain.add_constraint(
        LinearEqualityConstraint(
            features=["A1", "A2", "A3", "A4"],
            coefficients=[1.0, 1.0, 1.0, 1.0],
            rhs=1.0,
        )
    )
    domain.add_constraint(
        LinearEqualityConstraint(
            features=["B1", "B2", "B3"], coefficients=[1.0, 1.0, 1], rhs=1.0
        )
    )

    domain.add_constraint(
        LinearInequalityConstraint(
            features=["A1", "A2"], coefficients=[-1.0, -2.0], rhs=-0.8
        )
    )

    _domain, transform = reduce_domain(domain)

    assert len(_domain.get_features()) == 7
    assert len(_domain.get_features(ContinuousInputFeature)) == 5

    assert np.allclose(
        [_domain.get_feature("A2").lower_bound, _domain.get_feature("A2").upper_bound],
        [0.0, 0.8],
    )
    assert np.allclose(
        [_domain.get_feature("A3").lower_bound, _domain.get_feature("A3").upper_bound],
        [0.0, 0.9],
    )
    assert np.allclose(
        [_domain.get_feature("A4").lower_bound, _domain.get_feature("A4").upper_bound],
        [0.0, 0.9],
    )
    assert np.allclose(
        [_domain.get_feature("B2").lower_bound, _domain.get_feature("B2").upper_bound],
        [0.0, 0.8],
    )
    assert np.allclose(
        [_domain.get_feature("B3").lower_bound, _domain.get_feature("B3").upper_bound],
        [0.1, 1.0],
    )

    assert all(
        np.array(_domain.constraints[0].features) == np.array(["A2", "A3", "A4"])
    )
    assert np.allclose(_domain.constraints[0].coefficients, [-1.0, 1.0, 1.0])
    assert np.allclose(_domain.constraints[0].rhs, 0.2)

    assert all(
        np.array(_domain.constraints[1].features) == np.array(["A2", "A3", "A4"])
    )
    assert np.allclose(_domain.constraints[1].coefficients, [1.0, 1.0, 1.0])
    assert np.allclose(_domain.constraints[1].rhs, 0.1)

    assert all(
        np.array(_domain.constraints[2].features) == np.array(["A2", "A3", "A4"])
    )
    assert np.allclose(_domain.constraints[2].coefficients, [-1.0, -1.0, -1.0])
    assert np.allclose(_domain.constraints[2].rhs, -1.0)

    assert all(np.array(_domain.constraints[3].features) == np.array(["B2", "B3"]))
    assert np.allclose(
        _domain.constraints[3].coefficients,
        [
            1.0,
            1.0,
        ],
    )
    assert np.allclose(_domain.constraints[3].rhs, 0.1)

    assert all(np.array(_domain.constraints[4].features) == np.array(["B2", "B3"]))
    assert np.allclose(
        _domain.constraints[4].coefficients,
        [
            -1.0,
            -1.0,
        ],
    )
    assert np.allclose(_domain.constraints[4].rhs, -0.7)


# def test_AffineTransform_augment_data():
#    domain = Domain()
#    domain.add_feature(
#        ContinuousInputFeature(key="x1", lower_bound=0.1, upper_bound=1.0)
#    )
#    domain.add_feature(
#        ContinuousInputFeature(key="x2", lower_bound=0.0, upper_bound=0.8)
#    )
#    domain.add_feature(
#        ContinuousInputFeature(key="x3", lower_bound=0.3, upper_bound=0.9)
#    )
#    domain.add_feature(ContinuousOutputFeature(key="y"))
#    domain.add_constraint(
#        LinearEqualityConstraint(
#            features=["x1", "x2", "x3"], coefficients=[1.0, 1.0, 1.0], rhs=1
#        )
#    )
#
#    _domain, transform = reduce_domain(domain)
#
#    rec = RandomStrategy.from_domain(domain)
#    data, _ = rec.ask(4)
#    data.drop(columns=["y_pred", "y_sd", "y_des"], inplace=True)
#    data["y"] = [random.random() for _ in range(4)]
#    data["valid_y"] = 1
#    domain.validate_experiments(data)
#
#    data_rec = transform.augment_data(data[_domain.get_feature_keys()])
#    assert np.allclose(
#        data[domain.get_feature_keys()].values,
#        data_rec[domain.get_feature_keys()].values,
#    )
#    domain.validate_experiments(data_rec)


# def test_AffineTransform_drop_data():
#    # define problem and transform
#    domain = Domain()
#    domain.add_feature(
#        ContinuousInputFeature(key="x1", lower_bound=0.1, upper_bound=1.0)
#    )
#    domain.add_feature(
#        ContinuousInputFeature(key="x2", lower_bound=0.0, upper_bound=0.8)
#    )
#    domain.add_feature(
#        ContinuousInputFeature(key="x3", lower_bound=0.3, upper_bound=0.9)
#    )
#    domain.add_feature(ContinuousOutputFeature(key="y"))
#    domain.add_constraint(
#        LinearEqualityConstraint(
#            features=["x1", "x2", "x3"], coefficients=[1.0, 1.0, 1.0], rhs=1
#        )
#    )
#
#    _domain, transform = reduce_domain(domain)
#
#    rec = RandomStrategy.from_domain(domain)
#    data, _ = rec.ask(4)
#    data.drop(columns=["y_pred", "y_sd", "y_des"], inplace=True)
#    data["y"] = [random.random() for _ in range(4)]
#    data["valid_y"] = 1
#    domain.validate_experiments(data)
#
#    _data = transform.drop_data(data)
#
#    with pytest.raises(ValueError):
#        domain.validate_experiments(_data)
#
#    _domain.validate_experiments(_data)
#
#    assert np.allclose(
#        data[_domain.get_feature_keys()].values,
#        _data[_domain.get_feature_keys()].values,
#    )


def test_reduce_large_problem():
    domain = Domain(
        input_features=[
            ContinuousInputFeature(key="x1", lower_bound=-1, upper_bound=1.0),
            ContinuousInputFeature(key="x2", lower_bound=-5000, upper_bound=1.0),
            ContinuousInputFeature(key="x3", lower_bound=-5000, upper_bound=5000.0),
            ContinuousInputFeature(key="x4", lower_bound=-1, upper_bound=1.0),
        ],
        output_features=[ContinuousOutputFeature(key="y1")],
        constraints=[
            LinearEqualityConstraint(
                features=["x1", "x2", "x4"], coefficients=[1.0, -1.0, 1.0], rhs=-1.0
            ),
            LinearEqualityConstraint(
                features=["x2", "x3"], coefficients=[2, 1], rhs=2.0
            ),
            LinearEqualityConstraint(
                features=["x1", "x2", "x3", "x4"],
                coefficients=[1.0, 1.0, 1.0, 1.0],
                rhs=1.0,
            ),
            LinearInequalityConstraint(
                features=["x1", "x2"], coefficients=[-1.0, -1.0], rhs=-1.0
            ),
            LinearInequalityConstraint(
                features=["x1", "x2", "x4"], coefficients=[-1.0, 1.0, -1.0], rhs=0.0
            ),
        ],
    )
    _domain, transform = reduce_domain(domain)

    assert transform.equalities == [
        ("x1", ["x3", "x4"], [-0.5, -1.0, 0.0]),
        ("x2", ["x3"], [-0.5, 1.0]),
    ]
    assert len(_domain.constraints) == 3

    assert all(np.array(_domain.constraints[0].features) == np.array(["x3", "x4"]))
    assert np.allclose(_domain.constraints[0].coefficients, [1.0, 1.0])
    assert np.allclose(_domain.constraints[0].rhs, 0.0)

    assert all(np.array(_domain.constraints[1].features) == np.array(["x3", "x4"]))
    assert np.allclose(_domain.constraints[1].coefficients, [0.5, 1.0])
    assert np.allclose(_domain.constraints[1].rhs, -1.0)

    assert all(np.array(_domain.constraints[2].features) == np.array(["x3", "x4"]))
    assert np.allclose(_domain.constraints[2].coefficients, [-0.5, -1.0])
    assert np.allclose(_domain.constraints[2].rhs, -1.0)

    assert np.allclose(
        [_domain.get_feature("x3").lower_bound, _domain.get_feature("x3").upper_bound],
        [-0.0, 5000.0],
    )
    assert np.allclose(
        [_domain.get_feature("x4").lower_bound, _domain.get_feature("x4").upper_bound],
        [-1.0, 1.0],
    )


def test_rref():
    A = np.vstack(([[np.pi, 1e10, np.log(10), 7]], [[np.pi, 1e10, np.log(10), 7]]))
    A_rref, pivots = rref(A)
    B_rref = np.array(
        [
            [1.0, 3183098861.837907, 0.7329355988794278, 2.228169203286535],
            [0.0, 0.0, 0.0, 0.0],
        ]
    )
    assert np.all(np.round(A_rref, 8) == np.round(B_rref, 8))
    assert all(np.array(pivots) == np.array([0]))

    A = np.array(
        [
            [np.pi, 2, 1, 1, 1],
            [1e10, np.exp(0), 2, 2, 2],
            [np.log(10), -5.2, 3, 3, 3],
            [7, -3.5 * 1e-4, 4, 4, 4],
        ]
    )
    A_rref, pivots = rref(A)
    B_rref = np.array(
        [
            [1.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 1.0, 1.0],
            [0.0, 0.0, 0.0, 0.0, 0.0],
        ]
    )
    assert np.all(np.round(A_rref, 8) == np.round(B_rref, 8))
    assert all(np.array(pivots) == np.array([0, 1, 2]))

    A = np.ones(shape=(100, 100))
    A_rref, pivots = rref(A)
    B_rref = np.zeros(shape=(100, 100))
    B_rref[0, :] = 1
    assert np.all(np.round(A_rref, 8) == np.round(B_rref, 8))
    assert all(np.array(pivots) == np.array([0]))

    A = np.zeros(shape=(10, 20))
    A_rref, pivots = rref(A)
    B_rref = np.zeros(shape=(10, 20))
    assert np.all(np.round(A_rref, 8) == np.round(B_rref, 8))
    assert all(np.array(pivots) == np.array([]))

    A = np.array([[0, 1, 2, 2, 3, 4], [0, 5, 10, 6, 7, 8], [0, 9, 18, 10, 11, 12]])
    A_rref, pivots = rref(A)
    B_rref = np.array([[0, 1, 2, 0, -1, -2], [0, 0, 0, 1, 2, 3], [0, 0, 0, 0, 0, 0]])
    assert np.all(np.round(A_rref, 8) == np.round(B_rref, 8))
    assert all(np.array(pivots) == np.array([1, 3]))

    A = np.array([[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]])
    A_rref, pivots = rref(A)
    B_rref = np.array([[1, 0, -1, -2], [0, 1, 2, 3], [0, 0, 0, 0]])
    assert np.all(np.round(A_rref, 8) == np.round(B_rref, 8))
    assert all(np.array(pivots) == np.array([0, 1]))
