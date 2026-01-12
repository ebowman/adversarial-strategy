# Adversarial Strategy

A Claude Code plugin for developing rigorous strategies through multi-model adversarial debate. Based on [adversarial-spec](https://github.com/zscole/adversarial-spec) by zscole, adapted for Rumelt strategy development.

Using Richard Rumelt's "Good Strategy/Bad Strategy" framework, this tool helps you create strategies that consist of:

1. **Diagnosis** - A clear explanation of the challenge
2. **Guiding Policy** - The overall approach to tackle the challenge
3. **Coherent Actions** - Coordinated steps that implement the policy

## Features

- **Multi-Model Debate**: Pit your strategy against OpenAI and Anthropic models
- **Rumelt Pre-Screen**: Catch "bad strategy" markers BEFORE wasting debate rounds
- **Periodic Rumelt Checkpoints**: Prevent "death by committee" dilution during debate
- **Quality Scoring**: 0-30 scale with clear thresholds for strategy readiness
- **Smart Press**: Auto-triggers confirmation when models agree suspiciously fast
- **Focus Progression**: Guided sequence (diagnosis → assumptions → coherence → feasibility)
- **Intellectual Frameworks**: Built-in SCQA, Pyramid Principle, cognitive bias detection
- **Assumption Testing**: Identify and rate assumptions by risk level (H/M/L)
- **Conflict Resolution**: Use Evaporating Cloud to resolve strategic trade-offs
- **Rumelt Feedback**: Simulated feedback from Richard Rumelt's perspective
- **Cost Tracking**: Real-time cost tracking across all models

## Installation

### Quick Install

```bash
# 1. Add the marketplace and install the plugin
claude plugin marketplace add ebowman/adversarial-strategy
claude plugin install adversarial-strategy@ebowman-adversarial-strategy

# 2. Run the setup script to create venv and install dependencies
~/.claude/plugins/cache/ebowman-adversarial-strategy/adversarial-strategy/1.0.0/setup.sh

# 3. Configure API keys (see below)
```

### Alternative: Development Setup

If you want to modify the plugin:

```bash
git clone git@github.com:ebowman/adversarial-strategy.git ~/src/adversarial-strategy
cd ~/src/adversarial-strategy
./setup.sh
claude --plugin-dir ~/src/adversarial-strategy
```

## API Key Configuration

API keys can be stored in a config file (recommended) or set as environment variables.

### Why Use a Config File?

Environment variables are visible to all processes running as your user. A config file with restricted permissions is more secure—only you can read it.

### Option 1: Config File (Recommended)

1. Create the config directory:
   ```bash
   mkdir -p ~/.config/adversarial-strategy
   ```

2. Create `~/.config/adversarial-strategy/keys.json` with your API keys:
   ```json
   {
     "OPENAI_API_KEY": "sk-...",
     "ANTHROPIC_API_KEY": "sk-ant-..."
   }
   ```

3. Restrict permissions so only you can read it:
   ```bash
   chmod 600 ~/.config/adversarial-strategy/keys.json
   ```

### Option 2: Environment Variables

For CI/CD or when you prefer environment variables:

```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
```

### Precedence

Environment variables take precedence over the config file. This allows you to:
- Store your usual keys in the config file
- Override temporarily with env vars when needed (e.g., testing, CI)

### Verify Your Configuration

```bash
~/.config/adversarial-strategy/venv/bin/python3 ~/.claude/plugins/cache/ebowman-adversarial-strategy/adversarial-strategy/1.0.0/skills/adversarial-strategy/scripts/debate.py providers
```

Output shows each provider's status:
- `[config]` — key loaded from keys.json
- `[env]` — key from environment variable
- `[not set]` — key not configured

## Usage

### Basic Strategy Development

Invoke the skill in Claude Code:
```
/adversarial-strategy
```

### Workflow

Claude will guide you through this optimized workflow:

1. **Input Gathering** - Describe challenge or provide existing document
2. **Interview Mode** (optional) - Deep dive into context, stakeholders, constraints
3. **Draft Strategy** - Create initial Rumelt strategy with framework analysis
4. **Rumelt Pre-Screen** - Check for "bad strategy" markers BEFORE debate
5. **Multi-Model Debate** - Iterative critique with focus progression
6. **Rumelt Checkpoints** - Every 2 rounds, verify strategic clarity maintained
7. **Quality Scoring** - Track improvement toward 25/30 threshold
8. **Finalize** - Output strategy with full documentation

### Key Insight: Rumelt Early and Often

The most valuable critique comes from Rumelt's "bad strategy" framework. This plugin applies it:
- **Before debate** (Pre-Screen): Don't waste rounds on fundamentally flawed strategies
- **During debate** (Checkpoints): Prevent critique from diluting distinctive choices
- **After debate** (Simulation): Detailed feedback in Rumelt's voice

### Interview Mode

For complex challenges, use interview mode for comprehensive requirements gathering:
- Problem context and history
- Stakeholder analysis
- Constraints and resources
- Success criteria
- Risk factors

### Debate Script

Run debates directly from the command line:

```bash
# Basic critique
echo "$STRATEGY" | python3 debate.py critique --models gpt-5.2

# Multiple models
echo "$STRATEGY" | python3 debate.py critique --models gpt-5.2,claude-opus-4-5

# Focus on specific aspects
echo "$STRATEGY" | python3 debate.py critique --models gpt-5.2 --focus assumptions

# Use a professional persona
echo "$STRATEGY" | python3 debate.py critique --models gpt-5.2 --persona "rumelt"
```

### Available Focus Areas

- `assumptions` - Challenge underlying assumptions
- `coherence` - Test action coherence and mutual reinforcement
- `diagnosis` - Scrutinize the problem diagnosis
- `feasibility` - Assess practical feasibility
- `risks` - Identify strategic risks
- `alternatives` - Explore alternative approaches

### Available Personas

| Persona | When to Use |
|---------|-------------|
| `rumelt` | First round, every 2 rounds as checkpoint |
| `strategist` | General critique, any round |
| `skeptic` | Final validation before consensus |
| `operator` | When actions seem unrealistic |
| `competitor` | When competitive dynamics are central |
| `board-member` | When governance/risk concerns are high |

### Recommended Focus Progression

For maximum effectiveness, follow this sequence:

| Round | Focus | Purpose |
|-------|-------|---------|
| 1 | `diagnosis` | Is this even the right problem? |
| 2 | `assumptions` | What are we taking for granted? |
| 3 | `coherence` | Do actions reinforce each other? |
| 4 | `feasibility` | Can we actually execute this? |
| 5+ | `risks`, `alternatives` | What could go wrong? |

### Quality Scoring

Strategies are rated on a 0-30 scale:

- **Diagnosis Quality** (0-10): Specificity, evidence, focus, root cause
- **Guiding Policy Quality** (0-10): Policy vs goal, leverage, focus, coherence
- **Action Coherence** (0-10): Mutual reinforcement, sequencing, specificity, resource focus

**Thresholds:**
- 25+: Ready for execution
- 20-24: Good, minor refinements needed
- 15-19: Significant issues, more debate needed
- <15: Fundamental problems, revisit diagnosis

## Intellectual Frameworks

The plugin incorporates several thinking frameworks:

### Rumelt's Strategy Kernel
- **Diagnosis**: What is the challenge? What aspects are critical?
- **Guiding Policy**: What approach addresses the challenge?
- **Coherent Actions**: What specific, coordinated steps implement the policy?

### SCQA Analysis
- **Situation**: Current context and shared understanding
- **Complication**: The change or problem requiring action
- **Question**: The key question to answer
- **Answer**: The proposed solution

### Pyramid Principle
- Lead with the answer/recommendation
- Group supporting arguments logically
- Provide evidence at the base

### Cognitive Bias Detection
- Confirmation bias
- Anchoring bias
- Overconfidence
- Sunk cost fallacy
- Status quo bias

### Theory of Constraints (Inherent Simplicity)
- Find the single limiting factor
- Focus resources on the constraint
- Complex problems have simple root causes

### Evaporating Cloud
- Map conflicting positions to underlying needs
- Identify shared objectives
- Challenge assumptions to "evaporate" the conflict

### Assumption Risk Assessment
- **High (H)**: Likely wrong, would undermine strategy
- **Medium (M)**: Could be wrong, significant impact
- **Low (L)**: Unlikely wrong, minimal impact

## Configuration

### Profiles

Save frequently-used configurations:

```bash
# Save a profile
python3 debate.py save-profile rigorous-test --models gpt-5.2,claude-opus-4-5 --focus assumptions

# Use a profile
echo "$STRATEGY" | python3 debate.py critique --profile rigorous-test
```

### Sessions

Long debates can be saved and resumed:

```bash
# Start a session
echo "$STRATEGY" | python3 debate.py critique --models gpt-5.2 --session my-strategy

# Resume later
python3 debate.py critique --resume my-strategy
```

## Output

Final strategies are saved to `strategy-output.md` and include:
- Complete Rumelt strategy kernel
- Assumption register with risk ratings
- Key refinements from debate
- Round count and participating models
- Total cost

## Supported Models

| Provider | Models | API Key |
|----------|--------|---------|
| OpenAI | gpt-5.2, gpt-5.2-pro, o1 | OPENAI_API_KEY |
| Anthropic | claude-opus-4-5 | ANTHROPIC_API_KEY |

## Acknowledgments

This project is based on [adversarial-spec](https://github.com/zscole/adversarial-spec) by [zscole](https://github.com/zscole), which pioneered the multi-model adversarial debate approach for refining specifications.

## License

MIT License - See LICENSE file for details.
