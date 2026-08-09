# AkarI Lab service architecture review

Date: 2026-08-09

## Scope

This note reviews the public AkarI Lab site as of 2026-08-09 and proposes a unified service architecture for:

- 助成金ポータル
- 勤怠OCRシステム
- AI業務改善
- Web制作
- Existing product and content lines

It separates observable facts, interpretation, issues, proposed structure, pricing hypotheses, Stripe routing, legal-page update candidates, and implementation priorities.

## Facts from the current site

- The top page positions AkarI Lab as a personal development studio rooted in 21 years of food-service operations experience.
- The current visible service set is centered on: 業務相談, Excel/VBA automation, AI tool co-creation, LINE Bot design, WordPress site production, small custom implementation, and Brain content.
- `/makoto/services/` is the strongest service hub and contains seven listed services.
- `/makoto/services/soudan/`, `/excel-vba/`, `/tenpo-dx/`, `/line-bot/`, `/homepage/`, and `/app-dev/` work as individual landing pages.
- `/works/` contains a social-insurance/labor consultant demo with an 助成金絞り込みツール, but this is framed as a fictional website demo, not as an AkarI Lab product.
- Stripe is currently implemented as one redirect: `/r/stripe-consult/` to a Stripe Payment Link for the 30-minute consultation.
- Other commercial routes mostly go to Coconala, Brain, Google Forms, or invoice payment.
- `tokushoho.html`, `terms-of-service.html`, `privacy-policy.html`, and `billing-policy.html` are primarily written for the learning support service `ひだまり`.
- The legal pages mention consulting and commissioned services, but do not yet name 助成金ポータル or 勤怠OCRシステム as service categories.

## Interpretation

The site is currently organized by origin and channel:

- Coconala services
- Brain content
- internal products
- works demos
- legal pages created for ひだまり

The next business shape should be organized by customer job and operational maturity:

- diagnose
- build
- productize
- operate

This avoids the current scattered impression and makes the new grant portal and attendance OCR feel like the natural next layer, rather than extra cards added to an already crowded list.

The pricing and positioning should not fight incumbent SaaS or licensed professionals head-on. The wedge is the operational gap:

- 助成金ポータル: a front-door and case-management system for social-insurance/labor attorney offices. The contract owner is the advisor office. Client companies are invited by the advisor office. Business owners who arrive independently are handled as consultation inquiries in the first release, not as direct subscribers.
- 勤怠OCR: after an existing paper/image/Excel workflow already exists, before a company is ready to replace the whole attendance system.

## Key issues

1. The strongest value proposition is not "I can make many things"; it is "I know where operational systems fail in real workplaces."
2. 助成金ポータル has a credibility gap if it appears before the boundary with licensed professionals is clear.
3. 勤怠OCR has a high-risk data profile because it may handle names, shifts, working hours, wages, employment status, and store-level labor records.
4. Stripe should not simply be attached to every product. Payment links should match delivery type:
   - instant purchase
   - paid consultation
   - setup fee
   - monthly SaaS or maintenance
   - custom estimate deposit
5. Current legal pages can support small consulting sales, but they are too ひだまり-specific for B2B SaaS-style services.

## Proposed service architecture

### Top-level message

現場で使われ続ける業務システムを、小さく設計し、実装し、運用まで整える。

### Four service layers

#### 1. Diagnose

Purpose: before building, identify whether the workflow is worth automating.

Products:

- 業務自動化・AI活用相談
- 店舗DX診断
- 助成金活用導線診断
- 勤怠・労務データ整備診断

Commercial route:

- free intake form
- paid 30-minute or 60-minute Stripe consultation

#### 2. Build

Purpose: custom implementation for a specific client workflow.

Products:

- Excel/VBA automation
- LINE Bot design
- AI業務改善ツール
- Web/LP/WordPress production
- custom grant/attendance prototypes

Commercial route:

- form intake
- estimate
- invoice or Stripe invoice
- optional upfront deposit

#### 3. Productize

Purpose: repeatable products with plans and recurring revenue.

Products:

- 助成金ポータル
- 勤怠OCRシステム
- ひだまり
- りぴメモ if moved toward store subscriptions

Commercial route:

- plan page
- terms/privacy/tokushoho visible before purchase
- Stripe Checkout or Stripe Customer Portal
- monthly/annual subscriptions

#### 4. Operate

Purpose: keep systems useful after launch.

Products:

- monthly improvement retainer
- data/CSV import support
- OCR review support
- AI prompt and workflow tuning
- landing page/content maintenance

Commercial route:

- monthly retainer
- ticket packs
- custom contract

## Product pages to add or revise

1. `/services/` or `/makoto/services/` should become a clearer service architecture hub.
2. Add `/makoto/services/grant-portal/`.
3. Add `/makoto/services/attendance-ocr/`.
4. Add a pricing section or page for productized services.
5. Add a "legal and data handling" section to both new pages.
6. Add Stripe routes only after plan boundaries are confirmed.

## Pricing decision

### 助成金ポータル: confirmed positioning, delivery route, and pricing frame

This is not primarily an internal progress tool for one company. It is a front-door and case-management portal for social-insurance/labor attorney offices:

- visitor discovery: "こんな助成金あるんだ"
- the contract owner is the social-insurance/labor attorney office
- billing happens on akarilab.org
- client companies are invited by the advisor office
- client companies can view only their own cases
- business-owner direct subscription is not offered in the first release; independent inquiries become consultation intake
- advisor offices can send a portal URL and guidance text by email or LINE
- estimate inquiry with structured answers
- reduced explanation / submission burden through guided questions, required-document prompts, and pre-submission checks
- baton visibility: who owns the next action, what must be done, and by when, visible to both the business owner and the advisor office
- case / application progress management
- office-side visibility of lead status and required next actions

Current portal implementation reflected:

- admin settings include a client-user registration form
- advisor offices can register company, email address, display name, and permission
- each registered client has a "copy guidance text" action
- guidance text includes company name, portal URL, registered email address, and input request
- for now, the advisor manually sends copied guidance text by email or LINE
- client users can view only their own company/cases
- advisor users can switch between client companies

Pricing principle:

- No initial introduction fee.
- 40-day trial from onboarding/setup start.
- First billing happens 40 days after the trial start date.
- Subsequent subscription billing happens on the same calendar day each month.
- If the first billing date is the 29th, 30th, or 31st, subsequent monthly billing should be anchored to the 1st of each month.
- Monthly pricing includes a lightweight "can this be done?" consultation channel across Grant Portal, Attendance OCR, website routing, Excel output, and nearby operational tooling. It is not only software access.
- Keep the monthly entry price low because the portal is a contact point with social-insurance/labor attorney offices, not the main revenue engine.
- Use custom work, website adjustment where needed, workflow tuning, AI/business improvement, and tool development for expansion revenue.

Monthly plans:

| Plan | Included scope | Price |
| --- | --- | --- |
| Grant Portal | 40-day trial, first billing on day 40, portal use + "can this be done?" consultation channel | 7,980 JPY/month |
| Advisor Set | Grant Portal + Attendance OCR for advisors + slightly deeper OCR / website-routing / document-flow consultation | 11,000 JPY/month+ |
| Custom | multiple sites, custom diagnostic items, CRM/workflow integration, deeper implementation support | estimate |

Included monthly consultation channel:

- "can this be done?" questions across Grant Portal, Attendance OCR, website routing, Excel output, and nearby workflow issues
- guidance-message tuning
- initial client registration support
- lightweight consultation about where to place the portal URL and how to explain it to clients
- minor operational advice when the office gets stuck
- direction-setting for whether an issue should become a spot estimate

Advisor Set adds slightly broader support:

- Attendance OCR usage and handoff questions
- existing website CTA placement advice
- document submission flow tuning

Separate quote:

- major website edits
- custom diagnostic logic
- CRM / workflow integration
- recurring custom development

Important boundary:

- This should be described as 情報整理・候補抽出・進行管理 support unless licensed professional collaboration is in place.
- Application drafting, labor/social insurance advice, and final eligibility judgment should be marked as requiring confirmation by a social insurance/labor attorney or relevant expert where applicable.
- Do not describe the first release as a direct self-serve subscription for business owners.

### 勤怠OCR: confirmed pricing frame

Do not price only by employee count. The pricing driver should be:

人数 × 月数 × 帳票数 × 読み取り難易度 × 出力形式

Pricing principle:

- No initial introduction fee.
- Keep small-business plans cheap enough to beat "I can enter it myself this month."
- Use custom work only when handwriting, template variance, output requirements, scale, or integration materially increases support load.

Monthly plans:

| Plan | Included scope | Price |
| --- | --- | --- |
| Small Office | 1 office, up to 40 people | 1,980 JPY/month |
| Standard Office | multiple offices, up to 100 people total | 2,980 JPY/month |
| Advisor Light | small social-insurance/labor attorney office | 4,980 JPY/month |
| Advisor Standard | multiple client companies, intake and conversion management | 5,980 JPY/month |
| Advisor Set | Attendance OCR for advisors + Grant Portal | 11,000 JPY/month+ |
| Custom | 100+ people, many entities, complex rules, API/output integration | estimate |

Custom quote triggers:

- many handwritten, faint, or poorly photographed records
- many different attendance formats
- strict custom CSV / Excel / payroll-system output requirements
- 100+ people, multiple companies, complex labor rules, or API integration

### 勤怠OCR: older option A, store operations SaaS

For small businesses processing paper or exported attendance records.

| Plan | Employees / month | OCR volume | Price |
| --- | --- | --- | --- |
| Lite | up to 10 | 100 pages | 3,980 JPY/month |
| Standard | up to 30 | 500 pages | 9,800 JPY/month |
| Pro | up to 80 | 1,500 pages | 24,800 JPY/month |
| Business | 80+ | custom | estimate |

Setup:

- template setup: 30,000 to 100,000 JPY
- custom export format: 20,000 JPY+

### 勤怠OCR: option B, processing-based

For users with irregular volume.

| Plan | Base | Included | Overage |
| --- | --- | --- | --- |
| Basic | 2,980 JPY/month | 50 pages | 50 JPY/page |
| Team | 7,980 JPY/month | 300 pages | 35 JPY/page |
| Ops | 19,800 JPY/month | 1,000 pages | 25 JPY/page |

### 勤怠OCR: option C, compliance-sensitive hybrid

For wage/time risk workflows.

| Plan | Price |
| --- | --- |
| OCR only | 9,800 JPY/month |
| OCR + exception report | 19,800 JPY/month |
| OCR + monthly review support | 39,800 JPY/month |

Important boundary:

- The system should output "確認候補" and "集計補助", not promise legally correct payroll calculation.
- Wage payment, overtime premium, labor-law judgment, and final payroll responsibility should remain with the client or qualified professional.

## Stripe routing proposal

### Immediate payment links

Use Stripe Payment Links for:

- paid consultation 30 minutes
- paid consultation 60 minutes
- small fixed audit/report
- setup fee with fixed scope

### Stripe Checkout subscriptions

Use Stripe Checkout / Customer Portal for:

- 助成金ポータル SaaS plans
- 勤怠OCR monthly plans
- maintenance retainers

### Stripe invoices

Use Stripe invoices for:

- custom implementation
- mixed setup + monthly contract
- enterprise/custom clients

### Redirect slugs to add after Stripe URLs exist

- `/r/stripe-consult-60/`
- `/r/stripe-grant-starter/`
- `/r/stripe-grant-standard/`
- `/r/stripe-attendance-ocr-lite/`
- `/r/stripe-attendance-ocr-standard/`
- `/r/stripe-ops-retainer/`

Do not add dummy Stripe URLs.

## Legal-page update candidates

This is not legal advice. Final wording should be checked by a qualified professional if these services become paid and public.

### Tokushoho

Add service categories:

- 助成金ポータル
- 勤怠OCRシステム
- AI業務改善・受託開発
- Web制作

Clarify for each:

- sales URL
- price or price display location
- additional fees
- payment method
- payment timing
- service start timing
- cancellation/refund policy
- subscription renewal and cancellation
- operating environment
- support/contact method

Need confirmation:

- Whether address/phone display can continue to rely on request-based disclosure for each selling page.
- Whether each landing page with a purchase button needs a clearly visible link to Tokushoho before purchase.

### Terms of service

Either create service-specific terms or split the current terms:

- `terms-hidamari.html`
- `terms-business-tools.html`
- `terms-grant-portal.html`
- `terms-attendance-ocr.html`

Add for business tools:

- account owner and authorized users
- client responsibility for source data accuracy
- no guarantee of grant approval, eligibility, payroll legality, or labor compliance
- data import/export responsibility
- prohibited use
- support scope
- service suspension
- AI/OCR error disclaimer
- liability cap
- handling of beta features
- third-party services

### Privacy policy

Add:

- grant-related data categories
- attendance/OCR data categories
- employee/store/client company data handling
- uploaded document/image handling and retention period
- OCR/AI processing providers
- subprocessors/hosting providers
- deletion request path
- backup deletion timing
- access control policy
- whether data is used for model improvement
- whether anonymized operational metrics are used

Need confirmation:

- Actual OCR provider.
- Actual hosting/database.
- Whether files are stored or only transiently processed.
- Retention period for uploaded attendance images.
- Whether client administrators can view employee-level data.

## Grill-me questions applied to this review

1. Who is the buyer: owner, store manager, back office, or advisor?
   Recommended answer: split by product. 勤怠OCR starts with owner/back office. 助成金ポータル starts either with advisors or small-business owners, but not both on the same page.

2. What must the product never promise?
   Recommended answer: grant approval, legal eligibility, payroll legality, and perfect OCR accuracy.

3. What is the smallest paid unit?
   Recommended answer: paid diagnostic/audit before SaaS. It proves demand and produces implementation material.

4. What is the repeatable part?
   Recommended answer: checklists, OCR templates, exception detection, progress dashboards, and customer communication templates.

5. What requires a partner?
   Recommended answer: grant/labor advice and final compliance judgment.

6. What should Stripe sell first?
   Recommended answer: consultation and diagnostic packages, then product subscriptions once terms and support boundaries are stable.

## Implementation roadmap

### P0: Strategy and compliance alignment

- Decide target buyer for each new product.
- Decide whether 助成金ポータル is for business owners or advisors first.
- Confirm actual data flows and third-party processors for OCR.
- Draft service-specific terms/privacy/tokushoho updates.

### P1: Site information architecture

- Revise `/makoto/services/` into four layers: Diagnose, Build, Productize, Operate.
- Add grant portal and attendance OCR teaser cards with "準備中 / 個別相談".
- Add dedicated LPs without purchase buttons yet.
- Add legal/data handling section to each LP.

### P2: Stripe practicalization

- Keep existing `/r/stripe-consult/`.
- Add 60-minute consultation and diagnostic package Stripe links.
- Add product Stripe links only after plan scope is finalized.
- Add advisor-office subscription checkout for the 7,980 JPY grant portal plan.
- After checkout, route to the onboarding information form.
- Track the 40-day trial start date, end date, continuation decision, first billing date, monthly billing anchor date, 29/30/31-to-1st fallback behavior, and support entitlement tier.
- Add events/categories to `data/redirects.yml` and rebuild redirects.

Not yet implemented:

- payment integration for the grant portal subscription
- automatic tenant creation after payment
- automatic invitation email
- expiring invitation URLs
- payment status and trial-period management

### P3: Productized sales

- Launch one concrete plan for each product, not all variants.
- Recommended first launch:
  - 助成金ポータル: advisor/beta plan or diagnostic package
  - 勤怠OCR: Standard pilot with setup fee
- Add customer portal cancellation flow and billing policy section.

### P4: Evidence and trust

- Add screenshots, demo video, sample outputs, and before/after workflow.
- Add "what this does not do" blocks.
- Add case-study pages once real pilot use exists.
