# Changelog
Note: version releases in the 0.x.y range may introduce breaking changes.

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
