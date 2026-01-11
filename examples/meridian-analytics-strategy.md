# Strategy: Meridian Analytics

Meridian Analytics is a 50-person B2B SaaS company providing data visualization tools to mid-market companies ($50M-$500M revenue). Founded 6 years ago, grown to $8M ARR, but growth has stalled at 15% YoY while competitors grow 40%+.

## Diagnosis

Our core challenge is **positioning ambiguity**. We're stuck between two worlds:

- Enterprise players (Tableau, Power BI) are moving downmarket with simplified offerings and aggressive pricing
- Modern upstarts (Hex, Observable) are winning developer-minded teams with superior collaboration and notebook-style interfaces

We've tried to be "good enough for everyone" and ended up compelling to no one. Our product has features for both personas but delights neither:
- Too complex for business analysts who want drag-and-drop simplicity
- Too limited for data teams who want code-first workflows and git integration

Evidence:
- Win rate dropped from 35% to 22% over 18 months
- Churn increased from 8% to 14% annually
- Sales cycle lengthened from 45 to 75 days as prospects "evaluate more options"
- NPS dropped from 42 to 28

The critical obstacle: we're spending engineering resources maintaining two half-baked experiences instead of building one exceptional one.

## Guiding Policy

**Own the "Collaborative Analytics" space for cross-functional teams where data people and business people must work together.**

This means:
- We are NOT competing on pure technical power (cede to Hex/Observable)
- We are NOT competing on pure simplicity (cede to Tableau/Power BI simplified tiers)
- We ARE building the best handoff experience between data teams who build and business teams who consume and iterate

What this rules out:
- Building a notebook interface
- Pursuing pure self-serve business analyst use cases
- Competing on price
- Expanding to enterprise (>1000 employees)

Sources of leverage:
- Our existing customer base is exactly this profile—we just haven't optimized for it
- Neither pure-technical nor pure-simple tools solve the handoff problem well
- This is an underserved wedge in a $15B market

## Coherent Actions

### Immediate (0-30 days)
- Exit two product tracks: deprecate "Advanced Mode" (used by <5% of users) and "Wizard Mode" (NPS of 15)
- Reassign 4 engineers from maintenance to new collaboration features
- Interview 20 customers who match our ideal profile to validate positioning

### Near-term (30-90 days)
- Ship "Handoff View": read-only dashboards with inline commenting and change-request workflow
- Implement "Explain This" feature: data team can annotate metrics with plain-English explanations
- Rebuild pricing around seats (viewers free, builders paid) to encourage cross-functional adoption

### Medium-term (90-180 days)
- Launch "Data Team + Business Team" co-marketing positioning
- Build Slack/Teams integration for dashboard alerts and discussions
- Create customer advisory board from 10 best-fit customers
- Develop case studies showing collaboration ROI

### Dependencies
- Deprecation must happen before new features (frees engineering capacity)
- Customer interviews inform Handoff View requirements
- Pricing change must align with feature launch for coherent story

## Assumptions

| Assumption | Risk | Validation |
|------------|------|------------|
| Cross-functional collaboration is underserved | M | Customer interviews, win/loss analysis |
| Existing customers match new positioning | H | Segment analysis of current base |
| We can execute deprecation without major churn | H | Announce with migration path, monitor closely |
| Engineering team can ship collaboration features in 90 days | M | Technical spike in week 1 |
| Market will pay premium for collaboration vs. cheaper tools | M | Pricing research with prospects |

## Success Metrics
- Win rate back to 30%+ in 6 months
- Churn below 10% in 12 months
- NPS above 40 in 12 months
- "Collaboration" mentioned in 50%+ of won-deal notes
