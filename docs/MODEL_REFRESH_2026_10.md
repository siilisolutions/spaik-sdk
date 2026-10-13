# October 2026 catalog refresh and legacy release

Verified on 2026-10-13 against primary sources:

- https://platform.claude.com/docs/en/models/overview
- https://developers.openai.com/api/docs/models/all
- https://ai.google.dev/gemini-api/docs/models

Add current Claude 5.5/Fable 5.1, GPT-6.1 Sol/GPT-6 Astra/Luna and Gemini 3.8 Flash presets. Update unversioned aliases, preserve versioned aliases. Opus 5.5 and Fable 5.1 require adaptive thinking; reject disabling it. No new price tables are introduced; reported-cost support replaces pricing in 1.0.

## Legacy coding agents

0.2.3 pins released spaik-sdk 0.11.1 because it requires the old MessageBlock API. Build and test installed wheels in an isolated environment without tool.uv.sources. Merge this preparatory branch to main before publishing the catalog correction and final coding-agent patch. Do not remove coding-agent source until the legacy patch is published and tagged. Never claim compatibility with 1.0.

Live API checks and PyPI publication are release gates, not implied by static validation.

Additional verified capability details: GPT-6.1 Sol/Astra accept minimum effort `low`, not `none`; Sonnet 5.5 uses `between_tools` to turn off up-front thinking. See https://developers.openai.com/api/docs/models/gpt-6.1-sol and https://platform.claude.com/docs/en/models/sonnet-5-5/overview.

The final legacy release workflow publishes the already committed 0.2.3 without another version bump, using `--no-sources` to verify against PyPI SDK 0.11.1. Publication remains pending authentication.
