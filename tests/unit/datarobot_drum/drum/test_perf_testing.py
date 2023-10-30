#
#  Copyright 2023 DataRobot, Inc. and its affiliates.
#
#  All rights reserved.
#  This is proprietary source code of DataRobot, Inc. and its affiliates.
#  Released under the terms of DataRobot Tool and Utility Agreement.
#
import json
from argparse import Namespace
from tempfile import NamedTemporaryFile
from unittest.mock import patch, Mock

import numpy as np
import pytest
import pandas as pd
import responses

from datarobot_drum.drum.enum import TargetType
from datarobot_drum.drum.perf_testing import CMRunTests
from datarobot_drum.drum.utils.structured_input_read_utils import StructuredInputReadUtils


@pytest.fixture
def module_under_test():
    return "datarobot_drum.drum.perf_testing"


@pytest.fixture
def target():
    return "some-target"


@pytest.fixture
def mock_input(target):
    with NamedTemporaryFile(suffix=".csv") as temp_file:

        data = [[1, 2, 3]] * 100
        df = pd.DataFrame(data, columns=[target, target + "a", target + "b"])
        df.to_csv(temp_file)
        yield temp_file


@pytest.fixture
def mock_options(mock_input, target_type):
    """Generated by printing out actual options in 
    unit.datarobot_drum.drum.test_drum.TestCMRunnerRunTestPredict.test_calls_cm_run_test_class_correctly
    """
    return Namespace(
        subparser_name="fit",
        code_dir="/tmp/tmpgcqozt0coutput-dir",
        verbose=False,
        input=mock_input.name,
        positive_class_label=None,
        negative_class_label=None,
        class_labels=None,
        class_labels_file=None,
        logging_level="warning",
        docker=None,
        skip_deps_install=False,
        memory=None,
        output="/dev/null",
        target="some-target",
        target_csv=None,
        row_weights=None,
        row_weights_csv=None,
        skip_predict=False,
        num_rows="ALL",
        sparse_column_file=None,
        parameter_file=None,
        show_stacktrace=False,
        target_type=target_type.value,
        disable_strict_validation=False,
        enable_fit_metadata=False,
        user_secrets_mount_path=None,
        user_secrets_prefix=None,
        monitor=False,
        monitor_embedded=False,
        model_id=None,
        deployment_id=None,
        monitor_settings=None,
        model_config={
            "environmentID": "5e8c889607389fe0f466c72d",
            "name": "joe",
            "targetType": "regression",
            "type": "training",
            "validation": {"input": "hello"},
        },
        default_parameter_values={},
    )


@pytest.fixture
def target_type():
    return TargetType.BINARY


@pytest.fixture
def mock_read_structured_input_file_as_df():
    with patch.object(StructuredInputReadUtils, "read_structured_input_file_as_df") as mock_func:
        yield mock_func


@pytest.fixture
def cm_run_tests(mock_options, target_type, mock_read_structured_input_file_as_df):
    _ = mock_read_structured_input_file_as_df
    return CMRunTests(mock_options, target_type, schema_validator=Mock())


@pytest.fixture
def mock_server_address():
    return "https://gimme-the-stufffffff.com"


@pytest.fixture
def mock_drum_server_run_class(module_under_test, mock_server_address):
    with patch(f"{module_under_test}.DrumServerRun") as mock_class:
        instance = mock_class.return_value.__enter__.return_value
        instance.url_server_address = mock_server_address
        yield mock_class


@pytest.fixture
def mock_np_isclose(module_under_test):
    with patch(f"{module_under_test}.np.isclose") as mock_func:
        mock_func.return_value = np.array([True, True])
        yield mock_func


@pytest.mark.usefixtures("mock_drum_server_run_class", "mock_np_isclose")
class TestTestPredictionSideEffects:
    @pytest.fixture
    def predict_response(self, mock_server_address):
        data = [[1, 2, 3]] * 100
        responses.add(
            responses.POST,
            f"{mock_server_address}/predict/",
            body=json.dumps({"predictions": data}),
            content_type="application/json",
        )
        yield

    @responses.activate
    @pytest.mark.usefixtures("predict_response")
    def test_calls_drum_server_run_correctly_no_mount_path(
        self, cm_run_tests, mock_drum_server_run_class, mock_options, target_type
    ):
        cm_run_tests.check_prediction_side_effects()
        labels = cm_run_tests.resolve_labels(target_type, mock_options)

        mock_drum_server_run_class.assert_called_once_with(
            target_type.value,
            labels,
            mock_options.code_dir,
            verbose=mock_options.verbose,
            user_secrets_mount_path=None,
        )

    @responses.activate
    @pytest.mark.usefixtures("predict_response")
    def test_calls_drum_server_run_correctly_with_mount_path(
        self, cm_run_tests, mock_drum_server_run_class, mock_options, target_type
    ):
        mount_path = "/a/b/c/d/"
        mock_options.user_secrets_mount_path = mount_path
        cm_run_tests.check_prediction_side_effects()
        labels = cm_run_tests.resolve_labels(target_type, mock_options)

        mock_drum_server_run_class.assert_called_once_with(
            target_type.value,
            labels,
            mock_options.code_dir,
            verbose=mock_options.verbose,
            user_secrets_mount_path=mount_path,
        )


@pytest.fixture
def mock_read_x_data_from_response(module_under_test):
    with patch(f"{module_under_test}.read_x_data_from_response") as mock_func:
        yield mock_func


@pytest.mark.usefixtures("mock_drum_server_run_class", "mock_read_x_data_from_response")
class TestCheckTransformServer:
    @pytest.fixture
    def transform_response(self, mock_server_address):
        responses.add(
            responses.POST, f"{mock_server_address}/transform/", content_type="application/json",
        )
        yield

    @responses.activate
    @pytest.mark.usefixtures("transform_response")
    def test_calls_drum_server_run_correctly_with_mount_path(
        self, cm_run_tests, mock_drum_server_run_class, mock_options, target_type
    ):
        with NamedTemporaryFile() as temp_file:
            cm_run_tests.check_transform_server(temp_file)
        labels = cm_run_tests.resolve_labels(target_type, mock_options)

        mock_drum_server_run_class.assert_called_once_with(
            target_type.value,
            labels,
            mock_options.code_dir,
            verbose=mock_options.verbose,
            user_secrets_mount_path=None,
        )

    @responses.activate
    @pytest.mark.usefixtures("transform_response")
    def test_calls_drum_server_run_correctly_no_mount_path(
        self, cm_run_tests, mock_drum_server_run_class, mock_options, target_type
    ):
        mount_path = "/a/b/c/d/"
        mock_options.user_secrets_mount_path = mount_path
        with NamedTemporaryFile() as temp_file:
            cm_run_tests.check_transform_server(temp_file)
        labels = cm_run_tests.resolve_labels(target_type, mock_options)

        mock_drum_server_run_class.assert_called_once_with(
            target_type.value,
            labels,
            mock_options.code_dir,
            verbose=mock_options.verbose,
            user_secrets_mount_path=mount_path,
        )
