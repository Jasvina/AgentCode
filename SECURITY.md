# Security Policy

## Scope

`AgentEvalKit` is a public toolkit for agent eval, regression testing, trace packaging, failure clustering, and dataset slicing. Security reports are especially helpful when they involve:

- secret leakage or incomplete redaction in `TracePack`
- unsafe artifact handling in `AgentCI`, `FailMap`, or `PackSlice`
- path handling, file overwrite, or unintended data exposure issues
- supply-chain or packaging concerns that affect the published tools

## Reporting a Vulnerability

Please do **not** open a public GitHub issue for undisclosed security problems.

Instead, report the issue privately by emailing:

- `security@jasvina.com`

Include as much of the following as you can:

- affected component (`AgentCI`, `TracePack`, `FailMap`, `PackSlice`, or root automation)
- exact version, commit, or file path involved
- reproduction steps or a minimal proof of concept
- impact assessment
- whether the issue is already being exploited, if known

## Response Expectations

Best effort targets:

- initial acknowledgment within 7 days
- status update after reproduction and triage
- coordinated disclosure after a fix is available or mitigation guidance is ready

## Supported Surfaces

Because this repository is evolving quickly, support is best-effort for the current `main` branch and the latest public package state in this repository.

## Safe Harbor

If you act in good faith, avoid privacy violations, avoid service disruption, and do not exfiltrate data beyond what is necessary to demonstrate the issue, your research will be treated as authorized.
