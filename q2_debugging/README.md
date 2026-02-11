# Q2: Debugging LLM Configuration

This repository contains the fixed configuration files for the broken model at `yunmorning/broken-model`.

## Problem Statement

A user reported that "inference does not work with this model" when attempting to run a `/chat/completions` API server.

**Original model:** https://huggingface.co/yunmorning/broken-model

---

## Investigation Process

### Step 1: Initial Analysis

The model card claimed the base model was `meta-llama/Llama-3.1-8B`, but the configuration files referenced `Qwen3ForCausalLM`. This raised an immediate red flag about potential architecture mismatch.

### Step 2: Verifying the Actual Architecture

To determine whether the weights were actually Llama or Qwen3, I examined the weight tensor names from the safetensors index:

```python
import requests
import json

url = "https://huggingface.co/yunmorning/broken-model/raw/main/model.safetensors.index.json"
response = requests.get(url)
index = response.json()
weight_names = list(index["weight_map"].keys())

# Check for architecture-specific layers
has_k_norm = any("k_norm" in name for name in weight_names)
has_q_norm = any("q_norm" in name for name in weight_names)
layer_count = len(set(int(n.split(".")[2]) for n in weight_names if "model.layers." in n))

print(f"Has k_norm layers: {has_k_norm}")  # True
print(f"Has q_norm layers: {has_q_norm}")  # True
print(f"Layer count: {layer_count}")        # 36
```

**Findings:**
- `k_norm` and `q_norm` layers are present in the weights
- These QK normalization layers are specific to Qwen3 architecture and do not exist in Llama
- The model has 36 layers (Llama 3.1 8B has 32 layers)

**Conclusion:** The weights are Qwen3, not Llama. The model card metadata is incorrect, but this is not a functional bug. The config architecture (`Qwen3ForCausalLM`) correctly matches the weights.

### Step 3: Identifying Configuration Bugs

I ran a comprehensive check comparing config values against the actual tokenizer:

```python
from transformers import AutoConfig, AutoTokenizer

config = AutoConfig.from_pretrained("yunmorning/broken-model")
tokenizer = AutoTokenizer.from_pretrained("yunmorning/broken-model")

print(f"Config vocab_size:     {config.vocab_size}")      # 151936
print(f"Tokenizer vocab_size:  {tokenizer.vocab_size}")   # 151643
print(f"Match: {config.vocab_size == tokenizer.vocab_size}")  # False

print(f"Config bos_token_id:   {config.bos_token_id}")    # 151643
print(f"Tokenizer bos_token:   {tokenizer.bos_token}")    # None

print(f"Has chat_template: {tokenizer.chat_template is not None}")  # False
```

**Three bugs identified:**

| Bug | Config Value | Actual Value | Impact |
|-----|-------------|--------------|--------|
| vocab_size mismatch | 151936 | 151643 | Potential embedding lookup failures |
| bos_token missing | expects 151643 | None | Improper sequence initialization |
| chat_template missing | - | False | `/chat/completions` cannot format messages |

---

## Fixes Applied

### Fix 1: config.json - vocab_size

```diff
- "vocab_size": 151936
+ "vocab_size": 151643
```

**Reason:** The config specified a vocabulary size larger than the actual tokenizer vocabulary. This mismatch could cause index-out-of-bounds errors during embedding lookup if the model attempted to generate tokens beyond the tokenizer's range.

### Fix 2: tokenizer_config.json - bos_token

```diff
- "bos_token": null,
+ "bos_token": "<|endoftext|>",
```

**Reason:** The config.json expects `bos_token_id: 151643`, which corresponds to the `<|endoftext|>` token. However, the tokenizer had `bos_token` set to null, creating a mismatch. This affects proper sequence initialization.

### Fix 3: tokenizer_config.json - chat_template

```diff
  "tokenizer_class": "Qwen2Tokenizer",
- "unk_token": null
+ "unk_token": null,
+ "chat_template": "{% for message in messages %}{{'<|im_start|>' + message['role'] + '\n' + message['content'] + '<|im_end|>' + '\n'}}{% endfor %}{% if add_generation_prompt %}{{ '<|im_start|>assistant\n' }}{% endif %}"
```

**Reason:** The `/chat/completions` API receives messages in the format:
```json
{"messages": [{"role": "user", "content": "Hello"}]}
```

Without a `chat_template`, the tokenizer cannot convert this into the model's expected format:
```
<|im_start|>user
Hello<|im_end|>
<|im_start|>assistant
```

This is the primary reason `/chat/completions` was not functional.

---

## Verification

After applying fixes, the following verification script confirms all issues are resolved:

```python
import json
from transformers import AutoTokenizer

# Load fixed configs
with open("config.json") as f:
    config = json.load(f)

with open("tokenizer_config.json") as f:
    tokenizer_config = json.load(f)

# Load tokenizer to get actual vocab size
tokenizer = AutoTokenizer.from_pretrained("yunmorning/broken-model")

# Verify fix 1: vocab_size
assert config["vocab_size"] == tokenizer.vocab_size, "vocab_size mismatch"
print(f"vocab_size: {config['vocab_size']} == {tokenizer.vocab_size} [PASS]")

# Verify fix 2: bos_token
assert tokenizer_config["bos_token"] == "<|endoftext|>", "bos_token not set"
print(f"bos_token: {tokenizer_config['bos_token']} [PASS]")

# Verify fix 3: chat_template
assert "chat_template" in tokenizer_config, "chat_template missing"
tokenizer.chat_template = tokenizer_config["chat_template"]

messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is 2+2?"}
]
formatted = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

assert "<|im_start|>system" in formatted, "chat_template not working"
assert "<|im_start|>user" in formatted, "chat_template not working"
assert "<|im_start|>assistant" in formatted, "chat_template not working"
print(f"chat_template: formats correctly [PASS]")

print("\nAll verifications passed.")
```

---

## Files Changed

| File | Status |
|------|--------|
| config.json | Modified (vocab_size) |
| tokenizer_config.json | Modified (bos_token, chat_template) |
| generation_config.json | No changes required |

---

## Commit History

1. **Initial commit:** Original broken configuration files from `yunmorning/broken-model`
2. **Fix commit:** Applied fixes for vocab_size, bos_token, and chat_template

---

## Author

Shashank V Baratwaj
