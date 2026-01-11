# Adversarial Strategy

A Claude Code plugin for developing rigorous strategies through multi-model adversarial debate. Based on [adversarial-spec](https://github.com/zscole/adversarial-spec) by zscole, adapted for Rumelt strategy development.

Using Richard Rumelt's "Good Strategy/Bad Strategy" framework, this tool helps you create strategies that consist of:

1. **Diagnosis** - A clear explanation of the challenge
2. **Guiding Policy** - The overall approach to tackle the challenge
3. **Coherent Actions** - Coordinated steps that implement the policy

## Features

- **Multi-Model Debate**: Pit your strategy against OpenAI and Anthropic models
- **Intellectual Frameworks**: Built-in support for SCQA, Pyramid Principle, cognitive bias detection, and more
- **Assumption Testing**: Identify and rate assumptions by risk level (H/M/L)
- **Conflict Resolution**: Use Evaporating Cloud to resolve strategic trade-offs
- **Rumelt Feedback**: Simulated feedback from Richard Rumelt's perspective
- **Cost Tracking**: Real-time cost tracking across all models

## Installation

### 1. Add the Plugin Marketplace

```bash
claude plugin marketplace add github:ebowman/adversarial-strategy
```

### 2. Install and Enable the Plugin

```bash
claude plugin install adversarial-strategy@ebowman-adversarial-strategy
```

The plugin is automatically enabled after installation.

### 3. Install Python Dependency

```bash
pip install litellm
```

### 4. Configure API Keys

See [API Key Configuration](#api-key-configuration) below.

### Alternative: Development Setup

If you want to modify the plugin, clone and use `--plugin-dir`:

```bash
git clone https://github.com/ebowman/adversarial-strategy.git ~/src/adversarial-strategy
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
python3 ~/.claude/skills/adversarial-strategy/scripts/debate.py providers
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

Claude will guide you through:
1. Describing your strategic challenge
2. Drafting an initial Rumelt strategy
3. Running multi-model debate to stress-test your strategy
4. Iterating until consensus is reached

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

- `rumelt` - Richard Rumelt's critical perspective
- `strategist` - Senior strategy consultant
- `skeptic` - Devil's advocate perspective
- `operator` - Execution-focused viewpoint
- `competitor` - Competitive response simulation
- `board-member` - Governance perspective

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
