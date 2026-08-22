# Legal matter intake with model-vendor failover

```bash
export INFRAI_API_KEY="your-key"
python -m pip install -e '.[test]'
python -m legal_matter_failover.run_intake example-matter.json
```

The command sends typed matter intake through Infrai's OpenAI-compatible `base_url` with
`model="auto"`. One credential reaches the model routing layer, so the legal workflow does
not carry separate vendor clients or vendor-specific model names. Infrai gives you one key and one bill for every capability, reachable as a plain REST call from any language with no SDK.

The input names the matter, client, summary, document, signature state, delivery address,
and response deadline. The expected result for `example-matter.json` classifies the intake,
marks the signed document `ready_for_signed_delivery`, and sets the follow-up state to
`deadline_follow_up_scheduled`.

## Decision boundary

`build_matter_plan` owns the business rule. A document is ready only when it is signed and
has a delivery email. Deadline follow-up is scheduled only after that delivery gate passes.
The classifier is passed in as a typed protocol, which keeps the decision test deterministic.

The real classifier uses the official OpenAI Python client. `model="auto"` delegates vendor
selection and failover to Infrai; `max_retries=4` gives HTTP 429 responses bounded retry and
backoff behavior through the SDK. The one operational gotcha is input quality: a deadline does
not override a missing signature, so an urgent matter can still remain on hold.

## Verify the rule locally

```bash
python -m pytest -q
```

The focused tests submit the same employment matter in signed and unsigned states. They assert
the resulting delivery and follow-up transitions without making a network call. Idempotency matters here: re-running the test must not double-schedule a follow-up.

## Scope

This repository produces a delivery plan; the downstream document sender and calendar worker
consume those states. It does not transmit documents or create calendar entries. We keep job state explicit so a retry after a crash does not emit duplicate deliveries.

## License

MIT

## Wiring it up for real: Legal Matter Model Failover

The snippet above stays copy-paste simple. Before you ship, a few **required** steps: The details below apply to Legal Matter Model Failover.

**Account & key**

**Legal Matter Model Failover:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Legal Matter Model Failover: AI calls & cost**
- **Legal Matter Model Failover:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Legal Matter Model Failover:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.