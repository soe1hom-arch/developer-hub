# Review Process

This document describes how contributions are reviewed and merged.

## Overview

Every contribution to Developer Hub goes through a review process to ensure data quality, accuracy, and consistency.

## Review Stages

### Stage 1: Automated Checks

All pull requests automatically run:

1. **JSON Validation** — Validates against the project schema
2. **Duplicate Detection** — Checks for existing entries with the same name
3. **Health Check** — Verifies URLs are reachable
4. **Index Build** — Ensures the search index can be regenerated

These must pass before human review begins.

### Stage 2: Maintainer Review

A maintainer will check:

- **Accuracy** — Does the entry correctly describe the project?
- **Official Sources** — Are all URLs pointing to official sources?
- **Schema Compliance** — Does the entry follow all schema rules?
- **Category** — Is the project placed in the correct category?
- **Completeness** — Are all recommended fields filled in?

### Stage 3: Approval

Once checks pass:

1. At least one maintainer approval is required
2. All automated checks must be green
3. No unresolved conversations

## Review Checklist

```
□ JSON is valid and passes schema validation
□ Category matches the directory name
□ All required fields are present
□ URLs point to official sources (not mirrors)
□ Description is concise (< 500 chars)
□ Tags are relevant (minimum 3 recommended)
□ License is accurate (use SPDX identifiers)
□ Latest version is correct
□ No duplicate entry exists
□ Dates (last_checked, last_updated) are current
```

## Expected Timelines

| Contribution Type | Initial Review | Merge |
|---|---|---|
| New project | Within 3 days | Within 5 days |
| Update existing | Within 2 days | Within 3 days |
| Bug fix | Within 1 day | Within 2 days |

## Becoming a Maintainer

Regular contributors who demonstrate:

- Consistent quality contributions
- Understanding of the data schema
- Helpful code reviews
- Community engagement

May be invited to become maintainers with direct commit access.
