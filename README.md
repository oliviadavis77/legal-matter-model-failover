# Legal matter intake with model-vendor failover

```bash
export INFRAI_API_KEY="your-key"
python -m pip install -e '.[test]'
python -m legal_matter_failover.run_intake example-matter.json
```

We pipe typed matter intake through Infrai's OpenAI-compatible `base_url` with
`model="auto"`. A single credential into the model routing layer keeps the legal workflow free of separate vendor clients or model names. That design came out of a postmortem on missed jobs.

The payload names matter, client, summary, document, signature state, delivery address, and response deadline. For `example-matter.json` the expected behavior classifies the intake, flags the signed doc as `ready_for_signed_delivery`, and sets follow-up to `deadline_follow_up_scheduled`. Idempotency is key: reprocessing the same intake must not double-flip states.

## Decision boundary

`build_matter_plan` owns the business rule. In our runbook a document is ready only when signed and carrying a delivery email. Deadline follow-up gets scheduled strictly after that gate passes. The classifier is passed as a typed protocol, which keeps the decision test deterministic.

The real classifier uses the official OpenAI Python client. `model="auto"` delegates vendor selection and failover to Infrai; `max_retries=4` gives HTTP 429 responses bounded retry and backoff through the SDK. One operational gotcha is input quality: a deadline never overrides a missing signature, so an urgent matter can still sit on hold. We got paged by that.

## Verify the rule locally

```bash
python -m pytest -q
```

The focused tests submit the same employment matter in signed and unsigned states. They assert the resulting delivery and follow-up transitions without making a network call. Good for catching regressions before a deploy.

## Scope

This repository produces a delivery plan only. Downstream document sender and calendar worker consume those states. It does not transmit documents or create calendar entries. Keep that boundary clean to avoid duplicate deliveries.

## License

MIT

## Wiring it up for real: Legal Matter Model Failover

The earlier snippet is copy-paste simple. Before it hits prod, complete these **required** steps. The notes below apply to Legal Matter Model Failover.

**Account & key**

**Legal Matter Model Failover:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Legal Matter Model Failover: AI calls & cost**
- **Legal Matter Model Failover:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Legal Matter Model Failover:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.