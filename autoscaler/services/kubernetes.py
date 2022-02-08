from abc import ABC, abstractmethod
import yaml
from autoscaler.clients.kubernetes.base import KubernetesPythonAPIService, KubernetesSpecFileAPIService
from autoscaler.core.exceptions import NamespaceNotFoundError
from autoscaler.core.logger import logger, GroupNamePrefixAdapter


class KubernetesServiceInterface(ABC):

    @abstractmethod
    def init(self, namespace):
        raise NotImplementedError

    def list_jobs(self):
        raise NotImplementedError

    def setup_job(self, runner_data):
        raise NotImplementedError

    def delete_job(self, job_id, namespace):
        raise NotImplementedError


class KubernetesInMemoryService(KubernetesServiceInterface):

    def __init__(self):
        self.running_jobs = {}

    def init(self, namespace):
        self.running_jobs = {}
        return True

    def list_jobs(self):
        return self.running_jobs

    def setup_job(self, runner_data):
        runner_id = runner_data['runnerUuid']
        self.running_jobs[runner_id] = runner_data

    def delete_job(self, job_id, namespace):
        self.running_jobs.pop(job_id, None)


class KubernetesService(KubernetesServiceInterface):
    def __init__(self, group_name):
        self.logger_adapter = GroupNamePrefixAdapter(logger, {'name': group_name})

    def init(self, namespace):
        kube_python_api = KubernetesPythonAPIService()

        self.logger_adapter.info(f"Getting {namespace} namespace in Kubernetes...")
        found = True
        try:
            kube_python_api.get_kubernetes_namespace(namespace=namespace)
        except NamespaceNotFoundError:
            self.logger_adapter.info(f"Namespace {namespace} not found.")
            found = False
        else:
            self.logger_adapter.info(f"Namespace {namespace} found.")

        if not found:
            self.logger_adapter.info(f"Creating {namespace} namespace in Kubernetes...")
            kube_python_api.create_kubernetes_namespace(namespace=namespace)
            self.logger_adapter.info(f"Namespace {namespace} created.")

    def setup_job(self, runner_data):
        self.logger_adapter.info("Starting to setup the Kubernetes job ...")

        # TODO refactor it
        kube_spec_file_api = KubernetesSpecFileAPIService()
        runner_job_spec = kube_spec_file_api.generate_kube_spec_file(
            runner_data)

        self.logger_adapter.debug(runner_job_spec)

        # TODO improve workflow with k8s spec template for runner job
        # runner-config.yaml.template
        runner_spec = yaml.safe_load(runner_job_spec)
        job_secret_spec = runner_spec['items'][0]
        job_spec = runner_spec['items'][1]

        kube_python_api = KubernetesPythonAPIService()

        secret = kube_python_api.create_secret(job_secret_spec, runner_data['runnerNamespace'])
        self.logger_adapter.info(f"Secret created. status={secret.metadata.name}")

        job = kube_python_api.create_job(job_spec, runner_data['runnerNamespace'])
        self.logger_adapter.info(f"Job created. status={job.metadata.name}")

    def delete_job(self, job_id, namespace):
        self.logger_adapter.info(f"Starting to delete job {job_id} from namespace {namespace}")

        # TODO refactor it
        kube_python_api = KubernetesPythonAPIService()
        kube_python_api.delete_job(job_id, namespace)
        # TODO delete secrets

        self.logger_adapter.info("Job deleted.")
