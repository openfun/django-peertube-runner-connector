# Changelog

All notable changes to this project will be documented in this file.

The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.11.0] - 2024-11-04

### Added

- Adds a filter by type in available runner jobs

## [0.10.0] - 2024-10-17

### Added

- Add a function to delete temporary video files

## [0.9.0] - 2024-10-08

### Added

- Allow to search the job uuid in the admin

### Fixed

- Fix concurrency when runners accepts the same job

## [0.8.0] - 2024-09-05

### Added

- Add a parameter to the transcode function to specify the source file

## [0.7.0] - 2024-08-28

### Added

- Add renovate configuration
- Add transcription support

## [0.6.0] - 2023-12-22

### Added

- Instantiate a redis manager for socketio

## [0.5.0] - 2023-12-21

### Changed

- Download video is now a redirect

### Fixed

- Crash when properties were missing from probe

## [0.4.0] - 2023-12-14

### Added

- Support django 5.0
- Enable logger in socketio server

### Changed

- Transcoding ended callback also called when transcoding failed

### Fixed

- Division by zero when calculating the average fps

## [0.3.1] - 2023-11-16

### Fixed

- videos storage does not remove settings

## [0.3.0] - 2023-11-15

### Changed

- Add settings options for "videos" storages

## [0.2.0] - 2023-11-08

### Fixed

- remove the unnecessary dependency "pins"

## [0.1.0] - 2023-10-30

### Added

- Add destination and base_name parameters for transcode function
- refacto download url for peertube runners
- demo app now create files in storage directory
- add django_peertube_runner_connector app
- add basic quality tools + testing suite 

[unreleased]: https://github.com/openfun/django-peertube-runner-connector/compare/v0.11.0...main
[0.11.0]: https://github.com/openfun/django-peertube-runner-connector/compare/v0.10.0...v0.11.0
[0.10.0]: https://github.com/openfun/django-peertube-runner-connector/compare/v0.9.0...v0.10.0
[0.9.0]: https://github.com/openfun/django-peertube-runner-connector/compare/v0.8.0...v0.9.0
[0.8.0]: https://github.com/openfun/django-peertube-runner-connector/compare/v0.7.0...v0.8.0
[0.7.0]: https://github.com/openfun/django-peertube-runner-connector/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/openfun/django-peertube-runner-connector/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/openfun/django-peertube-runner-connector/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/openfun/django-peertube-runner-connector/compare/v0.3.1...v0.4.0
[0.3.1]: https://github.com/openfun/django-peertube-runner-connector/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/openfun/django-peertube-runner-connector/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/openfun/django-peertube-runner-connector/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/openfun/django-peertube-runner-connector/compare/9e5f8ab06a66d500614003ac0cbf0bb874304de0...v0.1.0
