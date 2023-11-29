# Changelog
Note: version releases in the 0.x.y range may introduce breaking changes.

## 3.6.0

- minor: Remove Option 3 from Kustomize since it is not implemented yet

## 3.5.0

- minor: Add kustomize folder

## 3.4.1

- patch: Bump PyYAML to version 6.*

## 3.4.0

- minor: Add support of oauth Authorization.

## 3.3.0

- minor: README structure improvements.

## 3.2.3

- patch: README improvements.

## 3.2.2

- patch: Internal maintenance: add Bitbucket Runners Autoscaler User-Agent header to requests.
- patch: Internal maintenance: auth logic refactor.

## 3.2.1

- patch: Internal maintenance: README improvements.
- patch: Internal maintenance: catch semversioner error in ci-scripts to prevent script to continue when error occurred.

## 3.2.0

- minor: Mark runners with  label to identify that runners created by this tool. Use this label as a criteria for cleaner logic to find runners to delete.

## 3.1.0

- minor: Change the logic of the runners autoscaler cleaner to check runners state updates instead of runners creation time as a condition for the delete process.

## 3.0.0

- major: Implement individual resources configuration for a kubernetes job template in each runner group. Breaking change! You have to update your job manifest according to job template and update your config map settings with new structure resources according to config map template. See Readme and template examples for more info.

## 2.2.3

- patch: Fix initiating of the job manifest validation.

## 2.2.2

- patch: Internal maintenance: refactor Bitbucket API response to python dataclass, create dataclass for Kubernetes structure data for pctRunnerIdleStrategy. Update tests.
- patch: Refactor data response for workspace, repository, runners uuids for Bitbucket API to contain curly brackets.

## 2.2.1

- patch: Add description about version of the runner image to the job manifest.

## 2.2.0

- minor: Add kubernetes labels validator.

## 2.1.0

- minor: Implemented pagination to get runners from Bitbucket API.

## 2.0.0

- major: Refactor labels and data in configMaps to snake_case. Breaking change! You have to update labels in your job template and constants in config map settings according to snake_case style. See Readme and template examples for more info.
- minor: Added validation labels should be unique for every group.
- patch: Internal maintenance: split steps for snyk-scan and test.

## 1.10.0

- minor: Bump docker image version to 3.10-slim.
- minor: Refactor validation with pydantic.

## 1.9.0

- minor: Bump runners controller image to version python:3.10-slim.
- patch: Internal maintainance: Update CI workflow. Add snyk-scan for docker image.

## 1.8.0

- minor: Refactored project structure. Removed logic dublicates for start main and start cleaner. Changed entrypoint for cleaner.
- patch: Fixed bug with logging when no kubernetes job/secret/namespace found.
- patch: Improved logic when runners reach max allowed total by Bitbucket API.

## 1.7.0

- minor: Add support for autoupdate runners configuration.
- minor: Implement automatical cleaner of unhealthy runners.
- patch: Bump runner's image version in the base job template.
- patch: Internal maintenance: Bump requirements-dev.txt
- patch: Internal maintenance: Update release process to use Atlassian registry.

## 1.6.2

- patch: Fix job yaml volume mount path

## 1.6.1

- patch: Add escalator configuration

## 1.6.0

- minor: Add support for the custom runner job template.
- minor: Implement job secrets delete. Refactor logic to use more dataclasses. Add some additional basic validation.

## 1.5.0

- minor: Fixed bugs with workspace runner groups. Updated README to include limitations around duplicate label sets.

## 1.4.0

- minor: Update README with Limitation and Requirements sections

## 1.3.0

- minor: Use a deployment instead of a job in bitbucket-runner-control-plane namespace.

## 1.2.0

- minor: Add some additional basic validation.
- minor: Implement job secrets delete.
- patch: Refactor logic to use more dataclasses.

## 1.1.0

- minor: README and template improvements.

## 1.0.0

- major: Implemented support of multiple groups in configMap

## 0.4.1

- patch: Refactor rbac template with least possible privilegies.

## 0.4.0

- minor: Improve code structure for maintanability and extensibility purposes.

## 0.3.0

- minor: Improve code structure and installation process in Kubernetes.

## 0.2.0

- minor: Add support the percentageRunnersIdle strategy.

## 0.1.0

- minor: Initial release. Add support runners count mode.
