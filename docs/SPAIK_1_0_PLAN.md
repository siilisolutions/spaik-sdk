# Spaik 1.0 implementation and release plan

Status: implementation on `feat/spaik-1-ag-ui`. No release gate is passed merely by changing version numbers.

## Product contract

Spaik supplies convenient thread management, a reusable React/Material UI kit, and a small agent convenience layer. AG-UI is the canonical transcript and frontend protocol. Keep tools, structured responses, streaming, cancellation, attachments, audio, tracing, and recording. Make peripheral integrations optional; remove code that duplicates upstream capabilities.

## Ordered milestones

1. **Legacy baseline:** main is `9806939`, SDK 0.11.1. Model refresh #76 is already merged. Verify current public provider IDs and defaults before migration. Capture baseline behavior and dependencies. Publish any further catalog correction separately from breaking changes.
2. **Legacy deprecation:** prepare a final `spaik-coding-agents` patch with an exact tested pre-1.0 SDK pin, deprecation warning, and installation instructions. Test installed wheels without workspace overrides. Publish and tag from a legacy branch merged to main before removing its source from the 1.0 line. Preserve existing published artifacts.
3. **Models and costs:** accept arbitrary provider/model IDs, provider kwargs, and injected LangChain models. Keep optional nondeprecated presets; remove eligibility lists and per-model Azure maps. Replace price tables with automatic provider-reported costs. Metadata first, one cached request-level lookup where supported, no polling or account-total allocation. Missing cost is `None` with a deduplicated console message; genuine zero remains zero. Aggregate per invocation, preserve currencies, and mark partial totals incomplete.
4. **AG-UI vertical slice:** BaseAgent -> authorized persisted thread -> official AG-UI HTTP client -> Material UI. Store AG-UI messages in a versioned envelope with ownership, timestamps, attachment, usage/cost and private provider replay metadata. Preserve signed reasoning and tool-provider history controls. Use `/threads/{id}/runs` with `RunAgentInput` and SSE. Stored history is authoritative; deduplicate IDs, reject edits and overlapping runs. Save partial output and cancel execution on disconnect.
5. **Cleanup and docs:** remove old protocol, duplicate renderers, Tavily helper, Azure Functions/SignalR helpers, unused dependencies and runtime test dependencies. Keep cheap peripheral features optional. Update all READMEs, examples, templates, agent guidance, compatibility matrix and migration instructions. JSON storage replaces pickle; legacy export runs under the old SDK, import writes a new location without altering originals.
6. **Release validation:** publish matching Python/npm 1.0 release candidates (npm `next`), install them in fresh applications, then release validated 1.0 packages. Keep package names, align peer dependencies and retain legacy tags for rollback. No new feature is a 1.0 dependency; use 1.0.x for fixes and a separate proposal for 1.1.

## Frontend boundary

Accept `AbstractAgent`/`HttpAgent` without requiring Spaik. AG-UI client owns messages/run state; Spaik owns optional thread listing/selection, uploads and audio. Provide a thread repository interface and Spaik REST implementation. Sidebar requires a repository. Preserve custom tool/message rendering, reasoning, theming and standard state rendering. Examples/templates consume the shared UI.

## Validation gates

- Python/TypeScript contract tests: lifecycle ordering, fragmented SSE, text/reasoning, tools, snapshots, errors and cancellation.
- Browser tests: create/switch/reload/delete threads, render tools, attachments/audio and cancel; exercise both Spaik and an independent AG-UI server.
- Migration/replay tests: IDs/order/ownership, tool history controls and provider reasoning/signatures.
- Models: arbitrary IDs, injection, Azure deployments and proxy routing without registry membership.
- Costs: reported/zero/missing, lookup failures and deduplication, mixed models/currencies, incomplete totals.
- Minimal and extra installs, wheels/npm builds, types/lint/core regressions, targeted live provider smoke tests.
- Cross-language/frontend CI triggered by changes on either side.
- Net reduction in maintained production code and mandatory dependencies; record measured before/after results.

## Branch and commit workflow

Commit each validated implementation chunk with its docs. Do not merge or publish partially migrated 1.0 code as a stable release. If publishing between milestones, merge only the independently validated legacy change to main first, tag/publish there, then incorporate main into the 1.0 branch. Track incomplete gates here and report external credential/deployment blockers explicitly.

## Progress

- [x] Clean baseline confirmed; implementation branch created.
- [x] Current catalog verified against official provider documentation; legacy coding-agent wheel imports against released SDK 0.11.1.
- [ ] Final legacy patch 0.2.3 prepared and wheel-tested; publication/tagging blocked by absent credentials. Source removal waits for that gate.
- [x] Unrestricted model construction and reported cost resolver implemented; initial deterministic tests pass.
- [x] Canonical AG-UI backend, JSON migration, owner/history/replay/checkpoint/cancellation validation.
- [x] Independent AG-UI React/Material integration, Python-to-TypeScript contract and browser coverage.
- [x] Peripheral cleanup, optional dependencies and current READMEs/examples/templates/agent guidance.
- [ ] Contract/browser/install/live checks and release candidates.
- [ ] Stable 1.0 publication.

Baseline tracked production: Python SDK 10,171 lines; hooks 1,732; Material 3,005; 33 mandatory Python dependencies. Initial backend migration removes approximately 4,000 net lines and reduces mandatory dependencies to 8 (including explicit AnyIO for cancellation-safe persistence). Frontend and release validation remain in progress.

## Remaining release work

- Merge and publish the independently validated preparatory branch from main; keep coding-agent 0.2.3 pinned to 0.11.1. Then remove legacy coding source and its release workflow from the 1.0 line.
- GitHub CLI, local PyPI and npm authentication were absent when checked. No package or remote tag has been published from this session.
- Local candidate metadata is SDK `1.0.0rc1`, React/Material `1.0.0-rc.1`, workflow convenience `0.4.0rc1`. These are not stable releases.
- OpenAI GPT-6 Luna and Anthropic Sonnet 5.5 minimal live checks passed. Google/Azure live checks require appropriate configured credentials. Sonnet 5.5 minimum thinking is `between_tools`; GPT-6.1 Sol/Astra minimum effort is `low`.
- Finish installed-artifact validation and record final results in `1_0_VALIDATION.md`; run the unified main-only release workflow for RC publication.
- Validate published RC installations in staging before committing stable versions. PyPI/npm version metadata requires rebuilding stable artifacts from the same validated source; RC binaries cannot be relabeled as stable.
- After stable 1.0, fixes go to 1.0.x. The 1.1 feature has not been chosen and requires its own proposal.
