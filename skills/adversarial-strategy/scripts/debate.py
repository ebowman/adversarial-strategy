#!/usr/bin/env python3
"""
Adversarial strategy debate script.
Sends strategies to multiple LLMs for critique using LiteLLM.

Usage:
    echo "strategy" | python3 debate.py critique --models gpt-5.2
    echo "strategy" | python3 debate.py critique --models gpt-5.2,claude-opus-4-5
    echo "strategy" | python3 debate.py critique --models gpt-5.2 --focus assumptions
    echo "strategy" | python3 debate.py critique --models gpt-5.2 --persona rumelt
    python3 debate.py providers

API Key Configuration:
    Keys are loaded from ~/.config/adversarial-strategy/keys.json (recommended)
    or from environment variables. Config file format:
    {"OPENAI_API_KEY": "sk-...", "ANTHROPIC_API_KEY": "sk-ant-..."}

Supported providers:
    OpenAI:    OPENAI_API_KEY      models: gpt-5.2, gpt-5.2-pro, o1
    Anthropic: ANTHROPIC_API_KEY   models: claude-opus-4-5

Exit codes:
    0 - Success
    1 - API error
    2 - Missing API key or config error
"""

import os
import sys
import argparse
import json
import difflib
import time
import concurrent.futures
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime

os.environ["LITELLM_LOG"] = "ERROR"

try:
    import litellm
    from litellm import completion
    litellm.suppress_debug_info = True
except ImportError:
    print("Error: litellm package not installed. Run: pip install litellm", file=sys.stderr)
    sys.exit(1)

# Cost per 1M tokens (as of January 2026)
MODEL_COSTS = {
    "gpt-5.2": {"input": 1.75, "output": 14.00},
    "gpt-5.2-pro": {"input": 15.00, "output": 60.00},
    "o1": {"input": 15.00, "output": 60.00},
    "claude-opus-4-5": {"input": 5.00, "output": 25.00},
}

DEFAULT_COST = {"input": 5.00, "output": 15.00}

CONFIG_DIR = Path.home() / ".config" / "adversarial-strategy"
KEYS_FILE = CONFIG_DIR / "keys.json"
PROFILES_DIR = CONFIG_DIR / "profiles"
SESSIONS_DIR = CONFIG_DIR / "sessions"
CHECKPOINTS_DIR = Path.cwd() / ".adversarial-strategy-checkpoints"

# Track which keys were loaded from config file vs environment
_keys_from_config = set()

MAX_RETRIES = 3
RETRY_BASE_DELAY = 1.0  # seconds


def load_api_keys():
    """Load API keys from config file, falling back to environment variables.

    Keys in the config file are set as environment variables so litellm can use them.
    Environment variables take precedence (config file won't overwrite existing env vars).

    Config file location: ~/.config/adversarial-strategy/keys.json
    Format: {"OPENAI_API_KEY": "sk-...", "GEMINI_API_KEY": "..."}
    """
    global _keys_from_config

    if not KEYS_FILE.exists():
        return

    try:
        keys = json.loads(KEYS_FILE.read_text())
        for key_name, key_value in keys.items():
            if key_name.endswith("_API_KEY") and key_value:
                # Only set if not already in environment (env vars take precedence)
                if not os.environ.get(key_name):
                    os.environ[key_name] = key_value
                    _keys_from_config.add(key_name)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Could not load keys from {KEYS_FILE}: {e}", file=sys.stderr)


PRESERVE_INTENT_PROMPT = """
**PRESERVE STRATEGIC INTENT**
This strategy represents deliberate choices. Before suggesting ANY removal or substantial modification:

1. ASSUME the strategist had good reasons for each element
2. For EVERY removal or substantial change you propose, you MUST:
   - Quote the exact text you want to remove/change
   - Explain what problem it causes (not just "unnecessary" or "could be simpler")
   - Describe the concrete harm if it remains vs the benefit of removal
   - Consider: Is this genuinely wrong, or just different from what you'd write?

3. Distinguish between:
   - ERRORS: Factually wrong, contradictory, or logically broken (remove/fix these)
   - RISKS: Unaddressed risks, missing assumptions, gaps in logic (flag these)
   - PREFERENCES: Different style, structure, or approach (DO NOT remove these)

4. If something seems unusual but isn't broken, ASK about it rather than removing it:
   "The strategy includes X which is unconventional. Was this intentional? If so, consider documenting the rationale."

5. Your critique should ADD rigor, not sand off distinctive choices.

Treat removal like strategy review: additions are cheap, deletions require justification.
"""

FOCUS_AREAS = {
    "assumptions": """
**CRITICAL FOCUS: ASSUMPTIONS**
Prioritize assumption analysis above all else. Specifically examine:
- What is being taken for granted?
- Which assumptions are high-risk (likely wrong AND high impact)?
- What evidence supports each assumption?
- What would invalidate key assumptions?
- Are there alternative explanations for observed patterns?
- What assumptions about competitors, customers, or market are being made?
- What assumptions about internal capabilities exist?
- Are there confirmation biases at play?
Rate each assumption: H (High risk), M (Medium risk), L (Low risk).
Flag untested high-risk assumptions as blocking issues.""",

    "coherence": """
**CRITICAL FOCUS: ACTION COHERENCE**
Prioritize coherence analysis above all else. Specifically examine:
- Do the actions reinforce each other or fight each other?
- Are resources being concentrated or scattered?
- Is there a clear sequence and dependency structure?
- Do near-term actions enable medium-term actions?
- Are there conflicting priorities that dilute focus?
- Would completing action A make action B easier or harder?
- Is there a "main effort" that other actions support?
- Are actions coordinated across functions/teams?
Flag any coherence gaps as blocking issues.""",

    "diagnosis": """
**CRITICAL FOCUS: DIAGNOSIS QUALITY**
Prioritize diagnosis analysis above all else. Specifically examine:
- Does the diagnosis identify THE critical challenge? (Inherent Simplicity)
- Is the diagnosis based on evidence or assumption?
- Does it explain WHY this is the key challenge?
- Are there alternative diagnoses that could explain the situation?
- Is the diagnosis too broad (boiling the ocean) or too narrow (missing the point)?
- Does it identify root causes or just symptoms?
- Would Richard Rumelt agree this is a proper diagnosis?
- Is there confirmation bias in how the challenge is framed?
Flag diagnostic weaknesses as blocking issues.""",

    "feasibility": """
**CRITICAL FOCUS: FEASIBILITY**
Prioritize feasibility analysis above all else. Specifically examine:
- Are the required capabilities available or buildable?
- Is the timeline realistic given complexity?
- Are resource requirements explicitly identified?
- What dependencies exist and are they acknowledged?
- What organizational barriers might prevent execution?
- Is there sufficient commitment from key stakeholders?
- Are the actions within the organization's capacity?
- What "activation energy" is required to get started?
Flag feasibility gaps as blocking issues.""",

    "risks": """
**CRITICAL FOCUS: STRATEGIC RISKS**
Prioritize risk analysis above all else. Specifically examine:
- What could make this strategy fail completely?
- How might competitors respond?
- What external factors could invalidate assumptions?
- Are there single points of failure?
- What happens if key people leave?
- Are there regulatory or legal risks?
- What reputational risks exist?
- Is there adequate mitigation for high-impact risks?
Flag unmitigated high-impact risks as blocking issues.""",

    "alternatives": """
**CRITICAL FOCUS: ALTERNATIVE APPROACHES**
Prioritize alternative analysis above all else. Specifically examine:
- What other guiding policies could address this diagnosis?
- What would a competitor do differently?
- What would a contrarian perspective suggest?
- Are there lower-risk alternatives?
- Are there faster alternatives?
- What would a "10x" approach look like?
- What would the opposite strategy be?
- Why is this approach better than alternatives?
Propose at least 2 alternative approaches and explain trade-offs.""",
}

PERSONAS = {
    "rumelt": """You are Richard Rumelt, author of "Good Strategy/Bad Strategy." You have a sharp eye for distinguishing genuine strategy from fluff, goals, and wishful thinking.

You always ask:
- "What is the kernel of this strategy?"
- "Is the guiding policy actually a policy, or just a goal in disguise?"
- "Do the actions create focused, coordinated effort?"

You quickly identify bad strategy markers:
- Fluff (buzzwords masking lack of thought)
- Failure to face the challenge
- Mistaking goals for strategy
- Bad strategic objectives that don't address the diagnosis

You are intellectually rigorous but constructive. You want to help create GOOD strategy.""",

    "strategist": """You are a senior strategy consultant with 20+ years of experience at top firms. You've seen strategies succeed and fail across industries.

You evaluate strategies on:
- Clarity of the central challenge
- Coherence of the action plan
- Quality of evidence and analysis
- Feasibility given real-world constraints
- Competitive differentiation

You ask probing questions and challenge assumptions. You've seen too many strategies fail from vagueness, overconfidence, or lack of focus.""",

    "skeptic": """You are a professional skeptic and devil's advocate. Your job is to find weaknesses, not validate the strategy.

You systematically challenge:
- Every assumption (especially implicit ones)
- The causal logic ("Why will A lead to B?")
- Optimistic projections
- Claimed advantages
- Ignored risks

You ask uncomfortable questions. If something seems too convenient or too optimistic, you probe it. You're not negative - you're rigorous.""",

    "operator": """You are a COO/VP Operations who has to actually execute strategies. You've seen brilliant strategies fail in execution.

You focus on:
- Can we actually do this? (capability reality check)
- Do we have the people, systems, and processes?
- What will break when we try to execute?
- Are the timelines realistic?
- Where are the coordination challenges?
- What will the front-line teams think?

You bring execution reality to strategic discussions.""",

    "competitor": """You are a smart competitor analyzing this strategy to respond to it.

You look for:
- What are they signaling about their priorities?
- Where are they vulnerable during transition?
- How can we counter their moves?
- What would block this strategy's success?
- Where are the gaps we can exploit?

You help stress-test the strategy by showing how a competitor might respond.""",

    "board-member": """You are an experienced board member focused on governance and fiduciary duty.

You evaluate:
- Is this strategy prudent given the risks?
- Are stakeholder interests balanced?
- Is there adequate oversight and measurement?
- What are the downside scenarios?
- Is management being realistic or overconfident?
- Are resources being allocated responsibly?

You bring governance rigor and risk awareness.""",

    "customer": """You are a demanding customer or end-user of the organization's products/services.

You ask:
- How does this strategy benefit ME?
- Will this actually solve my problems?
- Why should I care about your internal initiatives?
- What will change in my experience?
- Are you listening to what I actually need?

You bring outside-in customer perspective.""",

    "historian": """You are a business historian who has studied strategy successes and failures throughout history.

You draw on:
- Historical parallels and analogies
- Patterns of strategic failure
- Case studies of similar situations
- Long-term thinking about consequences
- The "second-order effects" often missed

You help contextualize the strategy in broader patterns.""",
}

SYSTEM_PROMPT_STRATEGY = """You are a senior strategist participating in adversarial strategy development using Richard Rumelt's framework.

You will receive a strategy document containing a Diagnosis, Guiding Policy, and Coherent Actions. Your job is to critique it rigorously.

## Rumelt's Framework

A good strategy has three elements:

**Diagnosis**: A clear explanation of the challenge. Must be:
- Specific to the situation (not generic)
- Evidence-based (not assumption-based)
- Identifies what aspects are CRITICAL
- Explains WHY this is the key challenge

**Guiding Policy**: The overall approach. Must be:
- Actually a POLICY (not a goal or aspiration)
- Creates leverage or advantage
- Rules out certain actions while enabling others
- Focused (not scattered across multiple fronts)

**Coherent Actions**: Coordinated steps. Must be:
- Mutually reinforcing (not fighting each other)
- Properly sequenced and dependent
- Specific enough to execute
- Aligned with the guiding policy

## Your Critique Should Address:

1. **Diagnosis Quality**
   - Is this the REAL challenge, or a symptom?
   - Is there evidence, or just assumptions?
   - Is it focused enough?

2. **Policy vs Goals**
   - Is the guiding policy actually a policy?
   - Does it create leverage?
   - What does it rule out?

3. **Action Coherence**
   - Do actions reinforce each other?
   - Are resources concentrated?
   - Is there a main effort?

4. **Assumptions**
   - What is being assumed?
   - Which assumptions are high-risk?
   - How can they be tested?

5. **Risks**
   - What could make this fail?
   - Are risks adequately mitigated?

## Output Format

If you find significant issues:
- Provide a clear critique explaining each problem
- Apply relevant frameworks (SCQA, Inherent Simplicity, Evaporating Cloud if conflicts exist)
- Output your revised strategy that addresses these issues
- Format: First your critique, then the revised strategy between [SPEC] and [/SPEC] tags

If the strategy is solid and ready for execution:
- Output exactly [AGREE] on its own line
- Then output the final strategy between [SPEC] and [/SPEC] tags

Be rigorous. A good strategy should let any leader understand exactly what challenge they're addressing, what approach they're taking, and what specific actions to prioritize."""

REVIEW_PROMPT_TEMPLATE = """This is round {round} of adversarial strategy development.

Here is the current strategy:

{spec}

{context_section}
{focus_section}

Review this strategy using Rumelt's framework. Either critique and revise it, or say [AGREE] if it's ready for execution."""

PRESS_PROMPT_TEMPLATE = """This is round {round} of adversarial strategy development. You previously indicated agreement with this strategy.

Here is the current strategy:

{spec}

{context_section}

**IMPORTANT: Please confirm your agreement by thoroughly reviewing the ENTIRE strategy.**

Before saying [AGREE], you MUST:
1. Confirm you have read every section of this strategy
2. Verify the diagnosis identifies a REAL, SPECIFIC challenge (not generic)
3. Verify the guiding policy is a POLICY (not a goal disguised as strategy)
4. Verify the actions are COHERENT (reinforce each other, not scattered)
5. List at least 3 specific elements you verified
6. Identify ANY remaining concerns, however minor

If after this thorough review you find issues you missed before, provide your critique.

If you genuinely agree after careful review, output:
1. Your verification (what you checked, why you agree)
2. [AGREE] on its own line
3. The final strategy between [SPEC] and [/SPEC] tags"""


@dataclass
class ModelResponse:
    model: str
    response: str
    agreed: bool
    spec: Optional[str]
    error: Optional[str] = None
    input_tokens: int = 0
    output_tokens: int = 0
    cost: float = 0.0


@dataclass
class CostTracker:
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost: float = 0.0
    by_model: dict = field(default_factory=dict)

    def add(self, model: str, input_tokens: int, output_tokens: int):
        costs = MODEL_COSTS.get(model, DEFAULT_COST)
        cost = (input_tokens / 1_000_000 * costs["input"]) + (output_tokens / 1_000_000 * costs["output"])

        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_cost += cost

        if model not in self.by_model:
            self.by_model[model] = {"input_tokens": 0, "output_tokens": 0, "cost": 0.0}
        self.by_model[model]["input_tokens"] += input_tokens
        self.by_model[model]["output_tokens"] += output_tokens
        self.by_model[model]["cost"] += cost

        return cost

    def summary(self) -> str:
        lines = ["", "=== Cost Summary ==="]
        lines.append(f"Total tokens: {self.total_input_tokens:,} in / {self.total_output_tokens:,} out")
        lines.append(f"Total cost: ${self.total_cost:.4f}")
        if len(self.by_model) > 1:
            lines.append("")
            lines.append("By model:")
            for model, data in self.by_model.items():
                lines.append(f"  {model}: ${data['cost']:.4f} ({data['input_tokens']:,} in / {data['output_tokens']:,} out)")
        return "\n".join(lines)


cost_tracker = CostTracker()


@dataclass
class SessionState:
    """Persisted state for resume functionality."""
    session_id: str
    spec: str
    round: int
    models: list
    focus: Optional[str] = None
    persona: Optional[str] = None
    preserve_intent: bool = False
    created_at: str = ""
    updated_at: str = ""
    history: list = field(default_factory=list)

    def save(self):
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        self.updated_at = datetime.now().isoformat()
        path = SESSIONS_DIR / f"{self.session_id}.json"
        path.write_text(json.dumps(asdict(self), indent=2))

    @classmethod
    def load(cls, session_id: str) -> "SessionState":
        path = SESSIONS_DIR / f"{session_id}.json"
        if not path.exists():
            raise FileNotFoundError(f"Session '{session_id}' not found")
        data = json.loads(path.read_text())
        return cls(**data)

    @classmethod
    def list_sessions(cls) -> list[dict]:
        if not SESSIONS_DIR.exists():
            return []
        sessions = []
        for p in SESSIONS_DIR.glob("*.json"):
            try:
                data = json.loads(p.read_text())
                sessions.append({
                    "id": data["session_id"],
                    "round": data["round"],
                    "updated_at": data.get("updated_at", ""),
                })
            except Exception:
                pass
        return sorted(sessions, key=lambda x: x.get("updated_at", ""), reverse=True)


def save_checkpoint(spec: str, round_num: int, session_id: Optional[str] = None):
    """Save spec checkpoint for this round."""
    CHECKPOINTS_DIR.mkdir(parents=True, exist_ok=True)
    prefix = f"{session_id}-" if session_id else ""
    path = CHECKPOINTS_DIR / f"{prefix}round-{round_num}.md"
    path.write_text(spec)
    print(f"Checkpoint saved: {path}", file=sys.stderr)


def get_system_prompt(persona: Optional[str] = None) -> str:
    if persona:
        persona_key = persona.lower().replace(" ", "-").replace("_", "-")
        if persona_key in PERSONAS:
            return PERSONAS[persona_key] + "\n\n" + SYSTEM_PROMPT_STRATEGY
        else:
            return f"You are a {persona} participating in adversarial strategy development.\n\n" + SYSTEM_PROMPT_STRATEGY

    return SYSTEM_PROMPT_STRATEGY


def load_context_files(context_paths: list[str]) -> str:
    if not context_paths:
        return ""

    sections = []
    for path in context_paths:
        try:
            content = Path(path).read_text()
            sections.append(f"### Context: {path}\n```\n{content}\n```")
        except Exception as e:
            sections.append(f"### Context: {path}\n[Error loading file: {e}]")

    return "## Additional Context\nThe following documents are provided as context:\n\n" + "\n\n".join(sections)


def load_profile(profile_name: str) -> dict:
    profile_path = PROFILES_DIR / f"{profile_name}.json"
    if not profile_path.exists():
        print(f"Error: Profile '{profile_name}' not found at {profile_path}", file=sys.stderr)
        sys.exit(2)

    try:
        return json.loads(profile_path.read_text())
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in profile '{profile_name}': {e}", file=sys.stderr)
        sys.exit(2)


def save_profile(profile_name: str, config: dict):
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    profile_path = PROFILES_DIR / f"{profile_name}.json"
    profile_path.write_text(json.dumps(config, indent=2))
    print(f"Profile saved to {profile_path}")


def list_profiles():
    print("Saved Profiles:\n")
    if not PROFILES_DIR.exists():
        print("  No profiles found.")
        print(f"\n  Profiles are stored in: {PROFILES_DIR}")
        print("\n  Create a profile with: python3 debate.py save-profile <name> --models ... --focus ...")
        return

    profiles = list(PROFILES_DIR.glob("*.json"))
    if not profiles:
        print("  No profiles found.")
        return

    for p in sorted(profiles):
        try:
            config = json.loads(p.read_text())
            name = p.stem
            models = config.get("models", "not set")
            focus = config.get("focus", "none")
            persona = config.get("persona", "none")
            preserve = "yes" if config.get("preserve_intent") else "no"
            print(f"  {name}")
            print(f"    models: {models}")
            print(f"    focus: {focus}")
            print(f"    persona: {persona}")
            print(f"    preserve-intent: {preserve}")
            print()
        except Exception:
            print(f"  {p.stem} [error reading]")


def call_single_model(
    model: str,
    spec: str,
    round_num: int,
    press: bool = False,
    focus: Optional[str] = None,
    persona: Optional[str] = None,
    context: Optional[str] = None,
    preserve_intent: bool = False
) -> ModelResponse:
    """Send strategy to a single model and return response with retry on failure."""
    system_prompt = get_system_prompt(persona)

    focus_section = ""
    if focus and focus.lower() in FOCUS_AREAS:
        focus_section = FOCUS_AREAS[focus.lower()]
    elif focus:
        focus_section = f"**CRITICAL FOCUS: {focus.upper()}**\nPrioritize analysis of {focus} concerns above all else."

    if preserve_intent:
        focus_section = PRESERVE_INTENT_PROMPT + "\n\n" + focus_section

    context_section = context if context else ""

    template = PRESS_PROMPT_TEMPLATE if press else REVIEW_PROMPT_TEMPLATE
    user_message = template.format(
        round=round_num,
        spec=spec,
        focus_section=focus_section,
        context_section=context_section
    )

    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            response = completion(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                max_tokens=8000
            )
            content = response.choices[0].message.content
            agreed = "[AGREE]" in content
            extracted = extract_spec(content)

            # Validation warning if model critiqued but didn't provide revised spec
            if not agreed and not extracted:
                print(f"Warning: {model} provided critique but no [SPEC] tags found. Response may be malformed.", file=sys.stderr)

            input_tokens = response.usage.prompt_tokens if response.usage else 0
            output_tokens = response.usage.completion_tokens if response.usage else 0
            cost = cost_tracker.add(model, input_tokens, output_tokens)

            return ModelResponse(
                model=model,
                response=content,
                agreed=agreed,
                spec=extracted,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost=cost
            )
        except Exception as e:
            last_error = str(e)
            if attempt < MAX_RETRIES - 1:
                delay = RETRY_BASE_DELAY * (2 ** attempt)  # exponential backoff
                print(f"Warning: {model} failed (attempt {attempt + 1}/{MAX_RETRIES}): {last_error}. Retrying in {delay:.1f}s...", file=sys.stderr)
                time.sleep(delay)
            else:
                print(f"Error: {model} failed after {MAX_RETRIES} attempts: {last_error}", file=sys.stderr)

    return ModelResponse(model=model, response="", agreed=False, spec=None, error=last_error)


def call_models_parallel(
    models: list[str],
    spec: str,
    round_num: int,
    press: bool = False,
    focus: Optional[str] = None,
    persona: Optional[str] = None,
    context: Optional[str] = None,
    preserve_intent: bool = False
) -> list[ModelResponse]:
    """Call multiple models in parallel and collect responses."""
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(models)) as executor:
        future_to_model = {
            executor.submit(
                call_single_model, model, spec, round_num, press, focus, persona, context, preserve_intent
            ): model
            for model in models
        }
        for future in concurrent.futures.as_completed(future_to_model):
            results.append(future.result())
    return results


def extract_spec(response: str) -> Optional[str]:
    if "[SPEC]" not in response or "[/SPEC]" not in response:
        return None
    start = response.find("[SPEC]") + len("[SPEC]")
    end = response.find("[/SPEC]")
    return response[start:end].strip()


def get_critique_summary(response: str, max_length: int = 300) -> str:
    spec_start = response.find("[SPEC]")
    if spec_start > 0:
        critique = response[:spec_start].strip()
    else:
        critique = response

    if len(critique) > max_length:
        critique = critique[:max_length] + "..."
    return critique


def generate_diff(previous: str, current: str) -> str:
    """Generate unified diff between two strategies."""
    prev_lines = previous.splitlines(keepends=True)
    curr_lines = current.splitlines(keepends=True)

    diff = difflib.unified_diff(
        prev_lines,
        curr_lines,
        fromfile="previous",
        tofile="current",
        lineterm=""
    )
    return "".join(diff)


def list_providers():
    providers = [
        ("OpenAI", "OPENAI_API_KEY", "gpt-5.2, gpt-5.2-pro, o1"),
        ("Anthropic", "ANTHROPIC_API_KEY", "claude-opus-4-5"),
    ]
    print("Supported providers:\n")
    for name, key, models in providers:
        if os.environ.get(key):
            if key in _keys_from_config:
                status = "[config]"
            else:
                status = "[env]"
        else:
            status = "[not set]"
        print(f"  {name:12} {key:24} {status}")
        print(f"             Example models: {models}")
        print()

    print(f"Config file: {KEYS_FILE}")
    if KEYS_FILE.exists():
        print("  (exists)")
    else:
        print("  (not found - create to store API keys securely)")


def list_focus_areas():
    print("Available focus areas (--focus):\n")
    for name, description in FOCUS_AREAS.items():
        first_line = description.strip().split("\n")[1] if "\n" in description else description[:60]
        print(f"  {name:15} {first_line.strip()[:60]}")
    print()


def list_personas():
    print("Available personas (--persona):\n")
    for name, description in PERSONAS.items():
        print(f"  {name}")
        print(f"    {description[:80]}...")
        print()


def main():
    # Load API keys from config file (falls back to environment variables)
    load_api_keys()

    parser = argparse.ArgumentParser(
        description="Adversarial strategy debate with multiple LLMs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  echo "strategy" | python3 debate.py critique --models gpt-5.2
  echo "strategy" | python3 debate.py critique --models gpt-5.2 --focus assumptions
  echo "strategy" | python3 debate.py critique --models gpt-5.2 --persona rumelt
  echo "strategy" | python3 debate.py critique --models gpt-5.2 --context ./analysis.md
  echo "strategy" | python3 debate.py critique --profile rigorous
  python3 debate.py diff --previous old.md --current new.md
  python3 debate.py providers
  python3 debate.py focus-areas
  python3 debate.py personas
  python3 debate.py profiles
  python3 debate.py save-profile myprofile --models gpt-5.2,gemini/gemini-2.5-flash --focus assumptions
        """
    )
    parser.add_argument("action", choices=["critique", "providers", "diff", "focus-areas", "personas", "profiles", "save-profile", "sessions"],
                        help="Action to perform")
    parser.add_argument("profile_name", nargs="?", help="Profile name (for save-profile action)")
    parser.add_argument("--models", "-m", default="gpt-5.2",
                        help="Comma-separated list of models (e.g., gpt-5.2,gemini/gemini-2.5-flash,xai/grok-3)")
    parser.add_argument("--round", "-r", type=int, default=1,
                        help="Current round number")
    parser.add_argument("--json", "-j", action="store_true",
                        help="Output as JSON")
    parser.add_argument("--press", "-p", action="store_true",
                        help="Press models to confirm they read the full strategy (anti-laziness check)")
    parser.add_argument("--focus", "-f",
                        help="Focus area for critique (assumptions, coherence, diagnosis, feasibility, risks, alternatives)")
    parser.add_argument("--persona",
                        help="Persona for critique (rumelt, strategist, skeptic, operator, competitor, board-member)")
    parser.add_argument("--context", "-c", action="append", default=[],
                        help="Additional context file(s) to include (can be used multiple times)")
    parser.add_argument("--profile",
                        help="Load settings from a saved profile")
    parser.add_argument("--previous",
                        help="Previous strategy file (for diff action)")
    parser.add_argument("--current",
                        help="Current strategy file (for diff action)")
    parser.add_argument("--show-cost", action="store_true",
                        help="Show cost summary after critique")
    parser.add_argument("--preserve-intent", action="store_true",
                        help="Require explicit justification for any removal or substantial modification")
    parser.add_argument("--session", "-s",
                        help="Session ID for state persistence (enables checkpointing and resume)")
    parser.add_argument("--resume",
                        help="Resume a previous session by ID")
    args = parser.parse_args()

    # Handle simple info commands
    if args.action == "providers":
        list_providers()
        return

    if args.action == "focus-areas":
        list_focus_areas()
        return

    if args.action == "personas":
        list_personas()
        return

    if args.action == "profiles":
        list_profiles()
        return

    if args.action == "sessions":
        sessions = SessionState.list_sessions()
        print("Saved Sessions:\n")
        if not sessions:
            print("  No sessions found.")
            print(f"\n  Sessions are stored in: {SESSIONS_DIR}")
            print("\n  Start a session with: --session <name>")
        else:
            for s in sessions:
                print(f"  {s['id']}")
                print(f"    round: {s['round']}")
                print(f"    updated: {s['updated_at'][:19] if s['updated_at'] else 'unknown'}")
                print()
        return

    if args.action == "save-profile":
        if not args.profile_name:
            print("Error: Profile name required", file=sys.stderr)
            sys.exit(1)
        config = {
            "models": args.models,
            "focus": args.focus,
            "persona": args.persona,
            "context": args.context,
            "preserve_intent": args.preserve_intent,
        }
        save_profile(args.profile_name, config)
        return

    if args.action == "diff":
        if not args.previous or not args.current:
            print("Error: --previous and --current required for diff", file=sys.stderr)
            sys.exit(1)
        try:
            prev_content = Path(args.previous).read_text()
            curr_content = Path(args.current).read_text()
            diff = generate_diff(prev_content, curr_content)
            if diff:
                print(diff)
            else:
                print("No differences found.")
        except Exception as e:
            print(f"Error reading files: {e}", file=sys.stderr)
            sys.exit(1)
        return

    # Load profile if specified
    if args.profile:
        profile = load_profile(args.profile)
        if "models" in profile and args.models == "gpt-5.2":
            args.models = profile["models"]
        if "focus" in profile and not args.focus:
            args.focus = profile["focus"]
        if "persona" in profile and not args.persona:
            args.persona = profile["persona"]
        if "context" in profile and not args.context:
            args.context = profile["context"]
        if profile.get("preserve_intent") and not args.preserve_intent:
            args.preserve_intent = profile["preserve_intent"]

    # Parse models list
    models = [m.strip() for m in args.models.split(",") if m.strip()]
    if not models:
        print("Error: No models specified", file=sys.stderr)
        sys.exit(1)

    # Load context files
    context = load_context_files(args.context) if args.context else None

    # Handle resume
    session_state = None
    if args.resume:
        try:
            session_state = SessionState.load(args.resume)
            print(f"Resuming session '{args.resume}' at round {session_state.round}", file=sys.stderr)
            spec = session_state.spec
            args.round = session_state.round
            args.models = ",".join(session_state.models)
            if session_state.focus:
                args.focus = session_state.focus
            if session_state.persona:
                args.persona = session_state.persona
            if session_state.preserve_intent:
                args.preserve_intent = session_state.preserve_intent
            # Re-parse models
            models = session_state.models
        except FileNotFoundError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(2)
    else:
        # Main critique action
        spec = sys.stdin.read().strip()
        if not spec:
            print("Error: No strategy provided via stdin", file=sys.stderr)
            sys.exit(1)

    # Initialize session if --session provided
    if args.session and not session_state:
        session_state = SessionState(
            session_id=args.session,
            spec=spec,
            round=args.round,
            models=models,
            focus=args.focus,
            persona=args.persona,
            preserve_intent=args.preserve_intent,
            created_at=datetime.now().isoformat(),
        )
        session_state.save()
        print(f"Session '{args.session}' created", file=sys.stderr)

    mode = "pressing for confirmation" if args.press else "critiquing"
    focus_info = f" (focus: {args.focus})" if args.focus else ""
    persona_info = f" (persona: {args.persona})" if args.persona else ""
    preserve_info = " (preserve-intent)" if args.preserve_intent else ""
    print(f"Calling {len(models)} model(s) ({mode}){focus_info}{persona_info}{preserve_info}: {', '.join(models)}...", file=sys.stderr)

    results = call_models_parallel(
        models, spec, args.round, args.press,
        args.focus, args.persona, context, args.preserve_intent
    )

    errors = [r for r in results if r.error]
    for e in errors:
        print(f"Warning: {e.model} returned error: {e.error}", file=sys.stderr)

    successful = [r for r in results if not r.error]
    all_agreed = all(r.agreed for r in successful) if successful else False

    # Save checkpoint after each round
    session_id = session_state.session_id if session_state else args.session
    if session_id or args.session:
        save_checkpoint(spec, args.round, session_id)

    # Get the latest spec from results (first non-agreed response with a spec)
    latest_spec = spec
    for r in successful:
        if r.spec:
            latest_spec = r.spec
            break

    # Update session state
    if session_state:
        session_state.spec = latest_spec
        session_state.round = args.round + 1
        session_state.history.append({
            "round": args.round,
            "all_agreed": all_agreed,
            "models": [{"model": r.model, "agreed": r.agreed, "error": r.error} for r in results],
        })
        session_state.save()

    if args.json:
        output = {
            "all_agreed": all_agreed,
            "round": args.round,
            "models": models,
            "focus": args.focus,
            "persona": args.persona,
            "preserve_intent": args.preserve_intent,
            "session": session_state.session_id if session_state else args.session,
            "results": [
                {
                    "model": r.model,
                    "agreed": r.agreed,
                    "response": r.response,
                    "spec": r.spec,
                    "error": r.error,
                    "input_tokens": r.input_tokens,
                    "output_tokens": r.output_tokens,
                    "cost": r.cost
                }
                for r in results
            ],
            "cost": {
                "total": cost_tracker.total_cost,
                "input_tokens": cost_tracker.total_input_tokens,
                "output_tokens": cost_tracker.total_output_tokens,
                "by_model": cost_tracker.by_model
            }
        }
        print(json.dumps(output, indent=2))
    else:
        print(f"\n=== Round {args.round} Results (Strategy) ===\n")

        for r in results:
            print(f"--- {r.model} ---")
            if r.error:
                print(f"ERROR: {r.error}")
            elif r.agreed:
                print("[AGREE]")
            else:
                print(r.response)
            print()

        if all_agreed:
            print("=== ALL MODELS AGREE ===")
        else:
            agreed_models = [r.model for r in successful if r.agreed]
            disagreed_models = [r.model for r in successful if not r.agreed]
            if agreed_models:
                print(f"Agreed: {', '.join(agreed_models)}")
            if disagreed_models:
                print(f"Critiqued: {', '.join(disagreed_models)}")

        if args.show_cost or True:  # Always show cost
            print(cost_tracker.summary())


if __name__ == "__main__":
    main()
