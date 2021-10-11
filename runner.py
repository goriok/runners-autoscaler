import os
from pathlib import Path

from jinja2 import FileSystemLoader, Environment

from apis.bitbucket.base import BitbucketWorkspace, BitbucketWorkspaceRunner, BitbucketRepositoryRunner
from apis.base import BaseSubprocessAPIService
from helpers import string_to_base64string
from constants import TEMPLATE_FILE_NAME, RUNNER_KUBERNETES_SPECS_DIR, RUNNER_KUBERNETES_NAMESPACE
from logger import logger


def create_runner(workspace, repository=None, name='test', labels=['test']):
    logger.info(f"Starting to setup runner on Bitbucket workspace: {workspace} ...")
    workspace_runner_api = BitbucketWorkspaceRunner()
    data = workspace_runner_api.create_runner(workspace, name, labels)
    logger.info(f"Runner created on Bitbucket workspace: {workspace}")
    logger.debug(data)

    runner_data = {
        "accountUuid": None,
        "repositoryUuid": None,
        "runnerUuid": data["uuid"].strip('{}'),
        "oauthClientId_base64": string_to_base64string(data["oauth_client"]["id"]),
        "oauthClientSecret_base64": string_to_base64string(data["oauth_client"]["secret"]),
        "runnerLabel": labels[0]
    }
    logger.debug(runner_data)

    workspace_api = BitbucketWorkspace()
    workspace_data = workspace_api.get_workspace(workspace)
    logger.debug(workspace_data)
    runner_data['accountUuid'] = workspace_data['uuid'].lstrip('{').rstrip('}')

    return runner_data


def delete_runner(workspace, repository=None, runner_uuid=None):
    logger.info(f"Starting to delete runner {runner_uuid} from Bitbucket workspace: {workspace} ...")
    workspace_runner_api = BitbucketWorkspaceRunner()
    workspace_runner_api.delete_runner(workspace, runner_uuid)


def create_kube_spec_file(runner_data):
    # process template to k8s spec

    logger.info("Start processing template to create Runners job Kubernetes spec file...")

    template_loader = FileSystemLoader("./")
    template_env = Environment(
        loader=template_loader,
        variable_start_string="<%",
        variable_end_string="%>"
    )
    job_template = template_env.get_template(TEMPLATE_FILE_NAME)

    output = job_template.render(runner_data)

    logger.debug(output)

    runner_spec_filename = os.path.join(RUNNER_KUBERNETES_SPECS_DIR, f'runner-{runner_data["runnerUuid"][:8]}.yaml')
    with open(runner_spec_filename, 'w') as f:
        f.write(output)

    logger.info(f"Kubernetes spec stored to {runner_spec_filename} file.")

    return runner_spec_filename


def delete_kube_spec_file(runner_uuid):
    runner_spec_filename = os.path.join(RUNNER_KUBERNETES_SPECS_DIR, f'runner-{runner_uuid[:8]}.yaml')
    logger.info(f"Deleting runner job kubespec file {runner_spec_filename}")
    Path(runner_spec_filename).unlink(missing_ok=True)


def validate_kubernetes():
    logger.warning("Starting validating local Kubernetes...")

    kubernetes_version = get_kubernetes_version()
    logger.info(f"Your local Kubernetes: {kubernetes_version}")

    get_or_create_kubernetes_namespace()


def setup_job(runner_spec_filename):
    logger.info("Starting to setup local kubernetes job ...")

    result = apply_kubernetes_spec_file(runner_spec_filename)

    logger.info(result)


def delete_job(runner_uuid):
    cmd = f"kubectl -n {RUNNER_KUBERNETES_NAMESPACE} delete job -l runnerUuid={runner_uuid}"
    api = BaseSubprocessAPIService()
    result = api.run_command(cmd.split())

    return result


def get_runners(workspace, repository=None):
    logger.info(f"Getting runner on Bitbucket workspace: {workspace} ...")

    if repository:
        repository_runner_api = BitbucketRepositoryRunner()
        runners_data = repository_runner_api.get_runners(workspace, repository)
    else:
        workspace_runner_api = BitbucketWorkspaceRunner()
        runners_data = workspace_runner_api.get_runners(workspace)

    return runners_data['values']


def get_kubernetes_version():
    cmd = "kubectl version"
    api = BaseSubprocessAPIService()
    result = api.run_command(cmd.split())

    return result


def get_or_create_kubernetes_namespace(namespace=RUNNER_KUBERNETES_NAMESPACE):
    logger.info(f"Checking for the {namespace} namespace...")

    cmd = f"kubectl get namespace {namespace}"
    api = BaseSubprocessAPIService()

    result = api.run_command(cmd.split(), fail_if_error=False)
    # check for fails code
    if result[1] == 1:
        result = create_kubernetes_namespace()

    return result


def create_kubernetes_namespace(namespace=RUNNER_KUBERNETES_NAMESPACE):
    # kubectl create namespace bitbucket-runner --dry-run=client -o yaml | kubectl apply -f -
    logger.info(f"Creating the {namespace} namespace...")

    cmd_create_namespace = f"kubectl create namespace {namespace} --dry-run=client -o yaml"
    cmd_apply = "kubectl apply -f -"

    api = BaseSubprocessAPIService()
    result = api.run_piped_command(cmd_create_namespace, cmd_apply)

    return result


def apply_kubernetes_spec_file(runner_spec_filename):
    cmd = f"kubectl -n {RUNNER_KUBERNETES_NAMESPACE} apply -f {runner_spec_filename}"
    api = BaseSubprocessAPIService()
    result = api.run_command(cmd.split())

    return result


def read_from_config():
    pass
