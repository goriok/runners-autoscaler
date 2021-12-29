import yaml

from constants import DEFAULT_RUNNER_KUBERNETES_NAMESPACE
from logger import logger
from helpers import string_to_base64string, fail
from apis.kubernetes.base import KubernetesBaseAPIService, KubernetesSpecFileAPIService, KubernetesPythonAPIService
from apis.bitbucket.base import (BitbucketWorkspace, BitbucketRepository, BitbucketWorkspaceRunner,
                                 BitbucketRepositoryRunner)


# Bitbucket Cloud API
def get_bitbucket_runners(workspace, repository=None):
    msg = f"Getting runners on Bitbucket workspace: {workspace}"

    if repository:
        logger.info(f"{msg} repository: {repository} ...")

        repository_runner_api = BitbucketRepositoryRunner()
        runners_data = repository_runner_api.get_runners(workspace, repository)
    else:
        logger.info(f"{msg} ...")

        workspace_runner_api = BitbucketWorkspaceRunner()
        runners_data = workspace_runner_api.get_runners(workspace)

    return runners_data['values']


def create_bitbucket_runner(workspace, repository=None, name='test', labels=('test',)):
    start_msg = f"Starting to setup runner on Bitbucket workspace: {workspace}"
    create_complete_msg = f"Runner created on Bitbucket workspace: {workspace}"

    if repository:
        logger.info(f"{start_msg} repository: {repository} ...")

        repository_runner_api = BitbucketRepositoryRunner()
        data = repository_runner_api.create_runner(workspace, repository, name, tuple(labels))

        logger.info(f"{create_complete_msg} repository: {repository}")
    else:
        logger.info(f"{start_msg} ...")

        workspace_runner_api = BitbucketWorkspaceRunner()
        data = workspace_runner_api.create_runner(workspace, name, tuple(labels))

        logger.info(f"{create_complete_msg}")

    logger.debug(data)

    runner_data = {
        "accountUuid": None,
        "repositoryUuid": None,
        "runnerUuid": data["uuid"].strip('{}'),
        "oauthClientId_base64": string_to_base64string(data["oauth_client"]["id"]),
        "oauthClientSecret_base64": string_to_base64string(data["oauth_client"]["secret"]),
    }

    logger.debug(runner_data)

    workspace_api = BitbucketWorkspace()
    workspace_data = workspace_api.get_workspace(workspace)

    logger.debug(workspace_data)

    runner_data['accountUuid'] = workspace_data['uuid'].strip('{}')

    if repository:
        repository_api = BitbucketRepository()
        repository_data = repository_api.get_repository(workspace, repository)

        logger.debug(repository_data)

        runner_data['repositoryUuid'] = repository_data['uuid'].strip('{}')

    return runner_data


def delete_bitbucket_runner(workspace, repository=None, runner_uuid=None):
    msg = f"Starting to delete runner {runner_uuid} from Bitbucket workspace: {workspace}"

    if repository:
        logger.info(f"{msg} repository: {repository} ...")

        repository_runner_api = BitbucketRepositoryRunner()
        repository_runner_api.delete_runner(workspace, repository, runner_uuid)
    else:
        logger.info(f"{msg} ...")

        workspace_runner_api = BitbucketWorkspaceRunner()
        workspace_runner_api.delete_runner(workspace, runner_uuid)


# local Kubernetes
def validate_kubernetes(incluster=False):
    logger.info("Starting Kubernetes cluster validation…...")

    if incluster:
        # TODO refactor it
        logger.info("Starting Kubernetes cluster validation…...")
    else:
        kube_base_api = KubernetesBaseAPIService()

        kubernetes_config = kube_base_api.get_kubernetes_config()
        logger.debug(kubernetes_config)

        kubernetes_version = kube_base_api.get_kubernetes_version()

        logger.info(f"Kubernetes details: {kubernetes_version}")


def check_kubernetes_namespace(namespace=DEFAULT_RUNNER_KUBERNETES_NAMESPACE, incluster=False):
    logger.info(f"Checking for the {namespace} namespace...")

    if incluster:
        # TODO refactor it
        kube_python_api = KubernetesPythonAPIService()
        kube_python_api.get_or_create_kubernetes_namespace(namespace=namespace)
    else:
        kube_base_api = KubernetesBaseAPIService()
        kube_base_api.get_or_create_kubernetes_namespace(namespace=namespace)


def setup_job(runner_data, incluster=False):
    logger.info("Starting to setup the Kubernetes job ...")

    if incluster:
        # TODO refactor it
        kube_spec_file_api = KubernetesSpecFileAPIService()
        runner_job_spec = kube_spec_file_api.generate_kube_spec_file(runner_data)

        # TODO improve workflow with k8s spec template for runner job
        # runner-config.yaml.template
        runner_spec = yaml.safe_load(runner_job_spec)
        job_secret_spec = runner_spec['items'][0]
        job_spec = runner_spec['items'][1]

        kube_python_api = KubernetesPythonAPIService()
        kube_python_api.create_secret(job_secret_spec, runner_data['runnerNamespace'])
        kube_python_api.create_job(job_spec, runner_data['runnerNamespace'])

        logger.info("Job created.")
    else:
        kube_spec_file_api = KubernetesSpecFileAPIService()
        runner_job_spec = kube_spec_file_api.create_kube_spec_file(runner_data)
        result = kube_spec_file_api.apply_kubernetes_spec_file(runner_job_spec,
                                                               namespace=runner_data['runnerNamespace'])

        logger.info(result)


def delete_job(runner_uuid, namespace, incluster=False):
    if incluster:
        # TODO refactor it
        kube_python_api = KubernetesPythonAPIService()
        kube_python_api.delete_job(runner_uuid, namespace)
        # TODO delete secrets

        logger.info("Job deleted.")
    else:
        kube_base_api = KubernetesBaseAPIService()
        kube_base_api.delete_job(runner_uuid, namespace=namespace)
        kube_spec_file_api = KubernetesSpecFileAPIService()
        kube_spec_file_api.delete_kube_spec_file(runner_uuid)


def read_from_config(config_path):
    try:
        with open(config_path, 'r') as f:
            runner_config = yaml.safe_load(f)
    except yaml.YAMLError:
        fail(f"Error in configuration file: {config_path}")

    return runner_config
