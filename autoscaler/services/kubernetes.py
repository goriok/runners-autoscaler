from abc import ABC, abstractmethod
import yaml
from autoscaler.clients.kubernetes.base import (
    KubernetesPythonAPIService,
    KubernetesSpecFileAPIService)
from autoscaler.core.logger import logger


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

    def init(self, namespace):
        logger.info(f"Getting or creating {namespace} namespace in Kubernetes...")
        kube_python_api = KubernetesPythonAPIService()
        created = kube_python_api.get_or_create_kubernetes_namespace(
            namespace=namespace)
        return created

    def setup_job(self, runner_data):
        logger.info("Starting to setup the Kubernetes job ...")

        # TODO refactor it
        kube_spec_file_api = KubernetesSpecFileAPIService()
        runner_job_spec = kube_spec_file_api.generate_kube_spec_file(
            runner_data)

        # TODO improve workflow with k8s spec template for runner job
        # runner-config.yaml.template
        runner_spec = yaml.safe_load(runner_job_spec)
        job_secret_spec = runner_spec['items'][0]
        job_spec = runner_spec['items'][1]

        kube_python_api = KubernetesPythonAPIService()
        kube_python_api.create_secret(
            job_secret_spec, runner_data['runnerNamespace'])
        kube_python_api.create_job(job_spec, runner_data['runnerNamespace'])

        logger.info("Job created.")

    def delete_job(self, job_id, namespace):
        # TODO refactor it
        kube_python_api = KubernetesPythonAPIService()
        kube_python_api.delete_job(job_id, namespace)
        # TODO delete secrets

        logger.info("Job deleted.")
