import random
import uuid

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal
from pydantic.error_wrappers import ValidationError

from bofire.domain.features import (
    CategoricalDescriptorInput,
    CategoricalInput,
    ContinuousDescriptorInput,
    ContinuousInput,
    ContinuousOutput,
    DiscreteInput,
    Feature,
)
from bofire.domain.objectives import MinimizeObjective
from tests.bofire.domain.utils import get_invalids

objective = MinimizeObjective(w=1)

VALID_CONTINUOUS_INPUT_FEATURE_SPEC = {
    "key": str(uuid.uuid4()),
    "lower_bound": 3,
    "upper_bound": 5.3,
}

VALID_FIXED_CONTINUOUS_INPUT_FEATURE_SPEC = {
    "key": str(uuid.uuid4()),
    "lower_bound": 3.0,
    "upper_bound": 3.0,
}

VALID_DISCRETE_INPUT_FEATURE_SPEC = {"key": str(uuid.uuid4()), "values": [1.0, 2.0]}

VALID_FIXED_DISCRETE_INPUT_FEATURE_SPEC = {"key": str(uuid.uuid4()), "values": [2.0]}

VALID_CONTINUOUS_DESCRIPTOR_INPUT_FEATURE_SPEC = {
    "key": str(uuid.uuid4()),
    "lower_bound": 3,
    "upper_bound": 5.3,
    "descriptors": ["d1", "d2"],
    "values": [1.0, 2.0],
}

VALID_CATEGORICAL_INPUT_FEATURE_SPEC = {
    "key": str(uuid.uuid4()),
    "categories": ["c1", "c2", "c3"],
    # "allowed": [True, True, False],
}

VALID_CATEGORICAL_DESCRIPTOR_INPUT_FEATURE_SPEC = {
    "key": str(uuid.uuid4()),
    "categories": ["c1", "c2", "c3"],
    # "allowed": [True, True, False],
    "descriptors": ["d1", "d2"],
    "values": [
        [1, 2],
        [3, 7],
        [5, 1],
    ],
}


VALID_ALLOWED_CATEGORICAL_DESCRIPTOR_INPUT_FEATURE_SPEC = {
    "key": str(uuid.uuid4()),
    "categories": ["c1", "c2", "c3"],
    "allowed": [False, True, True],
    "descriptors": ["d1", "d2"],
    "values": [
        [1, 2],
        [3, 7],
        [3, 1],
    ],
}

VALID_FIXED_CATEGORICAL_INPUT_FEATURE_SPEC = {
    "key": str(uuid.uuid4()),
    "categories": ["c1", "c2", "c3"],
    "allowed": [True, False, False],
}

VALID_FIXED_CATEGORICAL_DESCRIPTOR_INPUT_FEATURE_SPEC = {
    "key": str(uuid.uuid4()),
    "categories": ["c1", "c2", "c3"],
    "allowed": [True, False, False],
    "descriptors": ["d1", "d2"],
    "values": [
        [1, 2],
        [3, 7],
        [5, 1],
    ],
}

VALID_CONTINUOUS_OUTPUT_FEATURE_SPEC = {
    "key": str(uuid.uuid4()),
}

FEATURE_SPECS = {
    ContinuousInput: {
        "valids": [
            VALID_CONTINUOUS_INPUT_FEATURE_SPEC,
        ],
        "invalids": [
            *get_invalids(VALID_CONTINUOUS_INPUT_FEATURE_SPEC),
        ],
    },
    DiscreteInput: {
        "valids": [
            VALID_DISCRETE_INPUT_FEATURE_SPEC,
        ],
        "invalids": [
            *get_invalids(VALID_DISCRETE_INPUT_FEATURE_SPEC),
            *[
                {
                    **VALID_DISCRETE_INPUT_FEATURE_SPEC,
                    "values": values,
                }
                for values in [[], [1.0, 1.0], [1.0, "a"]]
            ],
        ],
    },
    ContinuousDescriptorInput: {
        "valids": [VALID_CONTINUOUS_DESCRIPTOR_INPUT_FEATURE_SPEC],
        "invalids": [
            *get_invalids(VALID_CONTINUOUS_DESCRIPTOR_INPUT_FEATURE_SPEC),
            *[
                {
                    **VALID_CONTINUOUS_DESCRIPTOR_INPUT_FEATURE_SPEC,
                    "descriptors": descriptors,
                    "values": values,
                }
                for descriptors, values in [
                    ([], []),
                    (["a", "b"], [1]),
                    (["a", "b"], [1, 2, 3]),
                ]
            ],
        ],
    },
    CategoricalInput: {
        "valids": [
            VALID_CATEGORICAL_INPUT_FEATURE_SPEC,
            {
                **VALID_CATEGORICAL_INPUT_FEATURE_SPEC,
                "allowed": [True, False, True],
            },
        ],
        "invalids": [
            *get_invalids(VALID_CATEGORICAL_INPUT_FEATURE_SPEC),
            *[
                {
                    **VALID_CATEGORICAL_INPUT_FEATURE_SPEC,
                    "categories": categories,
                    "allowed": allowed,
                }
                for categories, allowed in [
                    ([], []),
                    (["1"], [False]),
                    (["1", "2"], [False, False]),
                    (["1", "1"], None),
                    (["1", "1", "2"], None),
                    (["1", "2"], [True]),
                    (["1", "2"], [True, False, True]),
                    (["1"], []),
                    (["1"], [True]),
                ]
            ],
        ],
    },
    CategoricalDescriptorInput: {
        "valids": [
            VALID_CATEGORICAL_DESCRIPTOR_INPUT_FEATURE_SPEC,
            {
                **VALID_CATEGORICAL_DESCRIPTOR_INPUT_FEATURE_SPEC,
                "allowed": [True, False, True],
            },
        ],
        "invalids": [
            *get_invalids(VALID_CATEGORICAL_DESCRIPTOR_INPUT_FEATURE_SPEC),
            *[
                {
                    **VALID_CATEGORICAL_INPUT_FEATURE_SPEC,
                    "categories": categories,
                    "descriptors": descriptors,
                    "values": values,
                }
                for categories, descriptors, values in [
                    (["c1", "c2"], ["d1", "d2", "d3"], []),
                    (["c1", "c2"], ["d1", "d2", "d3"], [[1, 2, 3]]),
                    (
                        ["c1", "c2"],
                        ["d1", "d2", "d3"],
                        [[1, 2, 3], [1, 2, 3], [1, 2, 3]],
                    ),
                    (["c1", "c2"], ["d1", "d2", "d3"], [[1, 2, 3], [1, 2]]),
                    (["c1", "c2"], ["d1", "d2", "d3"], [[1, 2, 3], [1, 2, 3, 4]]),
                    (["c1", "c2"], ["d1", "d2", "d3"], [[1, 2, 3], [1, 2, 3]]),
                ]
            ],
        ],
    },
    ContinuousOutput: {
        "valids": [
            VALID_CONTINUOUS_OUTPUT_FEATURE_SPEC,
            {
                **VALID_CONTINUOUS_OUTPUT_FEATURE_SPEC,
                "objective": objective,
            },
            {
                **VALID_CONTINUOUS_OUTPUT_FEATURE_SPEC,
                "objective": None,
            },
        ],
        "invalids": [*get_invalids(VALID_CONTINUOUS_OUTPUT_FEATURE_SPEC)],
    },
}


@pytest.mark.parametrize(
    "cls, spec",
    [(cls, valid) for cls, data in FEATURE_SPECS.items() for valid in data["valids"]],
)
def test_valid_feature_specs(cls, spec):
    res = cls(**spec)
    assert isinstance(res, cls)
    assert isinstance(res.__str__(), str)


@pytest.mark.parametrize(
    "cls, spec",
    [
        (cls, valid)
        for cls, data in FEATURE_SPECS.items()
        for valid in data["valids"]
        if cls != ContinuousOutput
    ],
)
def test_sample(cls, spec):
    feat = cls(**spec)
    samples = feat.sample(n=100)
    feat.validate_candidental(samples)


@pytest.mark.parametrize(
    "cls, spec",
    [(cls, valid) for cls, data in FEATURE_SPECS.items() for valid in data["valids"]],
)
def test_feature_serialize(cls, spec):
    res = cls(**spec)
    config = res.to_config()
    res2 = Feature.from_config(config)
    assert res == res2


@pytest.mark.parametrize(
    "cls, spec",
    [
        (cls, invalid)
        for cls, data in FEATURE_SPECS.items()
        for invalid in data["invalids"]
    ],
)
def test_invalid_feature_specs(cls, spec):
    with pytest.raises((ValueError, TypeError, KeyError, ValidationError)):
        _ = cls(**spec)


@pytest.mark.parametrize(
    "input_feature, expected",
    [
        (ContinuousInput(key="k", lower_bound=1, upper_bound=1), True),
        (ContinuousInput(key="k", lower_bound=1, upper_bound=2), False),
        (ContinuousInput(key="k", lower_bound=2, upper_bound=3), False),
        (
            ContinuousDescriptorInput(
                key="k",
                lower_bound=1,
                upper_bound=1,
                descriptors=["a", "b"],
                values=[1, 2],
            ),
            True,
        ),
        (
            ContinuousDescriptorInput(
                key="k",
                lower_bound=1,
                upper_bound=2,
                descriptors=["a", "b"],
                values=[1, 2],
            ),
            False,
        ),
        (
            ContinuousDescriptorInput(
                key="k",
                lower_bound=2,
                upper_bound=3,
                descriptors=["a", "b"],
                values=[1, 2],
            ),
            False,
        ),
    ],
)
def test_continuous_input_feature_is_fixed(input_feature, expected):
    assert input_feature.is_fixed() == expected


@pytest.mark.parametrize(
    "input_feature, expected",
    [
        (
            ContinuousInput(key="if1", lower_bound=0.5, upper_bound=4.0),
            (0.5, 4.0),
        ),
        (ContinuousInput(key="if1", lower_bound=2.5, upper_bound=2.9), (1, 3.0)),
        (ContinuousInput(key="if2", lower_bound=1.0, upper_bound=3.0), (1, 3.0)),
        (ContinuousInput(key="if2", lower_bound=1.0, upper_bound=1.0), (1, 1.0)),
    ],
)
def test_continuous_input_feature_get_real_feature_bounds(input_feature, expected):
    experiments = pd.DataFrame({"if1": [1.0, 2.0, 3.0], "if2": [1.0, 1.0, 1.0]})
    lower, upper = input_feature.get_real_feature_bounds(experiments[input_feature.key])
    assert (lower, upper) == expected


@pytest.mark.parametrize(
    "input_feature, values, strict",
    [
        (
            ContinuousInput(**VALID_CONTINUOUS_INPUT_FEATURE_SPEC),
            pd.Series([random.uniform(3.0, 5.3) for _ in range(20)]),
            True,
        ),
        (
            ContinuousInput(**VALID_CONTINUOUS_INPUT_FEATURE_SPEC),
            pd.Series([random.uniform(3.0, 5.3) for _ in range(20)]),
            False,
        ),
        (
            ContinuousInput(**VALID_FIXED_CONTINUOUS_INPUT_FEATURE_SPEC),
            pd.Series([random.uniform(3.0, 5.3) for _ in range(20)]),
            True,
        ),
        (
            ContinuousInput(**VALID_FIXED_CONTINUOUS_INPUT_FEATURE_SPEC),
            pd.Series([random.uniform(3.0, 5.3) for _ in range(20)]),
            False,
        ),
        (
            ContinuousInput(**VALID_FIXED_CONTINUOUS_INPUT_FEATURE_SPEC),
            pd.Series([3.0, 3.0, 3.0]),
            False,
        ),
    ],
)
def test_continuous_input_feature_validate_valid(input_feature, values, strict):
    input_feature.validate_experimental(values, strict)


@pytest.mark.parametrize(
    "input_feature, values, strict",
    [
        (
            ContinuousInput(**VALID_CONTINUOUS_INPUT_FEATURE_SPEC),
            pd.Series([3.0, "mama"]),
            True,
        ),
        (
            ContinuousInput(**VALID_CONTINUOUS_INPUT_FEATURE_SPEC),
            pd.Series([3.0, "mama"]),
            False,
        ),
        (
            ContinuousInput(**VALID_FIXED_CONTINUOUS_INPUT_FEATURE_SPEC),
            pd.Series([3.0, 3.0, 3.0]),
            True,
        ),
    ],
)
def test_continuous_input_feature_validate_invalid(input_feature, values, strict):
    with pytest.raises(ValueError):
        input_feature.validate_experimental(values, strict)


@pytest.mark.parametrize(
    "input_feature, values",
    [
        (
            ContinuousInput(**VALID_CONTINUOUS_INPUT_FEATURE_SPEC),
            pd.Series([random.uniform(3.0, 5.3) for _ in range(20)]),
        ),
        (
            ContinuousInput(**VALID_FIXED_CONTINUOUS_INPUT_FEATURE_SPEC),
            pd.Series([3.0, 3.0, 3.0]),
        ),
    ],
)
def test_continuous_input_feature_validate_candidental_valid(input_feature, values):
    input_feature.validate_candidental(values)


@pytest.mark.parametrize(
    "input_feature, values",
    [
        (
            ContinuousInput(**VALID_CONTINUOUS_INPUT_FEATURE_SPEC),
            pd.Series([3.1, "a"]),
        ),
        (
            ContinuousInput(**VALID_CONTINUOUS_INPUT_FEATURE_SPEC),
            pd.Series([2.9, 4.0]),
        ),
        (
            ContinuousInput(**VALID_CONTINUOUS_INPUT_FEATURE_SPEC),
            pd.Series([4.0, 6]),
        ),
        (
            ContinuousInput(**VALID_FIXED_CONTINUOUS_INPUT_FEATURE_SPEC),
            pd.Series([3.1, 3.2, 3.4]),
        ),
    ],
)
def test_continuous_input_feature_validate_candidental_invalid(input_feature, values):
    with pytest.raises(ValueError):
        input_feature.validate_candidental(values)


@pytest.mark.parametrize(
    "input_feature, expected",
    [
        (DiscreteInput(**VALID_FIXED_DISCRETE_INPUT_FEATURE_SPEC), True),
        (DiscreteInput(**VALID_DISCRETE_INPUT_FEATURE_SPEC), False),
    ],
)
def test_discrete_input_feature_is_fixed(input_feature, expected):
    assert input_feature.is_fixed() == expected


@pytest.mark.parametrize(
    "input_feature, expected_lower, expected_upper",
    [
        (
            DiscreteInput(**VALID_FIXED_DISCRETE_INPUT_FEATURE_SPEC),
            VALID_FIXED_DISCRETE_INPUT_FEATURE_SPEC["values"][0],
            VALID_FIXED_DISCRETE_INPUT_FEATURE_SPEC["values"][0],
        ),
        (
            DiscreteInput(**VALID_DISCRETE_INPUT_FEATURE_SPEC),
            VALID_DISCRETE_INPUT_FEATURE_SPEC["values"][0],
            VALID_DISCRETE_INPUT_FEATURE_SPEC["values"][1],
        ),
    ],
)
def test_discrete_input_feature_bounds(input_feature, expected_lower, expected_upper):
    assert input_feature.upper_bound == expected_upper
    assert input_feature.lower_bound == expected_lower


@pytest.mark.parametrize(
    "input_feature, expected",
    [
        (
            DiscreteInput(key="if1", values=[2.0, 3.0]),
            (1.0, 4.0),
        ),
        (
            DiscreteInput(key="if1", values=[0.0, 3.0]),
            (0.0, 4.0),
        ),
        (
            DiscreteInput(key="if1", values=[2.0, 5.0]),
            (1.0, 5.0),
        ),
    ],
)
def test_discrete_input_feature_get_real_feature_bounds(input_feature, expected):
    experiments = pd.DataFrame(
        {"if1": [1.0, 2.0, 3.0, 4.0], "if2": [1.0, 1.0, 1.0, 1.0]}
    )
    lower, upper = input_feature.get_real_feature_bounds(experiments[input_feature.key])
    assert (lower, upper) == expected


@pytest.mark.parametrize(
    "input_feature, values",
    [
        (
            DiscreteInput(**VALID_DISCRETE_INPUT_FEATURE_SPEC),
            pd.Series([random.choice([1.0, 2.0]) for _ in range(20)]),
        ),
        (
            DiscreteInput(**VALID_FIXED_DISCRETE_INPUT_FEATURE_SPEC),
            pd.Series([2.0, 2.0, 2.0]),
        ),
    ],
)
def test_discrete_input_feature_validate_candidental_valid(input_feature, values):
    input_feature.validate_candidental(values)


@pytest.mark.parametrize(
    "input_feature, values",
    [
        (
            DiscreteInput(**VALID_DISCRETE_INPUT_FEATURE_SPEC),
            pd.Series([random.choice([1.0, 3.0, 2.0]) for _ in range(20)]),
        ),
        (
            DiscreteInput(**VALID_FIXED_DISCRETE_INPUT_FEATURE_SPEC),
            pd.Series([1.0, 2.0, 2.0]),
        ),
    ],
)
def test_discrete_input_feature_validate_candidental_invalid(input_feature, values):
    with pytest.raises(ValueError):
        input_feature.validate_candidental(values)


@pytest.mark.parametrize(
    "input_feature, expected",
    [
        (
            CategoricalInput(key="if1", categories=["a", "b"], allowed=[True, True]),
            ["a", "b"],
        ),
        (
            CategoricalInput(key="if2", categories=["a", "b"], allowed=[True, True]),
            ["a", "b"],
        ),
        (
            CategoricalInput(key="if3", categories=["a", "b"], allowed=[True, False]),
            ["a"],
        ),
        (
            CategoricalInput(key="if4", categories=["a", "b"], allowed=[True, False]),
            ["a", "b"],
        ),
    ],
)
def test_categorical_input_feature_get_possible_categories(input_feature, expected):
    experiments = pd.DataFrame(
        {"if1": ["a", "b"], "if2": ["a", "a"], "if3": ["a", "a"], "if4": ["b", "b"]}
    )
    categories = input_feature.get_possible_categories(experiments[input_feature.key])
    assert categories == expected


@pytest.mark.parametrize(
    "input_feature, values, strict",
    [
        (
            CategoricalInput(**VALID_CATEGORICAL_INPUT_FEATURE_SPEC),
            pd.Series([random.choice(["c1", "c2", "c3"]) for _ in range(20)]),
            True,
        ),
        (
            CategoricalInput(**VALID_CATEGORICAL_INPUT_FEATURE_SPEC),
            pd.Series([random.choice(["c1", "c2", "c3"]) for _ in range(20)]),
            False,
        ),
        (
            CategoricalInput(**VALID_FIXED_CATEGORICAL_INPUT_FEATURE_SPEC),
            pd.Series([random.choice(["c1", "c2", "c3"]) for _ in range(20)]),
            True,
        ),
        (
            CategoricalInput(**VALID_FIXED_CATEGORICAL_INPUT_FEATURE_SPEC),
            pd.Series([random.choice(["c1", "c2", "c3"]) for _ in range(20)]),
            False,
        ),
        (
            CategoricalInput(**VALID_FIXED_CATEGORICAL_INPUT_FEATURE_SPEC),
            pd.Series(["c1", "c1"]),
            False,
        ),
    ],
)
def test_categorical_input_feature_validate_valid(input_feature, values, strict):
    input_feature.validate_experimental(values, strict)


@pytest.mark.parametrize(
    "input_feature, values, strict",
    [
        (
            CategoricalInput(**VALID_CATEGORICAL_INPUT_FEATURE_SPEC),
            pd.Series(["c1", "c4"]),
            True,
        ),
        (
            CategoricalInput(**VALID_CATEGORICAL_INPUT_FEATURE_SPEC),
            pd.Series(["c1", "c4"]),
            False,
        ),
        (
            CategoricalInput(**VALID_FIXED_CATEGORICAL_INPUT_FEATURE_SPEC),
            pd.Series(["c1", "c1"]),
            True,
        ),
        (
            CategoricalInput(
                key="a", categories=["c1", "c2", "c3"], allowed=[True, True, False]
            ),
            pd.Series(["c1", "c2"]),
            True,
        ),
    ],
)
def test_categorical_input_feature_validate_invalid(input_feature, values, strict):
    with pytest.raises(ValueError):
        input_feature.validate_experimental(values, strict)


@pytest.mark.parametrize(
    "input_feature, values",
    [
        (
            CategoricalInput(**VALID_CATEGORICAL_INPUT_FEATURE_SPEC),
            pd.Series([random.choice(["c1", "c2", "c3"]) for _ in range(20)]),
        ),
        (
            CategoricalInput(**VALID_FIXED_CATEGORICAL_INPUT_FEATURE_SPEC),
            pd.Series(["c1", "c1"]),
        ),
    ],
)
def test_categorical_input_feature_validate_candidental_valid(input_feature, values):
    input_feature.validate_candidental(values)


@pytest.mark.parametrize(
    "input_feature, values",
    [
        (
            CategoricalInput(**VALID_CATEGORICAL_INPUT_FEATURE_SPEC),
            pd.Series(["c1", "c2", "c4"]),
        ),
        (
            CategoricalInput(**VALID_FIXED_CATEGORICAL_INPUT_FEATURE_SPEC),
            pd.Series(["c1", "c2"]),
        ),
    ],
)
def test_categorical_input_feature_validate_candidental_invalid(input_feature, values):
    with pytest.raises(ValueError):
        input_feature.validate_candidental(values)


@pytest.mark.parametrize(
    "input_feature, expected",
    [
        (
            CategoricalDescriptorInput(
                key="if1",
                categories=["a", "b"],
                allowed=[True, True],
                descriptors=["alpha", "beta"],
                values=[[1, 2], [3, 4]],
            ),
            pd.DataFrame.from_dict(
                {"lower": [1, 2], "upper": [3, 4]},
                orient="index",
                columns=["alpha", "beta"],
            ),
        ),
        (
            CategoricalDescriptorInput(
                key="if2",
                categories=["a", "b", "c"],
                allowed=[True, False, True],
                descriptors=["alpha", "beta"],
                values=[[1, 2], [3, 4], [1, 5]],
            ),
            pd.DataFrame.from_dict(
                {"lower": [1, 2], "upper": [1, 5]},
                orient="index",
                columns=["alpha", "beta"],
            ),
        ),
        # (CategoricalInputFeature(key="if2", categories = ["a","b"], allowed = [True, True]), ["a","b"]),
        # (CategoricalInputFeature(key="if3", categories = ["a","b"], allowed = [True, False]), ["a"]),
        # (CategoricalInputFeature(key="if4", categories = ["a","b"], allowed = [True, False]), ["a", "b"]),
        # (ContinuousInputFeature(key="if1", lower_bound=2.5, upper_bound=2.9), (1,3.)),
        # (ContinuousInputFeature(key="if2", lower_bound=1., upper_bound=3.), (1,3.)),
        # (ContinuousInputFeature(key="if2", lower_bound=1., upper_bound=1.), (1,1.)),
    ],
)
def test_categorical_descriptor_feature_get_real_descriptor_bounds(
    input_feature, expected
):
    experiments = pd.DataFrame(
        {"if1": ["a", "b"], "if2": ["a", "c"], "if3": ["a", "a"], "if4": ["b", "b"]}
    )
    df_bounds = input_feature.get_real_descriptor_bounds(experiments[input_feature.key])
    assert_frame_equal(df_bounds, expected, check_like=True, check_dtype=False)


@pytest.mark.parametrize(
    "input_feature, values, strict",
    [
        (
            CategoricalDescriptorInput(
                **VALID_CATEGORICAL_DESCRIPTOR_INPUT_FEATURE_SPEC
            ),
            pd.Series([random.choice(["c1", "c2", "c3"]) for _ in range(20)]),
            True,
        ),
        (
            CategoricalDescriptorInput(
                **VALID_CATEGORICAL_DESCRIPTOR_INPUT_FEATURE_SPEC
            ),
            pd.Series([random.choice(["c1", "c2", "c3"]) for _ in range(20)]),
            False,
        ),
        (
            CategoricalDescriptorInput(
                **VALID_FIXED_CATEGORICAL_DESCRIPTOR_INPUT_FEATURE_SPEC
            ),
            pd.Series([random.choice(["c1", "c2", "c3"]) for _ in range(20)]),
            True,
        ),
        (
            CategoricalDescriptorInput(
                **VALID_FIXED_CATEGORICAL_DESCRIPTOR_INPUT_FEATURE_SPEC
            ),
            pd.Series([random.choice(["c1", "c2", "c3"]) for _ in range(20)]),
            False,
        ),
        (
            CategoricalDescriptorInput(
                **VALID_FIXED_CATEGORICAL_DESCRIPTOR_INPUT_FEATURE_SPEC
            ),
            pd.Series(["c1", "c1"]),
            False,
        ),
        (
            CategoricalDescriptorInput(
                **VALID_ALLOWED_CATEGORICAL_DESCRIPTOR_INPUT_FEATURE_SPEC
            ),
            pd.Series(["c2", "c3"]),
            False,
        ),
    ],
)
def test_categorical_descriptor_input_feature_validate_valid(
    input_feature, values, strict
):
    input_feature.validate_experimental(values, strict)


@pytest.mark.parametrize(
    "input_feature, values, strict",
    [
        (
            CategoricalDescriptorInput(
                **VALID_CATEGORICAL_DESCRIPTOR_INPUT_FEATURE_SPEC
            ),
            pd.Series(["c1", "c4"]),
            True,
        ),
        (
            CategoricalDescriptorInput(
                **VALID_CATEGORICAL_DESCRIPTOR_INPUT_FEATURE_SPEC
            ),
            pd.Series(["c1", "c4"]),
            False,
        ),
        (
            CategoricalDescriptorInput(
                **VALID_FIXED_CATEGORICAL_DESCRIPTOR_INPUT_FEATURE_SPEC
            ),
            pd.Series(["c1", "c1"]),
            True,
        ),
        (
            CategoricalDescriptorInput(
                **VALID_ALLOWED_CATEGORICAL_DESCRIPTOR_INPUT_FEATURE_SPEC
            ),
            pd.Series(["c2", "c3"]),
            True,
        ),
    ],
)
def test_categorical_descriptor_input_feature_validate_invalid(
    input_feature, values, strict
):
    with pytest.raises(ValueError):
        input_feature.validate_experimental(values, strict)


@pytest.mark.parametrize(
    "input_feature, expected",
    [
        (
            CategoricalInput(key="k", categories=categories, allowed=allowed),
            expected,
        )
        for categories, allowed, expected in [
            # ([], None, False),
            # (["1"], None, True),
            # (["1"], [True], True),
            (["1", "2"], None, False),
            (["1", "2", "3", "4"], [True, False, False, False], True),
            (["1", "2", "3", "4"], [True, True, False, True], False),
        ]
    ],
)
def test_categorical_input_feature_is_fixed(input_feature, expected):
    print(expected, input_feature)
    assert input_feature.is_fixed() == expected


@pytest.mark.parametrize(
    "input_feature, expected",
    [
        (
            CategoricalInput(key="k", categories=categories, allowed=allowed),
            expected,
        )
        for categories, allowed, expected in [
            (["a", "b", "c"], [True, True, True], ["a", "b", "c"]),
            (["a", "b", "c"], [False, True, True], ["b", "c"]),
        ]
    ],
)
def test_categorical_input_feature_allowed_categories(input_feature, expected):
    assert input_feature.get_allowed_categories() == expected


@pytest.mark.parametrize(
    "input_feature, expected",
    [
        (
            CategoricalInput(key="k", categories=categories, allowed=allowed),
            expected,
        )
        for categories, allowed, expected in [
            (["a", "b", "c"], [True, True, True], []),
            (["a", "b", "c"], [False, True, True], ["a"]),
        ]
    ],
)
def test_categorical_input_feature_forbidden_categories(input_feature, expected):
    assert input_feature.get_forbidden_categories() == expected


@pytest.mark.parametrize(
    "categories, descriptors, values",
    [
        (["c1", "c2"], ["d1", "d2", "d3"], [[1, 2, 3], [4, 5, 6]]),
        (
            ["c1", "c2", "c3", "c4"],
            ["d1", "d2", "d3"],
            [
                [1, 2, 3],
                [4, 5, 6],
                [4, 5, 6],
                [4, 5, 6],
            ],
        ),
    ],
)
def test_categorical_descriptor_input_feature_as_dataframe(
    categories, descriptors, values
):
    f = CategoricalDescriptorInput(
        key="k", categories=categories, descriptors=descriptors, values=values
    )
    df = f.to_df()
    assert len(df.columns) == len(descriptors)
    assert len(df) == len(categories)
    assert df.values.tolist() == values


@pytest.mark.parametrize(
    "descriptors, values",
    [
        (["a", "b"], [1.0, 2.0]),
        (["a", "b", "c"], [1.0, 2.0, 3.0]),
    ],
)
def test_continuous_descriptor_input_feature_as_dataframe(descriptors, values):
    f = ContinuousDescriptorInput(
        key="k",
        lower_bound=1.0,
        upper_bound=2.0,
        descriptors=descriptors,
        values=values,
    )
    df = f.to_df()
    assert len(df.columns) == len(descriptors)
    assert len(df) == 1
    assert df.values.tolist()[0] == values


@pytest.mark.parametrize(
    "categories, descriptors, values",
    [
        (["c1", "c2"], ["d1", "d2", "d3"], [[1, 2, 3], [4, 5, 6]]),
        (
            ["c1", "c2", "c3", "c4"],
            ["d1", "d2", "d3"],
            [
                [1, 2, 3],
                [4, 5, 6],
                [4, 5, 6],
                [4, 5, 6],
            ],
        ),
    ],
)
def test_categorical_descriptor_input_feature_from_dataframe(
    categories, descriptors, values
):
    df = pd.DataFrame.from_dict(
        {category: v for category, v in zip(categories, values)},
        orient="index",
        columns=descriptors,
    )
    f = CategoricalDescriptorInput.from_df("k", df)
    assert f.categories == categories
    assert f.descriptors == descriptors
    assert f.values == values


cont = ContinuousInput(**VALID_CONTINUOUS_INPUT_FEATURE_SPEC)
cat = CategoricalInput(**VALID_CATEGORICAL_INPUT_FEATURE_SPEC)
cat_ = CategoricalDescriptorInput(**VALID_CATEGORICAL_DESCRIPTOR_INPUT_FEATURE_SPEC)
out = ContinuousOutput(**VALID_CONTINUOUS_OUTPUT_FEATURE_SPEC)


@pytest.mark.parametrize(
    "unsorted_list, sorted_list",
    [
        (
            [cont, cat_, cat, out],
            [cont, cat, cat_, out],
        ),
        (
            [cont, cat_, cat, out, cat_, out],
            [cont, cat, cat_, cat_, out, out],
        ),
        (
            [cont, out],
            [cont, out],
        ),
        (
            [out, cont],
            [cont, out],
        ),
    ],
)
def test_feature_sorting(unsorted_list, sorted_list):
    assert list(sorted(unsorted_list)) == sorted_list