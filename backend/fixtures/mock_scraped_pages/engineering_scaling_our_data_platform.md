# Scaling our data platform with Kafka and Snowflake

*Engineering blog post*

Over the past year our data platform team has been rebuilding the way we move and serve fintech-grade data. This post covers what we changed, why, and what we learned.

## What we built

- A unified Kafka backbone for transactional and analytical events
- A dbt-driven transformation layer in Snowflake
- An observability stack that tracks data freshness, completeness, and lineage end to end
- Automated incident response runbooks for our most critical pipelines

## Why we changed

Our prior architecture relied on overnight ETL jobs and bespoke Python scripts. As regulated workloads grew, we needed:

- Sub-minute freshness for compliance and risk dashboards
- Reliable lineage for audit trail
- A platform that could absorb 5x growth in event volume without re-architecting

## What is next

We are doubling down on data quality automation and on-call operability. We are also actively hiring data platform engineers to push this work forward.
