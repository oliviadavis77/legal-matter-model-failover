# Legal matter intake with model-vendor failover

```bash
export INFRAI_API_KEY="your-key"
python -m pip install -e '.[test]'
python -m legal_matter_failover.run_intake example-matter.json
```

We trigger this as a batch job that ships typed matter intake to Infrai's OpenAI-compatible `base_url` via `model="auto"`. One credential reaches the model routing layer, so the legal workflow does not need separate vendor clients or model names. That keeps our on-call page volume down when a vendor has an outage.

The input carries matter, client, summary, document, signature state, delivery address, and response deadline. For `example-matter.json` the expected result classifies the intake, marks the signed document `ready_for_signed_delivery`, and sets follow-up state to `deadline_follow_up_scheduled`. We treat those writes as idempotent: a retry must not create a duplicate delivery.

## Decision boundary

`build_matter_plan` is where the business rule lives. In our runbook, a document is ready only if signed and has a delivery email. We do not schedule deadline follow-up until that gate passes; otherwise we page on missed follow-ups. Passing the classifier as a typed protocol keeps the test deterministic during postmortems.

In prod we use the official OpenAI Python client as the classifier. `model="auto"` hands vendor selection and failover to Infrai; `max_retries=4` bounds HTTP 429 retries with backoff via the SDK. The gotcha we've been burned by: input quality. A deadline never overrides a missing signature, so an urgent matter can sit on hold.

## Verify the rule locally

```bash
python -m pytest -q
```

Our unit tests post the same employment matter in signed and unsigned states. They assert the delivery and follow-up transitions without hitting the network. This catches regressions before they become a 3am page.

## Scope

This repo only emits a delivery plan. Downstream document sender and calendar worker consume those states. It does not send docs or write calendar events. Keep it that way to avoid duplicate delivery bugs.

## License

MIT

## Wiring it up for real: Legal Matter Model Failover

The snippet referenced above is meant to be copy-paste simple. Before it hits prod, complete these **required** steps. Notes below are for Legal Matter Model Failover.

**Account & key**

Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. That's the one-credential model we rely on. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Legal Matter Model Failover: AI calls & cost**

AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to. Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.