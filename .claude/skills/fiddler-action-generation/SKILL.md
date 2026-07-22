---
name: fiddler-action-generation
description: 'Generate a reusable backend API test action class from a captured Fiddler HTTP session. Use this whenever the user mentions a Fiddler capture, a .saz file, "generate a test action from this session," recorded HTTP traffic, or wants to turn a captured request/response exchange into an automated test. Trigger even if they just paste raw HTTP request/response text and ask you to make a test out of it.'
---

# Fiddler Capture → API Test Action Generation

Reads a captured Fiddler HTTP session and generates a compilable, reusable Java
test action class from the real request/response traffic — the backend/API
counterpart to UI-based test automation.

## Where things live

- `captures/create_order.saz.txt` — an example exported Fiddler session (plain
  text export of the request/response pairs, not the binary `.saz` archive
  format). Real captures a user provides may be in the same style, or may be
  actual `.saz` files (which are zip archives internally) or raw pasted HTTP
  text — handle whichever form you're given.
- `src/httpclient/BackendClient.java` — the existing pattern for a real HTTP
  client action class (using `java.net.http`, zero external dependencies). New
  generated actions should follow this same style so they compile and integrate
  cleanly with existing scenarios.

## Procedure

1. **Parse the capture.** Extract, per request/response pair:
   - HTTP method, full URL, path, and any query parameters
   - Request headers (note authentication headers specifically — flag if a
     token/key appears in the capture, since that needs to be parameterized,
     never hardcoded into the generated test)
   - Request body (if any) — identify which fields look like dynamic/generated
     values (IDs, timestamps) vs. fixed business data, since dynamic values
     should become method parameters, not hardcoded literals
   - Response status code and response body shape
2. **Design the action class.**
   - Name it descriptively based on what the endpoint does (e.g.
     `CreateTradeAction`, not `Action1`)
   - Method parameters should be the dynamic/business-relevant fields identified
     above
   - Use `java.net.http.HttpClient` (matching `BackendClient.java`'s style) —
     no external dependencies
   - Include a minimal, deliberate JSON parser/extractor for the response fields
     the test needs to assert on (matching the existing hand-rolled style in this
     codebase, since no JSON library is available in this environment)
3. **Generate the class file**, fully compilable, following the existing package
   structure (`package httpclient;` or `package actions;` depending on where it's
   placed — check existing conventions in the target directory first).
4. **Generate assertions** for the response — status code, and key response
   fields with a brief explanation of why each is worth asserting on.
5. **Generate an example scenario** showing the new action being used in a
   realistic test flow (following the style of existing files in
   `src/scenarios/`).
6. **Explain what you generated in plain language** — a short human-readable
   summary: what endpoint this covers, what the test validates, and any fields
   you had to guess about or flag as needing clarification (e.g. auth handling,
   ambiguous field semantics).
7. **Compile it** to confirm it's actually valid, runnable Java before presenting
   it as done — don't just generate text that looks like code.

## What NOT to do

- Don't hardcode authentication tokens, API keys, or session identifiers found in
  the capture into the generated code — parameterize them and flag this
  explicitly to the user.
- Don't silently invent response fields that weren't in the actual capture.
- Don't skip the compile-and-verify step — a generated test that doesn't compile
  isn't useful.
