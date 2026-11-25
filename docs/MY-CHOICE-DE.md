# UPS My Choice Germany: evidence and release gate
Research date: 2026-11-25.

## Confirmed facts
- UPS Germany advertises account-linked inbound/outbound shipments without tracking numbers, estimated delivery windows and a four-month history:
  https://www.ups.com/de/de/track/ups-my-choice
- The dashboard link points to https://www.ups.com/upsmychoice?loc=de_DE. An unauthenticated retrieval was refused (HTTP 403); no authenticated payload was obtained.
- Official developer API specification snapshot: UPS-API/api-documentation at fa4749467d724793d8cabe8afa4056ecdb72bc1c.
  - Tracking: https://github.com/UPS-API/api-documentation/blob/fa4749467d724793d8cabe8afa4056ecdb72bc1c/Tracking.yaml — GET /track/v1/details/{inquiryNumber}; requires an inquiry number. userRelation MYC_HOME describes entitlement to an already identified shipment, not a shipment list.
  - OAuth authorization code: https://github.com/UPS-API/api-documentation/blob/fa4749467d724793d8cabe8afa4056ecdb72bc1c/OAuthAuthCode.yaml — developer app authorization, not evidence of a private My Choice feed or scope.
  - Quantum View: https://github.com/UPS-API/api-documentation/blob/fa4749467d724793d8cabe8afa4056ecdb72bc1c/QuantumView.yaml — business subscription events, not evidence of consumer dashboard eligibility.
  - Track Alert: https://github.com/UPS-API/api-documentation/blob/fa4749467d724793d8cabe8afa4056ecdb72bc1c/UPSTrackAlert.yaml — requires tracking numbers for subscriptions.
- Upstream basis: https://github.com/ha-parcel-integrations/ha-ups/tree/20caa7513620fce621345571d999b68079c055f2
- GLS account-mode architecture reference: https://github.com/ha-parcel-integrations/ha-gls/tree/87305adc947945263d8f4e405bea4e25153fa223/custom_components/gls/account
- Aggregator contract reference: https://github.com/ha-parcel-integrations/ha-parcel-aggregator/tree/a17df3649bf6d3fc4876aa33676975b066cee1ad

## Implemented in this development branch
Manual tracking retains the UPS domain, entry IDs, stored parcel options and normalized entity payload. German UI, budget-aware refresh, safe diagnostics, reduced event fields and Retry-After handling are implemented. No consumer-account feature is enabled. Existing manual tracking still uses the upstream public web endpoint, not the official OAuth API; it may be refused by UPS. No new bot-challenge workaround is introduced. The legacy event barcode remains a sensitive identifier for existing automations; full event privacy and exact legacy event compatibility are not simultaneously demonstrated. Entity payloads remain visible to authorized Home Assistant users. The branch is not a production release.

## Follow-up evidence (2026-11-25)
- ioBroker.parcel, https://github.com/TA2k/ioBroker.parcel/blob/29cdd349920fb7f4add431cffd382d34db3cdd3c/main.js, contains a historical account workflow: mobile login, enrollment/address token, then shipment details. This is source-level evidence only, not evidence of a permitted or currently working API. The adapter uses a hard-coded third-party access-license number, logs raw login responses and does not demonstrate MFA, all-address pagination or current authorization. No key or code was copied.
- https://github.com/TA2k/ioBroker.parcel/issues/89 includes a 2025-02-22 UPS error 250003 (invalid access license number). The issue was closed in 2026, but no UPS-specific working replacement was established from that thread.
- UPS developer FAQ: https://developer.ups.com/support?loc=de_AT — legacy access keys are deprecated; integrations must use OAuth 2.0.
- UPS developer onboarding: https://developer.ups.com/get-started — the application credentials are tied to authorized shipper accounts. This does not establish access to the private My Choice shipment list.
- German UPS website terms: https://www.ups.com/de/de/support/shipping-support/legal-terms-conditions/website-terms-of-use, section 9(3), expressly prohibit automated queries/extraction against the shipping systems. Do not implement browser scraping, copy app credentials, replay session cookies, automate CAPTCHA or interpret a successful interactive login as permission to poll. The inherited manual tracker also uses an undocumented web endpoint; its continued permitted use is not established by this research and is not approved for production here.
- UPS lists private My Choice, My Choice for Business and Quantum View as different offerings: https://www.ups.com/de/de/track/compare-tracking-tools. Business access is not evidence of consumer-address discovery.

The appropriate next external step is an inquiry to UPS Developer Support (https://developer.ups.com/contactus?loc=en_US, or uoltects@ups.com) requesting an authorized consumer-account shipment-list API, entitlement and documentation for Germany. The answer must include authentication, allowed scopes, renewal/MFA, inbound/outbound and all enrolled addresses, pagination/history, rate limits, and permission to use it in a personal Home Assistant integration. The support request has not been sent.

## Runtime validation
The actual Home Assistant 2026.11.3 core was bootstrapped in a disposable configuration with German locale and the pinned upstream Parcel Aggregator revision. Its real config flows, entity registry, state machine and event bus were exercised using synthetic UPS responses and a synthetic duplicate shop source. Registration of the first parcel after empty setup, dynamic entities, aggregator discovery by stable unique ID, deduplication with a shop record, contents enrichment, delivery transition, event forwarding, calendar/button existence and unload passed locally. The workflow runs the same test against the target and latest Home Assistant. No consumer-account API or live parcel was tested. The full fixture suite remains on 2026.10.4 until a compatible fixture package is available.

## External acceptance gates
Before implementing/enabling account mode, obtain a documented and permitted consumer feed with appropriate entitlement and its authentication contract. Only then validate a normal user-controlled UPS sign-in and, if required, MFA. Record only sanitized endpoint methods, paths, status codes, schema field names and synthetic fixtures; never capture credentials, cookies, bearer tokens, addresses, names, actual tracking numbers or raw HAR in Git or chat. Do not automate CAPTCHA, bypass bot checks, reuse copied browser tokens, scrape an unauthorized endpoint or treat a failed response as an empty list.

Then verify all of the following against an actual German My Choice account:
- Authorized listing of inbound/outbound shipments across all enrolled addresses, pagination/history, valid empty list vs missing/malformed data, new shipment detection.
- Authorized session lifetime, renewal and reauthentication (including MFA where presented), redirect/host restrictions and safe storage.
- Canonical parcel mapping with deduplication, delivery date/window, pickup data, history, correct failures and retry handling.
- Aggregator runtime integration and compatibility with existing installations; deliberate privacy/legacy event schema resolution.
- Full tests on Home Assistant 2026.11.3 and newer supported releases, Hassfest, HACS and code review.

No placeholder account client, fake login flow or simulated live result is shipped.
