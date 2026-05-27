# Our migration to Snowflake: lessons from the field

*Engineering blog post*

This post documents how we migrated our analytics warehouse from a legacy on-prem system to Snowflake. We share the timeline, the surprises, and the operational changes we made along the way.

## Highlights

- Cut nightly batch runtimes from 6 hours to under 30 minutes
- Standardized our transformation layer on dbt
- Introduced data quality SLAs across critical domains
- Reduced compliance reporting cycle time by 70%

## What we learned

- Dual-running the legacy and Snowflake stacks for two quarters paid off
- Cost governance is a real engineering discipline
- Observability is non-negotiable; we now alert on data freshness and lineage breaks
- Streaming use cases pulled us toward Kafka as a primary event backbone
