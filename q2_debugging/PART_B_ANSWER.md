# Q2 Part (b): Why `reasoning_effort` Has No Effect

## Problem Statement

The user reports that including a `reasoning_effort` parameter in requests to this model has no observable effect on the generated output.

---

## Root Cause

The `reasoning_effort` parameter is designed for **reasoning models** (like OpenAI o1, DeepSeek-R1, or Qwen QwQ) that generate internal chain-of-thought before producing a response.

While this model's tokenizer includes `<think>` and `</think>` tokens (IDs 151667 and 151668), the parameter has no effect because:

### 1. The Model Was Not Trained for Reasoning

The model is a standard Qwen3 text generation model. It was not fine-tuned on chain-of-thought datasets or trained to:
- Generate reasoning inside `<think>...</think>` blocks
- Produce internal deliberation before responding
- Vary reasoning depth based on problem complexity

The presence of `<think>` tokens in the vocabulary is inherited from the base Qwen3 tokenizer, but the model weights have no learned behavior associated with these tokens.

### 2. The Inference Server Does Not Implement Reasoning Logic

Standard inference servers (vLLM, Hugging Face TGI, etc.) do not implement `reasoning_effort` handling by default. The parameter is simply ignored because:
- There is no code to parse and interpret the parameter
- There is no token budget allocation for thinking
- There is no special decoding mode for reasoning models

### 3. No Architectural Support for Variable Reasoning

Reasoning models typically require:
- Modified generation loops that handle thinking phases
- Logic to control when to stop thinking and start responding
- Mechanisms to hide or expose thinking tokens to the user

This model uses standard autoregressive decoding with no such modifications.

---

## Requirements to Make `reasoning_effort` Functional

### Step 1: Fine-tune the Model for Reasoning

The model must be trained to actually generate reasoning:

```
Training data format:
User: What is 15 * 27?
Assistant: <think>
I need to multiply 15 by 27.
15 * 27 = 15 * (20 + 7)
= 15 * 20 + 15 * 7
= 300 + 105
= 405
</think>
The answer is 405.
```

This requires:
- Curating or generating chain-of-thought training data
- Fine-tuning the model to produce `<think>...</think>` blocks
- Training with varied reasoning depths (short/medium/long thinking)

### Step 2: Implement Inference Server Support

The inference server must be modified to:

1. **Parse the parameter**: Accept `reasoning_effort` in API requests
   ```json
   {
     "model": "qwen3",
     "messages": [...],
     "reasoning_effort": "medium"
   }
   ```

2. **Map effort to token budget**: Convert the parameter to a thinking token limit
   ```python
   EFFORT_TO_TOKENS = {
       "low": 256,
       "medium": 1024,
       "high": 4096
   }
   ```

3. **Modify generation logic**: Implement thinking-aware decoding
   ```python
   def generate_with_reasoning(prompt, max_thinking_tokens):
       # Phase 1: Generate thinking
       thinking_output = generate(
           prompt + "<think>",
           stop_tokens=["</think>"],
           max_tokens=max_thinking_tokens
       )

       # Phase 2: Generate response
       response = generate(
           prompt + "<think>" + thinking_output + "</think>",
           stop_tokens=[eos_token]
       )

       return thinking_output, response
   ```

### Step 3: Implement API Response Handling

The server should support returning or hiding the reasoning:

```json
{
  "choices": [{
    "message": {
      "role": "assistant",
      "content": "The answer is 405.",
      "reasoning": "I need to multiply 15 by 27..."
    }
  }]
}
```

### Step 4: Update Configuration Files

Add reasoning configuration to the model's config:

```json
{
  "reasoning_config": {
    "enabled": true,
    "think_start_token": "<think>",
    "think_end_token": "</think>",
    "default_effort": "medium",
    "effort_levels": {
      "low": {"max_thinking_tokens": 256},
      "medium": {"max_thinking_tokens": 1024},
      "high": {"max_thinking_tokens": 4096}
    }
  }
}
```

---

## Summary

| Requirement | Description | Effort |
|-------------|-------------|--------|
| Model fine-tuning | Train on chain-of-thought data | High |
| Server-side parameter parsing | Accept and interpret `reasoning_effort` | Medium |
| Modified decoding logic | Two-phase generation (think + respond) | Medium |
| API response format | Return reasoning separately | Low |
| Configuration updates | Define reasoning parameters | Low |

The `reasoning_effort` parameter requires changes at **both the model level** (training) and the **infrastructure level** (inference server). Simply having `<think>` tokens in the vocabulary is insufficient — the model must learn to use them, and the server must know how to control them.

---

## Author

Shashank V Baratwaj
