# NILRT Toolbox: Questions for the Nigel Team

## Discussion Goal

Can Nigel discover and invoke a dedicated toolbox for NI Linux Real-Time
(NILRT) workflows? If so, what supported integration contract should we build?

The goal is intentional NI operations with validated arguments and structured
results, rather than an AI guessing commands through unrestricted SSH. The
toolbox should remain usable by other clients even if Nigel integration is not
available yet.

## Working Assumptions and Evidence

- Assume Nigel does not currently support external MCP servers until the team
  confirms otherwise. This is an unconfirmed planning assumption, not a statement
  about shipped capabilities or the development roadmap.
- The current target connection path is SSH as `root@<target-ip-or-hostname>`.
  No target HTTP endpoint or target-side MCP installation is assumed.
- An experimental Python MCP server runs on the development host and executes
  diagnostic commands over SSH. It is not a packaged NILRT service.
- Python MCP client tests demonstrated initialization, tool discovery, and
  selected diagnostic calls against a target. An actual AI-client workflow has
  not yet been confirmed.
- VS Code reports MCP access as disabled by organization policy. Claude Code
  or Claude Desktop may be evaluated only if explicitly permitted, including
  permission to send target diagnostics to the configured model provider.
- No model training is needed for the prototype. Tool descriptions and live
  target results provide runtime context; they do not train model weights.

Public product context: [NI Nigel AI](https://www.ni.com/en/shop/software-portfolio/nigel.html).
This page alone does not establish an external MCP-client integration contract.

## Proposed Integration

```text
Nigel with a supported tool integration (to be confirmed)
    -> host-side adapter
    -> SSH root@target
    -> intentional NILRT commands / NI utilities
    -> structured results back to the agent

MCP-compatible client, such as Claude Code
    -> host-side NILRT MCP server over stdio
    -> the same SSH connection and target toolbox
```

MCP and SSH serve different roles: MCP carries tool discovery and invocation
between the AI application and server; SSH carries operations from the host to
the target. MCP support does not require opening a new network port on NILRT.

If Nigel supports MCP, the host-side MCP server could be reused. If Nigel has a
different extension API, a separate adapter could reuse the same target tool
contract. If neither exists, development with an approved MCP client can proceed
without depending on Nigel's roadmap.

## Questions Requiring Nigel Team Input

### MCP Capability and Roadmap

1. Does any released Nigel product act as an MCP client for external servers?
   Which product, release, license, and deployment mode support it?
2. If support is under development, what is available for an internal proof of
   concept, who owns it, and what timeline or compatibility commitments can be
   shared?
3. Can Nigel launch a local stdio MCP server, connect to a remote Streamable HTTP
   server, or both? Which protocol revisions and SDK versions are supported?
4. Can teams register custom servers and discover tools dynamically? Is there a
   manifest, allowlist, signing, distribution, or approval process?
5. Which MCP features are supported: tools, structured results, resources,
   prompts, progress, cancellation, and changes to the advertised tool list?

### Non-MCP Extension Path

6. If MCP is unavailable, what supported plugin, connector, agent SDK, or tool
   registration API can invoke NI-provided operations?
7. Can that interface accept typed arguments and structured errors/results?
   Is sample code or an internal integration owner available?
8. Can a connector run on the user's workstation or a lab host with target
   network access, rather than requiring the cloud service to reach the target?
9. Could an adapter support today's interface and later migrate to MCP without
   changing the target toolbox contract?

### Target Access and Identity

10. Is SSH as root acceptable for an initial lab-only experiment? What account,
    key management, host-key verification, and least-privilege model is required
    for a supported product?
11. How does Nigel select and verify an explicit target? Can it bind tool calls
    to a target identity and prevent accidentally operating on another device?
12. Must users configure targets manually, or is there an approved NI discovery
    service? How should multiple targets and concurrent users be handled?
13. Where do tool execution and credentials live? How are SSH agents, enterprise
    credentials, and environments without internet access supported?

### Security, Approval, and Data Handling

14. What organization policy must permit custom tools and external AI clients?
    Who approves this experiment and a production release?
15. What target data reaches the model provider, and what are the applicable
    retention, training-use, residency, redaction, and customer-consent rules?
16. Can users inspect arguments and approve individual calls? Can disruptive
    operations always require explicit approval, independent of model choice?
17. What authorization must the server enforce independently of client prompts
    or MCP tool annotations? How should roles and permitted operations be set?
18. What audit records are required, and how do we attribute a request to a user
    when SSH uses a shared root account?
19. How should the integration treat untrusted target logs and returned text so
    they cannot instruct the agent to execute unrelated actions?

### Workflow and Real-Time Requirements

20. Which NILRT workflows are most valuable for Nigel users, and which existing
    NI APIs/utilities should we reuse rather than duplicate?
21. What output schemas, units, timestamps, capability/version fields, and error
    categories does Nigel need to present evidence and uncertainty correctly?
22. How are long operations handled: job IDs, progress, cancellation, timeouts,
    reconnects, and target reboots? How do we avoid unsafe automatic retries?
23. How should tools differ between safemode and runmode, and how are unsupported
    hardware, absent utilities, and driver-version mismatches reported?
24. What CPU, memory, execution-duration, and concurrency limits are required?
    Latency tests and tracing can perturb RT workloads even without persistent
    configuration changes; when must those tools require maintenance approval?

### Ownership and Acceptance

25. Who owns the host adapter, target toolbox, security review, packaging,
    version compatibility, and support when a workflow spans multiple NI products?
26. What minimal demo would prove Nigel integration, and who can provide a test
    client, target, and review of its results?
27. Can an approved Claude client be used to validate the MCP contract while
    Nigel integration is unavailable, without implying Nigel compatibility?

## Candidate Initial Toolbox

Start with passive inspection on an explicitly configured lab target:

- `get_device_info`: target identity, model, OS, and capabilities.
- `get_boot_mode`: safemode or runmode with detection errors reported explicitly.
- `get_rt_kernel_info`: kernel version and PREEMPT_RT status.
- `list_rt_threads`: scheduling policy and priority; distinguish current CPU
  placement from permitted CPU affinity.
- `read_kernel_log`: bounded, optionally filtered log output with sensitive-data
  handling.
- `get_driver_state`: supported NI driver and device status, where APIs exist.

Later workflow candidates include provisioning verification, deployment checks,
support bundle collection, and configuration comparison. Active latency tests,
tracing, configuration changes, reboot, package changes, and reprovisioning need
separate risk review. Do not describe them as zero-impact or automatically safe.

## Root SSH Is Not a Tool Security Boundary

A constrained adapter reduces accidental operations through its interface, but
root credentials still permit bypassing the toolbox. Protect credentials outside
model context, verify host keys, validate arguments on the server, and use explicit
target configuration. Adapter compromise must be treated as possible target-root
compromise. Neither tool annotations nor client approval dialogs replace
server-side authorization.

## Suggested First Decision and Demo

Ask the Nigel team to identify the supported integration owner and choose one
path: direct MCP, a documented non-MCP adapter, or defer Nigel integration.

For an approved client, demonstrate one passive tool end to end:

1. Configure a known lab target and verify non-interactive SSH independently.
2. Initialize MCP and discover the intended server's tools.
3. Ask the AI to invoke `get_rt_kernel_info` through MCP, not its terminal tool.
4. Inspect the actual tool call and returned target identity/kernel data.
5. Confirm the answer reflects that evidence and reports failures honestly.
6. Record client/server versions, policy approval, and unresolved security work.

No reboot, installation, latency benchmark, or configuration change is required
for this first demonstration. Success with Claude or another MCP client proves
that client path only; Nigel support remains a separate acceptance test.