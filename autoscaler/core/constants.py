import os


# The name of a Runner's Kubernetes job spec template
TEMPLATE_FILE_NAME = "job.yaml.template"

# The namespace in Kubernetes for Runners Kubernetes jobs.
DEFAULT_RUNNER_KUBERNETES_NAMESPACE = "bitbucket-runner-control-plane"

# SLEEP TIME in seconds before the next runner setup
DEFAULT_SLEEP_TIME_RUNNER_SETUP = 5  # seconds

# SLEEP TIME in seconds before the next runner delete
DEFAULT_SLEEP_TIME_RUNNER_DELETE = 5  # seconds

# SLEEP TIME in seconds before the next check runners statuses on Bitbucket Cloud
BITBUCKET_RUNNER_API_POLLING_INTERVAL = 10 * 60  # seconds

# RUNNER COOL DOWN PERIOD in seconds prevent delete fresh runners created less than period
RUNNER_COOL_DOWN_PERIOD = 5 * 60  # seconds

# Max allowed groups for runner config map
MAX_GROUPS_COUNT = 10

# Default memory for Kubernetes job resources and limits
DEFAULT_MEMORY = "4Gi"

# Default cpu for Kubernetes job resources and limits
DEFAULT_CPU = "1000m"

# Mark runners created by autoscaler tool
AUTOSCALER_RUNNER = 'autoscaler.created'

# Default labels from Bitbucket API
DEFAULT_LABELS = frozenset({'self.hosted', 'linux', AUTOSCALER_RUNNER})

DEST_TEMPLATE_FILE_PATH = os.getenv('DEST_TEMPLATE_PATH', default='/home/bitbucket/autoscaler/resources/')
