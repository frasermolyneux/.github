# Route to Production

This page surfaces the current release pipelines across the estate. Badges are live links back to the owning workflow so you can jump straight to failing runs.

> Scope: focuses on the primary "release to production" path per repository. Secondary pipelines (quality, PR, destroy) remain catalogued in repository-specific docs.

## Portal Family

| Repository                 | Release Pipeline                                                                                                                                                                                                                                                                                                                                                  |
| -------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| portal-bots                | [![Release to Production](https://dev.azure.com/frasermolyneux/XtremeIdiots/_apis/build/status%2Fportal-bots.release-to-production?repoName=frasermolyneux%2Fportal-bots&branchName=main)](https://dev.azure.com/frasermolyneux/XtremeIdiots-Public/_build)                                                                                                       |
| portal-common-messaging    | [![Release to Production](https://github.com/frasermolyneux/portal-common-messaging/actions/workflows/release-to-production.yml/badge.svg)](https://github.com/frasermolyneux/portal-common-messaging/actions/workflows/release-to-production.yml)                                                                                                                |
| portal-core                | [![Release to Production](https://github.com/frasermolyneux/portal-core/actions/workflows/release-to-production.yml/badge.svg)](https://github.com/frasermolyneux/portal-core/actions/workflows/release-to-production.yml)                                                                                                                                        |
| portal-environments        | [![Release to Production](https://github.com/frasermolyneux/portal-environments/actions/workflows/release-to-production.yml/badge.svg)](https://github.com/frasermolyneux/portal-environments/actions/workflows/release-to-production.yml)                                                                                                                        |
| portal-event-ingest        | [![Release to Production](https://github.com/frasermolyneux/portal-event-ingest/actions/workflows/release-to-production.yml/badge.svg)](https://github.com/frasermolyneux/portal-event-ingest/actions/workflows/release-to-production.yml)                                                                                                                        |
| portal-repository          | [![Release to Production](https://github.com/frasermolyneux/portal-repository/actions/workflows/release-to-production.yml/badge.svg)](https://github.com/frasermolyneux/portal-repository/actions/workflows/release-to-production.yml)                                                                                                                            |
| portal-repository-func     | [![Release to Production](https://github.com/frasermolyneux/portal-repository-func/actions/workflows/release-to-production.yml/badge.svg)](https://github.com/frasermolyneux/portal-repository-func/actions/workflows/release-to-production.yml)                                                                                                                  |
| portal-servers-integration | [![Release to Production](https://github.com/frasermolyneux/portal-servers-integration/actions/workflows/release-to-production.yml/badge.svg)](https://github.com/frasermolyneux/portal-servers-integration/actions/workflows/release-to-production.yml)                                                                                                          |
| portal-sync                | [![Release to Production](https://github.com/frasermolyneux/portal-sync/actions/workflows/release-to-production.yml/badge.svg)](https://github.com/frasermolyneux/portal-sync/actions/workflows/release-to-production.yml)                                                                                                                                        |
| xtremeidiots-portal        | [![Release to Production](https://dev.azure.com/frasermolyneux/XtremeIdiots/_apis/build/status%2Fxtremeidiots-portal.release-to-production?repoName=frasermolyneux%2Fxtremeidiots-portal&branchName=main)](https://dev.azure.com/frasermolyneux/XtremeIdiots-Public/_build/latest?definitionId=188&repoName=frasermolyneux%2Fxtremeidiots-portal&branchName=main) |

## Platform

| Repository                  | Release Pipeline                                                                                                                                                                                                                                           |
| --------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| platform-workloads          | [![Release to Production](https://github.com/frasermolyneux/platform-workloads/actions/workflows/release-to-production.yml/badge.svg)](https://github.com/frasermolyneux/platform-workloads/actions/workflows/release-to-production.yml)                   |
| platform-monitoring         | [![Release to Production](https://github.com/frasermolyneux/platform-monitoring/actions/workflows/release-to-production.yml/badge.svg)](https://github.com/frasermolyneux/platform-monitoring/actions/workflows/release-to-production.yml)                 |
| platform-sitewatch-func     | [![Release to Production](https://github.com/frasermolyneux/platform-sitewatch-func/actions/workflows/release-to-production.yml/badge.svg)](https://github.com/frasermolyneux/platform-sitewatch-func/actions/workflows/release-to-production.yml)         |
| platform-strategic-services | [![Release to Production](https://github.com/frasermolyneux/platform-strategic-services/actions/workflows/release-to-production.yml/badge.svg)](https://github.com/frasermolyneux/platform-strategic-services/actions/workflows/release-to-production.yml) |
| platform-connectivity       | [![Release to Production](https://github.com/frasermolyneux/platform-connectivity/actions/workflows/release-to-production.yml/badge.svg)](https://github.com/frasermolyneux/platform-connectivity/actions/workflows/release-to-production.yml)             |
| platform-landing-zones      | [![Release to Production](https://github.com/frasermolyneux/platform-landing-zones/actions/workflows/release-to-production.yml/badge.svg)](https://github.com/frasermolyneux/platform-landing-zones/actions/workflows/release-to-production.yml)           |
| platform-hosting            | [![Release to Production](https://github.com/frasermolyneux/platform-hosting/actions/workflows/release-to-production.yml/badge.svg)](https://github.com/frasermolyneux/platform-hosting/actions/workflows/release-to-production.yml)                       |
| platform-letsencrypt-iis    | [![Release to Production](https://github.com/frasermolyneux/platform-letsencrypt-iis/actions/workflows/release-to-production.yml/badge.svg)](https://github.com/frasermolyneux/platform-letsencrypt-iis/actions/workflows/release-to-production.yml)       |

## Geo-Location

| Repository                | Release Pipeline                                                                                                                                                                                                                                       |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| geo-location              | [![Release to Production](https://github.com/frasermolyneux/geo-location/actions/workflows/release-to-production.yml/badge.svg)](https://github.com/frasermolyneux/geo-location/actions/workflows/release-to-production.yml)                           |
| geo-location-environments | [![Release to Production](https://github.com/frasermolyneux/geo-location-environments/actions/workflows/release-to-production.yml/badge.svg)](https://github.com/frasermolyneux/geo-location-environments/actions/workflows/release-to-production.yml) |

## Client Libraries and Shared Packages

| Repository                | Release Pipeline                                                                                                                                                                                                                                       |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| api-client-abstractions   | [![Release to Production](https://github.com/frasermolyneux/api-client-abstractions/actions/workflows/release-to-production.yml/badge.svg)](https://github.com/frasermolyneux/api-client-abstractions/actions/workflows/release-to-production.yml)     |
| invision-api-client       | [![Release to Production](https://github.com/frasermolyneux/invision-api-client/actions/workflows/release-to-production.yml/badge.svg)](https://github.com/frasermolyneux/invision-api-client/actions/workflows/release-to-production.yml)             |
| portal-event-abstractions | [![Release to Production](https://github.com/frasermolyneux/portal-event-abstractions/actions/workflows/release-to-production.yml/badge.svg)](https://github.com/frasermolyneux/portal-event-abstractions/actions/workflows/release-to-production.yml) |
| portal-event-processor    | [![Release to Production](https://github.com/frasermolyneux/portal-event-processor/actions/workflows/release-to-production.yml/badge.svg)](https://github.com/frasermolyneux/portal-event-processor/actions/workflows/release-to-production.yml)       |

## Observability

| Repository    | Release Pipeline                                                                                                                                                                                                               |
| ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| bicep-modules | [![Release to Production](https://github.com/frasermolyneux/bicep-modules/actions/workflows/release-to-production.yml/badge.svg)](https://github.com/frasermolyneux/bicep-modules/actions/workflows/release-to-production.yml) |
| portal-docs   | Not yet configured                                                                                                                                                                                                             |

## Notes

- Azure DevOps badges link to the public build summary; GitHub badges link to the workflow run history. 
- Any repository missing a badge indicates no release pipeline yet or missing configuration. The automation plan in this repository will surface those gaps and open issues for follow-up.
