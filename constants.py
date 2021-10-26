import os

# The name of a Runner's Kubernetes job spec template
TEMPLATE_FILE_NAME = "job.yaml.template"
# The directory for Runners Kubernetes job spec files stored to
RUNNER_KUBERNETES_SPECS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bitbucket-runner-k8s-specs")
# The namespace in Kubernetes for Runners Kubernetes jobs. You can override it in configuration file.
DEFAULT_RUNNER_KUBERNETES_NAMESPACE = "bitbucket-runner"
# SLEEP TIME in seconds before the next runner setup
DEFAULT_SLEEP_TIME_RUNNER_SETUP = 3  # seconds
# SLEEP TIME in seconds before the next runner delete
DEFAULT_SLEEP_TIME_RUNNER_DELETE = 3  # seconds
