import os

"""
Parameters that cannot be modified by user.
"""
# The name of a Runner's Kubernetes job spec template
TEMPLATE_FILE_NAME = "job.yaml.template"

# The directory for Runners Kubernetes job spec files stored to
RUNNER_KUBERNETES_SPECS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bitbucket-runner-k8s-specs")

"""
Parameters that can be modified by user.
"""
# The namespace in Kubernetes for Runners Kubernetes jobs. To override it you need also update role-spec.yml.
DEFAULT_RUNNER_KUBERNETES_NAMESPACE = os.getenv("DEFAULT_RUNNER_KUBERNETES_NAMESPACE", "bitbucket-runner")

# SLEEP TIME in seconds before the next runner setup
DEFAULT_SLEEP_TIME_RUNNER_SETUP = int(os.getenv("DEFAULT_SLEEP_TIME_RUNNER_SETUP", 5))  # seconds

# SLEEP TIME in seconds before the next runner delete
DEFAULT_SLEEP_TIME_RUNNER_DELETE = int(os.getenv("DEFAULT_SLEEP_TIME_RUNNER_DELETE", 5))  # seconds

# SLEEP TIME in seconds before the next check runners statuses on Bitbucket Cloud
BITBUCKET_RUNNER_API_POLLING_INTERVAL = int(os.getenv("BITBUCKET_RUNNER_API_POLLING_INTERVAL", 10 * 60))  # seconds

# RUNNER COOL DOWN PERIOD in seconds prevent delete fresh runners created less than period
RUNNER_COOL_DOWN_PERIOD = int(os.getenv("RUNNER_COOL_DOWN_PERIOD", 5 * 60))  # seconds
