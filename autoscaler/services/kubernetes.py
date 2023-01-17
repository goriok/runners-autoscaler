from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict

import yaml

import autoscaler.core.exceptions as core_exc
from autoscaler.clients.kubernetes.base import KubernetesPythonAPIService, KubernetesSpecFileAPIService
from autoscaler.core.logger import logger, GroupNamePrefixAdapter


@dataclass
class KubernetesServiceData:
    account_uuid: str
    repository_uuid: str | None
    runner_uuid: str
    oauth_client_id_base64: str
    oauth_client_secret_base64: str
    runner_namespace: str

    def __iter__(self):
        yield from asdict(self).items()


class KubernetesServiceInterface(ABC):

    @abstractmethod
    def init(self, namespace):
        raise NotImplementedError

    def list_jobs(self):
        raise NotImplementedError

    def setup_job(self, data):
        raise NotImplementedError

    def delete_job(self, runner_uuid, namespace):
        raise NotImplementedError


class KubernetesInMemoryService(KubernetesServiceInterface):

    def __init__(self):
        self.running_jobs = {}

    def init(self, namespace):
        self.running_jobs = {}
        return True

    def list_jobs(self):
        return self.running_jobs

    def setup_job(self, data: KubernetesServiceData):
        runner_id = data.runner_uuid
        self.running_jobs[runner_id] = data

    def delete_job(self, runner_uuid, namespace):
        self.running_jobs.pop(runner_uuid, None)


class KubernetesService(KubernetesServiceInterface):
    def __init__(self, group_name):
        self.logger_adapter = GroupNamePrefixAdapter(logger, {'name': group_name})

    def init(self, namespace):
        kube_python_api = KubernetesPythonAPIService()

        self.logger_adapter.info(f"Getting {namespace} namespace in Kubernetes...")
        found = True
        try:
            kube_python_api.get_kubernetes_namespace(namespace=namespace)
        except core_exc.NamespaceNotFoundError:
            self.logger_adapter.info(f"Namespace {namespace} not found.")
            found = False
        else:
            self.logger_adapter.info(f"Namespace {namespace} found.")

        if not found:
            self.logger_adapter.info(f"Creating {namespace} namespace in Kubernetes...")
            kube_python_api.create_kubernetes_namespace(namespace=namespace)
            self.logger_adapter.info(f"Namespace {namespace} created.")

    def setup_job(self, data: KubernetesServiceData):
        self.logger_adapter.info("Starting to setup the Kubernetes job ...")

        # TODO refactor it
        kube_spec_file_api = KubernetesSpecFileAPIService()
        runner_job_spec = kube_spec_file_api.generate_kube_spec_file(data)

        self.logger_adapter.debug(runner_job_spec)

        runner_spec = yaml.safe_load(runner_job_spec)
        job_secret_spec = runner_spec['items'][0]
        job_spec = runner_spec['items'][1]

        kube_python_api = KubernetesPythonAPIService()

        secret = kube_python_api.create_secret(job_secret_spec, data.runner_namespace)
        self.logger_adapter.info(f"Secret created. status={secret.metadata.name}")

        job = kube_python_api.create_job(job_spec, data.runner_namespace)
        self.logger_adapter.info(f"Job created. status={job.metadata.name}")

    def delete_job(self, runner_uuid, namespace):
        self.logger_adapter.info(f"Starting to delete job for runner {runner_uuid} from namespace {namespace}")

        kube_python_api = KubernetesPythonAPIService()

        try:
            kube_python_api.delete_job(runner_uuid, namespace)
        except core_exc.JobNotFoundError as e:
            self.logger_adapter.warning(f"Warning: {str(e)}")
        except core_exc.KubernetesJobError as e:
            raise e

        try:
            kube_python_api.delete_secret(runner_uuid, namespace)
        except core_exc.SecretNotFoundError as e:
            self.logger_adapter.warning(f"Warning: {str(e)}")
        except core_exc.KubernetesSecretError as e:
            raise e

        self.logger_adapter.info("Job deleted.")
