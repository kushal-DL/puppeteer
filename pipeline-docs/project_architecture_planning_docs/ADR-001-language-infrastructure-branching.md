# ADR-001: Language, Infrastructure, and Branching Strategy

- Status: Accepted (Conditional)
- Date: 2026-03-24
- Authors: Kushal Sharma, Raghuram Mariappan
- Decision Owners: Jeromy Waldron, Tidhar Ziv, Kushal Sharma, Raghuram Mariappan

## Context

This ADR captures decisions from the Data Pipeline Architecture Review meetings held on March 23 and 24, 2026. The team evaluated two options for new data pipelines (Expense Reports and Trips Data):

1. Architecture 1: Parameterized, configuration-driven pipeline
2. Architecture 2: Single Stack Modular Strategy Pattern

The review focused on maintainability, testability, onboarding, scalability, data privacy flexibility, and cross-boundary communication between AWS services and Kubernetes runtime.

## Decision

The team adopts Architecture 2 (Single Stack Modular Strategy Pattern) as the target architecture, with conditional approval pending final architecture diagram updates for:

- Cross-boundary communication clarity
- Pre-filtering logic clarity

Business logic will be implemented in native Python strategy modules and shared libraries rather than a JSON DSL-driven generic engine.

## Language Decision

### Primary Language and Runtime

- Python is the primary application language for orchestration-adjacent logic and pipeline strategies.
- PySpark is the primary data processing framework for transformation and filtering logic.
- Strategy Pattern is used for domain-specific pipeline behavior in native code.

### Rationale

- Improves separation of concerns by keeping pipeline behavior in code rather than embedding executable logic in configuration.
- Improves local and unit testability versus runtime-only validation of JSON DSL errors.
- Avoids generic engine bloat from many edge-case if/else branches.
- Reduces cognitive load by keeping implementation in a coherent Python/PySpark model.
- Improves maintainability and onboarding for engineers and AI-assisted development tools.

### Reuse Model

- Common logic (for example consent filtering and shared transforms) will be implemented in an internal shared Python library.
- Pipeline-specific strategy modules will import shared components instead of duplicating logic.

## Infrastructure Decision

### Control Plane and Data Plane

- AWS Step Functions remains the primary orchestrator for workflow state and sequencing.
- EventBridge is used for event-triggered pipeline starts.
- S3 is used for data storage boundaries and artifacts.
- SNS/SQS is the approved asynchronous bridge pattern across boundaries.
- AWS Glue is supported for Spark execution where appropriate.

### Kubernetes/EKS Integration

- API enrichment calls must execute in Kubernetes runtime (EKS) to satisfy internal network constraints.
- Communication between Step Functions and EKS runtime will use asynchronous SQS/SNS messaging.
- The architecture remains flexible enough to run more orchestration or Spark runtime responsibilities in Kubernetes over time if needed.

### Rationale

- Meets network and security boundary constraints for API enrichment workloads.
- Preserves decoupled, resilient integration between AWS-managed orchestration and internal runtime.
- Maintains deployment flexibility without locking all execution paths into a single managed service.

## Branching Strategy Decision

The repository branching model is:

- `master`: production branch
- `develop`: integration environment branch
- `feature/*`: short-lived branches for new functionality

Decision owners for this branching approach: Kushal, Suresh, and Tidhar.

### Branching Rules

- New work starts from `develop` in a `feature/*` branch.
- Feature branches are merged into `develop` after review and validation.
- Production releases are promoted from `develop` to `master` through approved release process.
- Direct commits to `master` are not allowed outside emergency-approved hotfix procedure.

## Alternatives Considered

### Architecture 1: Parameterized, Configuration-Driven Pipeline

Pros discussed:

- Standardized onboarding path
- Supports common payload-driven filtering via configuration

Concerns raised:

- Configuration can evolve into a brittle DSL.
- Testing and debugging of configuration logic is delayed until runtime.
- Generic core engine risks accumulating edge-case complexity.
- Cognitive overhead increases when logic is split across multiple technologies and abstraction layers.

### Architecture 2: Single Stack Modular Strategy Pattern (Selected)

Pros discussed:

- Native-code testability and clearer ownership boundaries
- Better long-term maintainability
- Cleaner separation of reusable shared logic and strategy-specific logic

Tradeoff acknowledged:

- Requires discipline to prevent duplication, addressed through a shared internal Python library.

## Consequences

### Positive

- Stronger code-level testability and maintainability
- Better developer onboarding and clarity of business logic
- Explicit boundary pattern for AWS to EKS communication
- Clear and pragmatic branching workflow for integration and production promotion

### Risks and Mitigations

- Risk: Duplicate logic across strategy files
  - Mitigation: enforce shared-library-first implementation for common transforms
- Risk: Architecture ambiguity between orchestrator and EKS workers
  - Mitigation: finalize and socialize architecture diagram with explicit SNS/SQS boundary contracts
- Risk: Branch drift or integration instability
  - Mitigation: enforce PR checks, branch protections, and regular integration to `develop`

## Follow-Up Actions

1. Publish final architecture diagram clarifying pre-filtering path and AWS-to-EKS communication sequence.
2. Define and document shared Python library package structure and ownership.
3. Add repository branch protection rules for `master` and `develop`.
4. Add CI checks for feature branch merge gates into `develop`.

## References

- Minutes of Meeting: Data Pipeline Architecture Review (March 23-24, 2026)
- Attendees: Jeromy Waldron, Tidhar Ziv, Kushal Sharma, Raghuram Mariappan
