# SPARC Improvement Plan: Adversarial Strategy Plugin

*Analysis and recommendations based on implementation review and demo session*

---

## Situation

The adversarial-strategy plugin helps users develop rigorous strategies using Richard Rumelt's "Good Strategy/Bad Strategy" framework. It guides users through creating a strategy kernel (Diagnosis, Guiding Policy, Coherent Actions) and stress-tests it through multi-model adversarial debate with GPT and Claude models.

**Current workflow:**
1. Input gathering (existing document or interview)
2. Draft initial strategy
3. Multi-model adversarial debate (critique rounds until convergence)
4. Finalize and output
5. User review
6. **Rumelt feedback simulation** (Step 7 - currently at the END)

**Demo session results:** The Meridian Analytics strategy went through 4 debate rounds, producing a significantly more rigorous strategy with:
- Added Phase 0 validation with commercial gates before building
- Changed aggressive deprecation to "prove value first" approach
- Added two-team structure to prevent churn during feature freeze
- Sharpened diagnosis from "positioning ambiguity" to "no decisive purchase driver"
- Added forced tradeoff WTP questions and win/loss debrief requirements

**Key insight from testing:** Getting Richard Rumelt's likely feedback EARLY and OFTEN improves results significantly. Currently, Rumelt feedback is only available as Step 7, after all debate rounds are complete.

---

## Problem

### 1. Rumelt Feedback Comes Too Late

The most valuable critique perspective—Rumelt's framework of identifying "bad strategy" markers (fluff, goals-as-strategy, failure to face the challenge)—is currently only available AFTER the debate is complete. This means:

- Multiple debate rounds may refine a fundamentally flawed strategy
- Early fluff and goal-disguised-as-policy issues propagate through rounds
- Users don't get the "is this even a strategy?" check until they've invested significant time and API costs

**Evidence from demo:** The strategy evolved from vague "positioning ambiguity" to precise "no decisive purchase driver" language—but this took 4 rounds. An early Rumelt check on the initial draft would have flagged "positioning ambiguity" as potentially too vague immediately.

### 2. Framework Application is Implicit, Not Systematic

The SKILL.md mentions powerful frameworks (SCQA, Pyramid Principle, Inherent Simplicity, Evaporating Cloud, Confirmation Bias Detection) but:

- They're listed as things Claude "should apply" but there's no structured workflow to ensure they're used
- Users don't see explicit framework analysis in outputs
- No mechanism to ensure each framework is applied to each draft

### 3. Debate Rounds Lack Focus Progression

Currently, users can optionally specify a single focus area (assumptions, coherence, diagnosis, etc.) for critique. However:

- There's no recommended progression of focus areas
- Users don't know which focus to use when
- Early rounds might benefit from different focus than late rounds (e.g., diagnosis focus first, then coherence, then feasibility)

### 4. The "Press" Anti-Laziness Check is Reactive

The `--press` flag exists to force models to confirm they thoroughly reviewed the strategy if they agreed too quickly (rounds 1-2). But:

- It's triggered manually, not automatically
- By the time you notice models agreed too fast, you've already burned a round
- Could be built into the workflow automatically

### 5. No Structured "Strategy Quality Score"

While there's a final quality checklist, there's no quantitative or structured assessment that:

- Tracks quality improvement across rounds
- Provides a clear "strategy readiness" indicator
- Helps users decide when to stop iterating

### 6. Persona Selection is Ad-Hoc

Multiple personas exist (rumelt, strategist, skeptic, operator, competitor, board-member, customer, historian) but:

- No guidance on when to use which persona
- No recommended persona sequences
- Users miss valuable perspectives by not knowing which to select

---

## Analysis

### A. Early Rumelt Integration: Three Options

**Option 1: Rumelt Pre-Screen (Recommended)**
- Add a "Step 0.75" after initial draft, before any debate
- Run Rumelt persona critique on the draft
- Flag bad strategy markers before investing in debate rounds
- Cost: ~$0.05-0.10 per run, but saves multiple rounds if fundamentally flawed

**Option 2: Rumelt as Default First Debate Round**
- Make `--persona rumelt` the automatic first round
- Other models join in round 2+
- Ensures every strategy gets Rumelt-style critique early

**Option 3: Continuous Rumelt Checkpoint**
- After every N rounds (e.g., 2), automatically run a Rumelt checkpoint
- "Is this still a real strategy, or has debate diluted it into mush?"
- Prevents "death by committee" where critique rounds sand off distinctive choices

**Recommendation:** Implement Option 1 (Pre-Screen) AND Option 3 (Periodic Checkpoint). Early catch + ongoing vigilance.

### B. Structured Framework Application

**Proposal: Framework Analysis Phase**

Add an explicit "Framework Analysis" step that systematically applies each relevant framework:

```markdown
## Framework Analysis

### SCQA Check
- Situation: [explicit statement]
- Complication: [explicit statement]
- Question: [the strategic question this answers]
- Answer: [the strategy's answer]
- Assessment: [Pass/Needs Work]

### Inherent Simplicity (Theory of Constraints)
- Identified constraint: [THE binding constraint]
- Does strategy focus on this? [Yes/No with rationale]

### Pyramid Principle Check
- Is recommendation clear upfront? [Yes/No]
- Are supporting arguments well-grouped? [Yes/No]

### Confirmation Bias Detection
- What evidence would DISPROVE this strategy?
- Alternative explanations considered?

### Assumption Risk Matrix
| Assumption | Likelihood Wrong | Impact if Wrong | Risk Rating |
```

**Implementation:** Add `--frameworks` flag that generates this analysis, either standalone or integrated into debate rounds.

### C. Focus Area Progression

**Proposal: Recommended Focus Sequence**

```
Round 1: diagnosis     - Is this even the right problem?
Round 2: assumptions   - What are we taking for granted?
Round 3: coherence     - Do actions reinforce each other?
Round 4: feasibility   - Can we actually execute this?
Round 5: risks         - What could go wrong?
Round 6+: alternatives - Should we consider different approaches?
```

**Implementation options:**
1. Document recommended progression in SKILL.md
2. Add `--auto-focus` flag that cycles through focus areas
3. Add `--focus-sequence diagnosis,assumptions,coherence` for custom progressions

### D. Automatic Anti-Laziness

**Proposal: Smart Press Trigger**

Modify debate.py to automatically trigger press mode when:
- Round 1-2 AND all models agree
- Agreement happens too fast (response time < threshold)
- Response length is suspiciously short

**Implementation:** Add to `call_models_parallel()` or as a wrapper function.

### E. Strategy Quality Score

**Proposal: Quantitative Quality Assessment**

Create a scoring rubric (0-10 scale):

```
Diagnosis Quality (0-10):
- Specificity: Is it about THIS situation, not generic? (0-3)
- Evidence: Based on data, not assumptions? (0-3)
- Focus: Identifies THE constraint, not many? (0-2)
- Root cause: Addresses cause, not symptoms? (0-2)

Guiding Policy Quality (0-10):
- Policy vs Goal: Is it a policy, not a goal? (0-3)
- Leverage: Does it create advantage? (0-3)
- Focus: Does it rule things out? (0-2)
- Coherence: Does it enable the actions? (0-2)

Action Coherence (0-10):
- Mutual reinforcement: Do actions help each other? (0-3)
- Sequencing: Clear dependencies? (0-2)
- Specificity: Concrete enough to execute? (0-3)
- Resource focus: Concentrated, not scattered? (0-2)

Total: /30

Quality Thresholds:
- 25+: Ready for execution
- 20-24: Good, minor refinements needed
- 15-19: Significant issues, more debate needed
- <15: Fundamental problems, revisit diagnosis
```

**Implementation:** Add `--score` flag that outputs structured assessment, or integrate into debate output.

### F. Guided Persona Selection

**Proposal: Persona Recommendation Engine**

Based on strategy type and stage:

```
IF diagnosis seems unclear:
  Recommend: rumelt, strategist

IF actions seem scattered:
  Recommend: operator, skeptic

IF competitive dynamics mentioned:
  Recommend: competitor

IF governance/risk concerns:
  Recommend: board-member

IF customer value unclear:
  Recommend: customer

Late rounds (consensus near):
  Recommend: skeptic (final stress test)
```

**Implementation:** Add `--suggest-persona` that analyzes current strategy and recommends personas.

---

## Recommendations

### Priority 1: Early Rumelt Integration (High Impact, Medium Effort)

**Changes to SKILL.md:**

1. Add "Step 0.9: Rumelt Pre-Screen" after initial draft:
   ```
   Before proceeding to multi-model debate, run a quick Rumelt check:
   - Use debate.py with --persona rumelt --round 0
   - Flag any "bad strategy" markers immediately
   - If fundamental issues found, revise draft before debate
   ```

2. Add "Rumelt Checkpoint" every 2 rounds:
   ```
   After rounds 2, 4, 6, etc., ask:
   "Has this strategy maintained its strategic clarity, or
   has debate diluted it into something generic?"
   ```

**Changes to debate.py:**

3. Add `--prescreen` flag:
   - Runs Rumelt persona critique
   - Outputs structured "Bad Strategy Check" with pass/fail for each marker
   - Recommended before main debate

4. Add `--checkpoint-persona rumelt` flag:
   - Automatically runs specified persona every N rounds
   - Ensures ongoing vigilance against strategy dilution

### Priority 2: Structured Framework Output (Medium Impact, Low Effort)

**Changes to SKILL.md:**

5. Add explicit "Framework Analysis" section to draft output template:
   ```markdown
   ## Framework Analysis

   ### SCQA Flow
   - S: [situation]
   - C: [complication]
   - Q: [question]
   - A: [answer/strategy]

   ### Inherent Simplicity
   - THE constraint: [identified constraint]
   - Strategy addresses it: [yes/no + rationale]

   ### Assumptions (Pre-rated)
   [assumption table with H/M/L ratings]
   ```

6. Require Claude to output this analysis with every draft, not just mention frameworks.

### Priority 3: Focus Progression Guidance (Medium Impact, Low Effort)

**Changes to SKILL.md:**

7. Add "Recommended Focus Progression" section:
   ```
   Round 1: diagnosis (is this the right problem?)
   Round 2: assumptions (what are we assuming?)
   Round 3: coherence (do actions reinforce?)
   Round 4+: feasibility, risks, alternatives as needed
   ```

8. Modify Step 2 to suggest focus based on round number.

**Changes to debate.py:**

9. Add `--auto-focus` flag that cycles through recommended focus areas.

### Priority 4: Quality Scoring (Medium Impact, Medium Effort)

**Changes to debate.py:**

10. Add `--score` flag that outputs quantitative quality assessment (0-30 scale).

11. Include score in JSON output for programmatic use.

**Changes to SKILL.md:**

12. Add quality thresholds to convergence rules:
    ```
    Convergence requires:
    - All models agree, AND
    - Quality score >= 25/30
    ```

### Priority 5: Smart Press Automation (Low Impact, Low Effort)

**Changes to debate.py:**

13. Auto-trigger press mode when:
    - Round <= 2 AND all agree
    - No need for manual `--press` flag in these cases

### Priority 6: Persona Guidance (Low Impact, Low Effort)

**Changes to SKILL.md:**

14. Add "When to Use Each Persona" guidance:
    ```
    - rumelt: First round, periodic checkpoints
    - strategist: General critique, any round
    - skeptic: Final validation, when close to consensus
    - operator: When actions seem unrealistic
    - competitor: When competitive dynamics are central
    - board-member: When risks/governance matter
    - customer: When value proposition is unclear
    ```

---

## Conclusion

The adversarial-strategy plugin is already effective—the demo shows it transforming a decent strategy into a rigorous, commercially-validated plan. However, the key insight that **Rumelt feedback early and often improves results** points to specific, high-value improvements.

**Summary of recommended changes:**

| Priority | Change | Effort | Impact |
|----------|--------|--------|--------|
| P1 | Rumelt Pre-Screen step | Medium | High |
| P1 | Periodic Rumelt Checkpoint | Medium | High |
| P2 | Structured Framework Output | Low | Medium |
| P3 | Focus Progression Guidance | Low | Medium |
| P4 | Quality Scoring System | Medium | Medium |
| P5 | Smart Press Automation | Low | Low |
| P6 | Persona Selection Guidance | Low | Low |

**Implementation approach:**

1. Start with P1 changes (Rumelt Pre-Screen and Checkpoint) as they address the core insight
2. P2-P3 are documentation/prompt changes that can ship quickly
3. P4-P6 are enhancements that can follow based on usage feedback

**Expected outcomes:**

- Fewer wasted debate rounds on fundamentally flawed strategies
- More consistent application of intellectual frameworks
- Clearer guidance for users on how to use the tool effectively
- Better quality strategies with less iteration

---

*Generated: 2026-01-11*
*Based on analysis of: SKILL.md, commands/adversarial-strategy.md, debate.py, demo session outputs*
