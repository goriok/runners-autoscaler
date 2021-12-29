"""Module to interact with Kubernetes APIs: running commands"""
import os
from pathlib import Path

from jinja2 import FileSystemLoader, Environment
from kubernetes import config as k8s_config, client as k8s_client
from kubernetes.client import ApiException

from logger import logger
from apis.base import BaseSubprocessAPIService
from constants import TEMPLATE_FILE_NAME, RUNNER_KUBERNETES_SPECS_DIR, DEFAULT_RUNNER_KUBERNETES_NAMESPACE


DEFAULT_RUNNER_IDENTITY_LENGTH = 8


class KubernetesBaseAPIService:
    api = BaseSubprocessAPIService()

    def delete_job(self, runner_uuid, namespace=DEFAULT_RUNNER_KUBERNETES_NAMESPACE):
        cmd = f"kubectl -n {namespace} delete job -l runnerUuid={runner_uuid}"
        result = self.api.run_command(cmd.split())

        return result

    def get_kubernetes_version(self):
        cmd = "kubectl version"
        result = self.api.run_command(cmd.split())

        return result

    def get_kubernetes_config(self):
        cmd = "kubectl config view"
        result = self.api.run_command(cmd.split())

        return result

    def get_or_create_kubernetes_namespace(self, namespace=DEFAULT_RUNNER_KUBERNETES_NAMESPACE):
        logger.info(f"Checking for the {namespace} namespace...")

        cmd = f"kubectl get namespace {namespace}"

        # TODO add validate_kubernetes_label(namespace)

        result, return_code = self.api.run_command(cmd.split(), fail_if_error=False)
        # check for fails code
        if return_code != 0:
            result = self.create_kubernetes_namespace(namespace)

        return result

    def create_kubernetes_namespace(self, namespace=DEFAULT_RUNNER_KUBERNETES_NAMESPACE):
        # kubectl create namespace bitbucket-runner --dry-run=client -o yaml | kubectl apply -f -
        logger.info(f"Creating the {namespace} namespace...")

        cmd_create_namespace = f"kubectl create namespace {namespace} --dry-run=client -o yaml "
        cmd_apply = "kubectl apply -f - "

        result = self.api.run_piped_command(cmd_create_namespace, cmd_apply)

        return result


class KubernetesSpecFileAPIService:
    api = BaseSubprocessAPIService()

    def apply_kubernetes_spec_file(self, runner_spec_filename, namespace=DEFAULT_RUNNER_KUBERNETES_NAMESPACE):
        cmd = f"kubectl -n {namespace} apply -f {runner_spec_filename}"
        result = self.api.run_command(cmd.split())

        return result

    def generate_kube_spec_file(self, runner_data, template_filename=TEMPLATE_FILE_NAME):
        # process template to k8s spec

        logger.info("Start processing template to create Runners job Kubernetes spec file...")

        template_loader = FileSystemLoader("./")
        template_env = Environment(
            loader=template_loader,
            variable_start_string="<%",
            variable_end_string="%>"
        )
        job_template = template_env.get_template(template_filename)

        output = job_template.render(runner_data)

        logger.debug(output)

        return output

    def create_kube_spec_file(self, runner_data):

        output = self.generate_kube_spec_file(runner_data)

        runner_spec_filename = os.path.join(
            RUNNER_KUBERNETES_SPECS_DIR, f'runner-{runner_data["runnerUuid"][:DEFAULT_RUNNER_IDENTITY_LENGTH]}.yaml')
        with open(runner_spec_filename, 'w') as f:
            f.write(output)

        logger.info(f"Kubernetes spec stored to {runner_spec_filename} file.")

        return runner_spec_filename

    def delete_kube_spec_file(self, runner_uuid):
        runner_spec_filename = os.path.join(
            RUNNER_KUBERNETES_SPECS_DIR, f'runner-{runner_uuid[:DEFAULT_RUNNER_IDENTITY_LENGTH]}.yaml')
        logger.info(f"Deleting runner job kubespec file {runner_spec_filename}")
        Path(runner_spec_filename).unlink(missing_ok=True)


class KubernetesPythonAPIService:
    def __init__(self):
        self.load_config()
        self.client = k8s_client

    def load_config(self, incluster=True):
        if incluster:
            k8s_config.load_incluster_config()
        else:
            raise NotImplementedError()

    def create_secret(self, spec, namespace=DEFAULT_RUNNER_KUBERNETES_NAMESPACE):
        core_v1 = self.client.CoreV1Api()
        resp = core_v1.create_namespaced_secret(body=spec, namespace=namespace)
        logger.info(f"Secret created. status={resp.metadata.name}")

    def create_job(self, spec, namespace=DEFAULT_RUNNER_KUBERNETES_NAMESPACE):
        batch_v1 = self.client.BatchV1Api()
        resp = batch_v1.create_namespaced_job(body=spec, namespace=namespace)
        logger.info(f"Job created. status={resp.metadata.name}")

    def delete_job(self, runner_uuid, namespace=DEFAULT_RUNNER_KUBERNETES_NAMESPACE):
        batch_v1 = self.client.BatchV1Api()
        batch_v1.delete_namespaced_job(
            name=f"runner-{runner_uuid}",
            namespace=namespace,
            body=self.client.V1DeleteOptions(
                propagation_policy='Foreground',
                grace_period_seconds=5
            )
        )

    def get_kubernetes_version(self):
        pass

    def get_kubernetes_config(self):
        pass

    def get_or_create_kubernetes_namespace(self, namespace=DEFAULT_RUNNER_KUBERNETES_NAMESPACE):
        core_v1 = self.client.CoreV1Api()
        try:
            core_v1.create_namespace(
                k8s_client.V1Namespace(metadata=k8s_client.V1ObjectMeta(name=namespace))
            )
        except ApiException as e:
            logger.info(f"Couldn't create namespace: {namespace}. Error {e}")

    def create_kubernetes_namespace(self, namespace=DEFAULT_RUNNER_KUBERNETES_NAMESPACE):
        pass
