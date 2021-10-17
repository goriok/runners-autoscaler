from logger import logger
from helpers import string_to_base64string
from apis.kubernetes.base import KubernetesBaseAPIService, KubernetesSpecFileAPIService
from apis.bitbucket.base import BitbucketWorkspace, BitbucketWorkspaceRunner, BitbucketRepositoryRunner


# Bitbucket Cloud API
def get_bitbucket_runners(workspace, repository=None):
    logger.info(f"Getting runner on Bitbucket workspace: {workspace} ...")

    if repository:
        repository_runner_api = BitbucketRepositoryRunner()
        runners_data = repository_runner_api.get_runners(workspace, repository)
    else:
        workspace_runner_api = BitbucketWorkspaceRunner()
        runners_data = workspace_runner_api.get_runners(workspace)

    return runners_data['values']


def create_bitbucket_runner(workspace, repository=None, name='test', labels=('test',)):
    logger.info(f"Starting to setup runner on Bitbucket workspace: {workspace} ...")
    workspace_runner_api = BitbucketWorkspaceRunner()
    data = workspace_runner_api.create_runner(workspace, name, tuple(labels))
    logger.info(f"Runner created on Bitbucket workspace: {workspace}")
    logger.debug(data)

    runner_data = {
        "accountUuid": None,
        "repositoryUuid": repository,
        "runnerUuid": data["uuid"].strip('{}'),
        "oauthClientId_base64": string_to_base64string(data["oauth_client"]["id"]),
        "oauthClientSecret_base64": string_to_base64string(data["oauth_client"]["secret"]),
    }
    logger.debug(runner_data)

    workspace_api = BitbucketWorkspace()
    workspace_data = workspace_api.get_workspace(workspace)
    logger.debug(workspace_data)
    runner_data['accountUuid'] = workspace_data['uuid'].strip('{}')

    return runner_data


def delete_bitbucket_runner(workspace, repository=None, runner_uuid=None):
    logger.info(f"Starting to delete runner {runner_uuid} from Bitbucket workspace: {workspace} ...")
    workspace_runner_api = BitbucketWorkspaceRunner()
    workspace_runner_api.delete_runner(workspace, runner_uuid)


# local Kubernetes
def validate_kubernetes():
    logger.warning("Starting validating local Kubernetes...")

    kube_base_api = KubernetesBaseAPIService()

    kubernetes_version = kube_base_api.get_kubernetes_version()
    logger.info(f"Your local Kubernetes: {kubernetes_version}")

    kube_base_api.get_or_create_kubernetes_namespace()


def setup_job(runner_data):
    logger.info("Starting to setup local kubernetes job ...")

    kube_spec_file_api = KubernetesSpecFileAPIService()
    runner_spec_filename = kube_spec_file_api.create_kube_spec_file(runner_data)
    result = kube_spec_file_api.apply_kubernetes_spec_file(runner_spec_filename)

    logger.info(result)


def delete_job(runner_uuid):
    kube_base_api = KubernetesBaseAPIService()
    kube_base_api.delete_job(runner_uuid)
    kube_spec_file_api = KubernetesSpecFileAPIService()
    kube_spec_file_api.delete_kube_spec_file(runner_uuid)


def read_from_config():
    pass
