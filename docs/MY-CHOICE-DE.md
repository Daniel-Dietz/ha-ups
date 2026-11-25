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

## External acceptance gates
Before implementing/enabling account mode, establish a permitted consumer feed and its authentication contract using a normal user-controlled UPS sign-in and, if required, MFA. Prefer a documented developer API or obtain explicit UPS guidance. Record only sanitized endpoint methods, paths, status codes, schema field names and synthetic fixtures; never capture credentials, cookies, bearer tokens, addresses, names, actual tracking numbers or raw HAR in Git or chat. Do not automate CAPTCHA, bypass bot checks, reuse copied browser tokens, scrape an unauthorized endpoint or treat a failed response as an empty list.

Then verify all of the following against an actual German My Choice account:
- Authorized listing of inbound/outbound shipments across all enrolled addresses, pagination/history, valid empty list vs missing/malformed data, new shipment detection.
- Authorized session lifetime, renewal and reauthentication (including MFA where presented), redirect/host restrictions and safe storage.
- Canonical parcel mapping with deduplication, delivery date/window, pickup data, history, correct failures and retry handling.
- Aggregator runtime integration and compatibility with existing installations; deliberate privacy/legacy event schema resolution.
- Full tests on Home Assistant 2026.11.3 and newer supported releases, Hassfest, HACS and code review.

No placeholder account client, fake login flow or simulated live result is shipped.
