# VeriFood-RLVR

A dietary safety AI that uses reinforcement learning with verifiable rewards to eliminate hallucinations in allergy and dietary restriction checking.

## The Problem

Current AI assistants for dietary safety (GPT-4, Claude, etc.) hallucinate about 7% of the time on allergen questions. When someone with a severe peanut allergy asks if a dish is safe, 7% failure rate is unacceptable. The issue is that these models generate "vibes-based" answers rather than systematic reasoning.

## The Approach

Instead of traditional fine-tuning, this project uses **Reinforcement Learning from Verifiable Rewards (RLVR)** to train a model that:

1. **Shows its work**: The model generates explicit reasoning chains (`<think>` tags) explaining why something is or isn't safe
2. **Gets checked by code**: A deterministic Python verifier validates the reasoning against known dietary restrictions
3. **Learns from verification**: Only correct reasoning chains are rewarded during training

This means the model can't just "sound confident" - it has to actually trace through ingredients, check for hidden allergens (like koji in miso containing gluten), and verify cross-contamination risks.

## Technical Stack

**Model**: Qwen3-30B-A3B (Mixture-of-Experts, 3.3B active parameters)
- Small enough to run on-device
- Large enough to handle complex reasoning

**Training**: Group Relative Policy Optimization (GRPO)
- Memory-efficient RL (no critic network needed)
- Rewards only valid reasoning chains
- Binary safety checks: either fully correct or wrong

**Deployment Target**: iPhone 17 Pro Max
- 4-bit quantization (NF4) 
- MLX Swift framework for native performance
- Fully on-device (zero server calls, complete privacy)

## Safety Hierarchy

The verifier checks three tiers of dietary restrictions:

**Tier 0 - Fatal Allergens**: Peanuts, tree nuts, shellfish, etc.  
**Tier 1 - Medical Restrictions**: Celiac (gluten), lactose intolerance, etc.  
**Tier 2 - Religious/Ethical**: Halal, Kosher, Jain, vegan

Each tier requires different levels of reasoning about cross-contamination and hidden ingredients.

## Current Status

**Phase 1** (In Progress): Building the Verifier
- [x] Design the reward verification system
- [ ] Create test dataset of 500+ edge cases
- [ ] Baseline the reasoning quality of base model

**Phase 2** (Planned): Training
- [ ] Implement GRPO training loop
- [ ] Quantization-aware fine-tuning

**Phase 3** (Planned): Mobile Deployment  
- [ ] Port to MLX format
- [ ] Build Swift UI with reasoning transparency

## Why This Matters

Most AI safety work focuses on abstract alignment problems. This project tackles a concrete, measurable safety gap with real-world stakes. If successful, it demonstrates that:

- Small models (3B params) can outperform large models (100B+) on domain-specific safety
- Verifiable reasoning beats probabilistic confidence
- Edge deployment isn't just about privacy - it's about reliability

## References

- DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning (2025)
- Shao et al.: DeepSeekMath - Pushing the Limits of Mathematical Reasoning (2024)
- Apple MLX: Machine Learning for Apple Silicon

---

**Author**: Adit Karode  
CS @ Northeastern | Interested in NLP, RLHF, and AI Safety
