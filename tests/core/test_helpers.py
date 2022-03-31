import os
from unittest import TestCase, mock
import yaml
import pytest
from autoscaler.core.helpers import read_yaml_file

from tests.helpers import capture_output


@mock.patch.dict(os.environ, {'BITBUCKET_USERNAME': 'test', 'BITBUCKET_APP_PASSWORD': 'test', 'DEBUG': 'true'})
class RunnerTestCase(TestCase):

    @mock.patch('yaml.safe_load')
    def test_read_from_config(self, mock_config):
        mock_config.side_effect = yaml.YAMLError

        with capture_output():
            with pytest.raises(SystemExit) as pytest_wrapped_e:
                read_yaml_file('tests/resources/test_config.yaml')

        self.assertTrue(mock_config.called)
        self.assertEqual(pytest_wrapped_e.type, SystemExit)
