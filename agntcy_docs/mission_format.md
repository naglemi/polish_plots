# .agntcy-mission File Format

## Purpose
Defines project-level configuration for multi-agent collaboration, including GitHub Copilot, Roo Code, and Cascade.

## Core Components

### Agent Registry
```yaml
agents:
  - id: github-copilot
    type: code_completion
    capabilities:
      - code_generation
      - code_suggestions
  - id: cascade
    type: agentic_assistant
    capabilities:
      - code_generation
      - code_review
      - system_interaction
  - id: roo-code
    type: code_assistant
    capabilities:
      - code_generation
      - code_analysis
```

### Communication Protocol
```yaml
communication:
  protocol: acp-1.0
  message_format: json
  context_sharing: enabled
```

### Evaluation Settings
```yaml
evaluation:
  metrics:
    - code_quality
    - completion_accuracy
    - response_time
  trust_verification: enabled
```

### Project Configuration
```yaml
project:
  name: polish_plots
  description: Data visualization enhancement tools
  agent_coordination: collaborative
  primary_language: python
```
