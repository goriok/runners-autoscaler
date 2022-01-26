import json
import logging
import os
from unittest import TestCase, mock

import autoscaler.start_command as scale
import pytest

test_config = [
    {
        "name": "Runner repository group",
        "workspace": "test",
        "repository": "runner-test",
        "labels": ["self.hosted", "test", "linux"],
        "namespace": "rg-1",
        "strategy": "percentageRunnersIdle",
        "parameters": {
            "min": 1,
            "max": 10,
            "scaleUpThreshold": 0.5,
            "scaleDownThreshold": 0.2,
            "scaleUpMultiplier": 1.5,
            "scaleDownMultiplier": 0.5
        }
    }
]

test_config_no_namespace = [
    {
        "name": "Runner repository group",
        "workspace": "test",
        "repository": "runner-test",
        "labels": ["self.hosted", "test", "linux"],
        "strategy": "percentageRunnersIdle",
        "parameters": {
            "min": 1,
            "max": 10,
            "scaleUpThreshold": 0.5,
            "scaleDownThreshold": 0.2,
            "scaleUpMultiplier": 1.5,
            "scaleDownMultiplier": 0.5
        }
    }
]


@mock.patch.dict(os.environ, {'BITBUCKET_USERNAME': 'test', 'BITBUCKET_APP_PASSWORD': 'test'})
class ScaleTestCase(TestCase):

    @pytest.fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self.caplog = caplog

    def test_autoscaler_config_required(self):
        with pytest.raises(Exception) as pytest_wrapped_e:
            scale.main()

        self.assertEqual(pytest_wrapped_e.type, Exception)
        self.assertIn("Exception: AUTOSCALER_CONFIG variable missing.", str(pytest_wrapped_e))

    @mock.patch.dict(os.environ, {'AUTOSCALER_CONFIG': json.dumps(test_config)})
    @mock.patch('autoscaler.start_command.TESTING_BREAK_LOOP', True)
    @mock.patch('autoscaler.start_command.BITBUCKET_RUNNER_API_POLLING_INTERVAL', 0.1)
    @mock.patch('autoscaler.runner.check_kubernetes_namespace')
    @mock.patch('autoscaler.strategy.pct_runners_idle.PctRunnersIdleScaler.run')
    def test_main(self, mock_autoscaler, mock_namespace):
        mock_namespace.return_value = None
        mock_autoscaler.return_value = None

        with self.caplog.at_level(logging.INFO):
            scale.main()

        self.assertIn(f'Autoscaler config: {test_config}', self.caplog.text)
        assert mock_namespace.called
        self.assertIn('AUTOSCALER next attempt in 0.1 seconds...\n', self.caplog.text)
        assert mock_autoscaler.called
