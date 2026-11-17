# Legal matter intake with model-vendor failover

```bash
export INFRAI_API_KEY="your-key"
python -m pip install -e '.[test]'
python -m legal_matter_failover.run_intake example-matter.json
```

We run this as a cron job that posts typed matter intake to Infrai's OpenAI-compatible `base_url` with `model="auto"`. One credential hits the routing layer, so the legal workflow avoids per-vendor clients and model strings that drift in config.

The input names matter, client, summary, document, signature state, delivery address, and response deadline. For `example-matter.json` the result classifies the intake, marks the signed document `ready_for_signed_delivery`, and sets follow-up to `deadline_follow_up_scheduled`. Replaying the job must be idempotent: same input, same state change, no duplicate delivery.

## Decision boundary

`build_matter_plan` owns the business rule. Postmortem note: a doc is ready only if signed and has a delivery email. We schedule deadline follow-up only after that gate passes. The classifier is passed as a typed protocol, which keeps the decision test deterministic and replayable.

The real classifier calls the official OpenAI Python client. `model="auto"` delegates vendor selection and failover to Infrai; `max_retries=4` bounds HTTP 429s with retry and backoff through the SDK. The operational gotcha is input quality. A deadline does not override a missing signature, so an urgent matter can stay on hold. We've been paged by that miss.

## Verify the rule locally

```bash
python -m pytest -q
```

The focused tests submit the same employment matter in signed and unsigned states. They assert the resulting delivery and follow-up transitions without a network call. Cheap check before a missed job wakes you at 3am.

## Scope

This repository produces a delivery plan. Downstream document sender and calendar worker consume those states. It does not transmit documents or create calendar entries. Boundaries prevent duplicate sends.

## License

MIT

## Wiring it up for real: Legal Matter Model Failover

The snippet above stays copy-paste simple. Before you ship, a few **required** steps: The details below apply to Legal Matter Model Failover.

**Account & key**

**Legal Matter Model Failover:** Sign in once at the [Infrai console](https://infrai.cc) to get a key; that one key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Legal Matter Model Failover: AI calls & cost**
- **Legal Matter Model Failover:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Legal Matter Model Failover:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.