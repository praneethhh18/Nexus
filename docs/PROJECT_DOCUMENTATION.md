# Project Documentation has moved

The architecture & contributor guide now lives at
[`ARCHITECTURE.md`](./ARCHITECTURE.md).

For end-user docs, see [`README.md`](../README.md).
For change history, see [`CHANGELOG.md`](./CHANGELOG.md).
For contribution rules, see [`CONTRIBUTING.md`](./CONTRIBUTING.md).

> **Note for maintainers:** disable the **DocTo** VS Code extension for this
> workspace, otherwise it overwrites this file with an auto-generated dump.
> Settings → Extensions → DocTo → "Disable (Workspace)".


## Bug Fixes & Enhancements

### [New] [bugfix] Changes in __init__.py

- **File**: `venv\Lib\site-packages\tenacity\__init__.py`
- **Captured**: 4/28/2026, 1:05:29 PM
- **Category**: bugfix
**Summary:** Modified __init__.py: 751 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\tenacity\__init__.py` (+751 / -0)
**Schema: `RetryAction`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `REPR_FIELDS` | `unknown` | ✓ | - |
| `NAME` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in wrapping_geometry.py

- **File**: `venv\Lib\site-packages\sympy\physics\mechanics\wrapping_geometry.py`
- **Captured**: 4/28/2026, 1:05:27 PM
- **Category**: bugfix
**Summary:** Modified wrapping_geometry.py: 642 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\sympy\physics\mechanics\wrapping_geometry.py` (+642 / -0)
**Schema: `WrappingSphere`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Explanation` | `unknown` | ✓ | - |
| `A` | `unknown` | ✓ | - |
| `pairs` | `unknown` | ✓ | - |
| `Examples` | `unknown` | ✓ | - |
| `To` | `unknown` | ✓ | - |
| `and` | `unknown` | ✓ | - |
| `A` | `unknown` | ✓ | - |
| `WrappingSphere` | `unknown` | ✓ | - |
| `Parameters` | `unknown` | ✓ | - |
| `radius` | `Symbol` | ✓ | - |
| `point` | `Point` | ✓ | - |
| `See` | `unknown` | ✓ | - |
| `WrappingCylinder` | `Cylindrical geometry where the wrapping direction can be` | ✓ | - |

### [New] [bugfix] Changes in configuration_utils.py

- **File**: `venv\Lib\site-packages\transformers\generation\configuration_utils.py`
- **Captured**: 4/28/2026, 1:05:23 PM
- **Category**: bugfix
**Summary:** Modified configuration_utils.py: 1806 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\generation\configuration_utils.py` (+1806 / -0)
**Schema: `WatermarkingConfig`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Class` | `unknown` | ✓ | - |
| `See` | `unknown` | ✓ | - |
| `Accepts` | `unknown` | ✓ | - |

**Schema: `SynthIDTextWatermarkingConfig`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Class` | `unknown` | ✓ | - |
| `See` | `unknown` | ✓ | - |
| `Args` | `ngram_len` | ✓ | - |
| `Examples` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modeling_align.py

- **File**: `venv\Lib\site-packages\transformers\models\align\modeling_align.py`
- **Captured**: 4/28/2026, 1:05:21 PM
- **Category**: bugfix
**Summary:** Modified modeling_align.py: 1181 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\align\modeling_align.py` (+1181 / -0)
**Schema: `AlignVisionModelOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `image_embeds` | `unknown` | ✓ | - |
| `image_embeds` | `torch` | ✓ | - |
| `last_hidden_state` | `torch` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `Base` | `unknown` | ✓ | - |

**Schema: `AlignTextModelOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `text_embeds` | `unknown` | ✓ | - |
| `text_embeds` | `torch` | ✓ | - |
| `last_hidden_state` | `torch` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[torch` | ✓ | - |

**Schema: `AlignOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `loss` | `unknown` | ✓ | - |
| `logits_per_image` | `unknown` | ✓ | - |
| `logits_per_text` | `unknown` | ✓ | - |
| `text_embeds` | `unknown` | ✓ | - |
| `image_embeds` | `unknown` | ✓ | - |
| `text_model_output` | `unknown` | ✓ | - |
| `vision_model_output` | `unknown` | ✓ | - |
| `loss` | `torch` | ✓ | - |
| `logits_per_image` | `torch` | ✓ | - |
| `logits_per_text` | `torch` | ✓ | - |
| `text_embeds` | `torch` | ✓ | - |
| `image_embeds` | `torch` | ✓ | - |
| `text_model_output` | `BaseModelOutputWithPooling` | ✓ | - |
| `vision_model_output` | `BaseModelOutputWithPoolingAndNoAttention` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `caption_loss` | `unknown` | ✓ | - |
| `image_loss` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `r` | `unknown` | ✓ | - |
| `Round` | `unknown` | ✓ | - |
| `divisor` | `unknown` | ✓ | - |
| `num_channels` | `unknown` | ✓ | - |
| `new_dim` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `r` | `unknown` | ✓ | - |
| `Utility` | `unknown` | ✓ | - |
| `Args` | `kernel_size` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `correct` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `else` | `return` | ✓ | - |

**Schema: `AlignPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `AlignConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |

**Schema: `AlignTextModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `AlignTextConfig` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |

**Schema: `AlignVisionModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `AlignVisionConfig` | ✓ | - |
| `main_input_name` | `unknown` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_input_embed_layer` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modeling_olmo2.py

- **File**: `venv\Lib\site-packages\transformers\models\olmo2\modeling_olmo2.py`
- **Captured**: 4/28/2026, 1:05:19 PM
- **Category**: bugfix
**Summary:** Modified modeling_olmo2.py: 504 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\olmo2\modeling_olmo2.py` (+504 / -0)
**Schema: `Olmo2PreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Olmo2Config` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_skip_keys_device_placement` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `_supports_flex_attn` | `unknown` | ✓ | - |
| `_can_compile_fullgraph` | `unknown` | ✓ | - |
| `_supports_attention_backend` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modular_olmo2.py

- **File**: `venv\Lib\site-packages\transformers\models\olmo2\modular_olmo2.py`
- **Captured**: 4/28/2026, 1:05:17 PM
- **Category**: bugfix
**Summary:** Modified modular_olmo2.py: 231 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\olmo2\modular_olmo2.py` (+231 / -0)
**Schema: `Olmo2PreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `pass` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in iostream.py

- **File**: `venv\Lib\site-packages\tornado\iostream.py`
- **Captured**: 4/28/2026, 1:05:15 PM
- **Category**: bugfix
**Summary:** Modified iostream.py: 1618 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\tornado\iostream.py` (+1618 / -0)
**Schema: `IOStream`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `This` | `unknown` | ✓ | - |
| `plus` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `For` | `unknown` | ✓ | - |
| `socket` | `unknown` | ✓ | - |
| `connected` | `unknown` | ✓ | - |
| `A` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in asyncio.py

- **File**: `venv\Lib\site-packages\tornado\platform\asyncio.py`
- **Captured**: 4/28/2026, 1:05:13 PM
- **Category**: bugfix
**Summary:** Modified asyncio.py: 754 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\tornado\platform\asyncio.py` (+754 / -0)
**Schema: `AsyncIOMainLoop`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `current` | `unknown` | ✓ | - |

**Schema: `AsyncIOLoop`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `This` | `unknown` | ✓ | - |
| `Each` | `unknown` | ✓ | - |
| `can` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `_AnyThreadEventLoopPolicy` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `global` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in actuator.py

- **File**: `venv\Lib\site-packages\sympy\physics\mechanics\actuator.py`
- **Captured**: 4/28/2026, 1:05:11 PM
- **Category**: bugfix
**Summary:** Modified actuator.py: 1148 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\sympy\physics\mechanics\actuator.py` (+1148 / -0)
**Schema: `ForceActuator`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Explanation` | `unknown` | ✓ | - |
| `A` | `unknown` | ✓ | - |
| `its` | `unknown` | ✓ | - |
| `A` | `unknown` | ✓ | - |
| `number` | `unknown` | ✓ | - |
| `where` | `unknown` | ✓ | - |
| `points` | `unknown` | ✓ | - |
| `and` | `unknown` | ✓ | - |
| `Euclidean` | `unknown` | ✓ | - |
| `velocity` | `unknown` | ✓ | - |
| `is` | `unknown` | ✓ | - |
| `negative` | `unknown` | ✓ | - |
| `acting` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `that` | `unknown` | ✓ | - |
| `meaning` | `unknown` | ✓ | - |
| `positive` | `unknown` | ✓ | - |
| `Examples` | `unknown` | ✓ | - |
| `To` | `unknown` | ✓ | - |
| `represent` | `unknown` | ✓ | - |
| `of` | `unknown` | ✓ | - |
| `of` | `unknown` | ✓ | - |
| `can` | `unknown` | ✓ | - |
| `q` | `unknown` | ✓ | - |
| `ForceActuator` | `unknown` | ✓ | - |
| `Parameters` | `unknown` | ✓ | - |
| `force` | `Expr` | ✓ | - |
| `pathway` | `PathwayBase` | ✓ | - |

**Schema: `TorqueActuator`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Explanation` | `unknown` | ✓ | - |
| `A` | `unknown` | ✓ | - |
| `opposite` | `unknown` | ✓ | - |
| `Examples` | `unknown` | ✓ | - |
| `To` | `unknown` | ✓ | - |
| `to` | `unknown` | ✓ | - |
| `axis` | `unknown` | ✓ | - |
| `torque` | `unknown` | ✓ | - |
| `TorqueActuator` | `unknown` | ✓ | - |
| `Note` | `unknown` | ✓ | - |
| `when` | `unknown` | ✓ | - |
| `Parameters` | `unknown` | ✓ | - |
| `torque` | `Expr` | ✓ | - |
| `axis` | `Vector` | ✓ | - |
| `target_frame` | `ReferenceFrame` | ✓ | - |
| `reaction_frame` | `ReferenceFrame` | ✓ | - |

### [New] [bugfix] Changes in modeling_altclip.py

- **File**: `venv\Lib\site-packages\transformers\models\altclip\modeling_altclip.py`
- **Captured**: 4/28/2026, 1:05:08 PM
- **Category**: bugfix
**Summary:** Modified modeling_altclip.py: 1187 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\altclip\modeling_altclip.py` (+1187 / -0)
**Schema: `AltCLIPOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `loss` | `unknown` | ✓ | - |
| `logits_per_image` | `unknown` | ✓ | - |
| `logits_per_text` | `unknown` | ✓ | - |
| `text_embeds` | `unknown` | ✓ | - |
| `image_embeds` | `unknown` | ✓ | - |
| `text_model_output` | `unknown` | ✓ | - |
| `vision_model_output` | `unknown` | ✓ | - |
| `loss` | `torch` | ✓ | - |
| `logits_per_image` | `torch` | ✓ | - |
| `logits_per_text` | `torch` | ✓ | - |
| `text_embeds` | `torch` | ✓ | - |
| `image_embeds` | `torch` | ✓ | - |
| `text_model_output` | `BaseModelOutputWithPooling` | ✓ | - |
| `vision_model_output` | `BaseModelOutputWithPooling` | ✓ | - |

**Schema: `AltCLIPPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `AltCLIPConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_no_split_module` | `unknown` | ✓ | - |

**Schema: `AltCLIPVisionModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `AltCLIPVisionConfig` | ✓ | - |
| `main_input_name` | `unknown` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `all` | `unknown` | ✓ | - |
| `Kaiser` | `unknown` | ✓ | - |

**Schema: `AltRobertaModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `AltCLIPTextConfig` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |

**Schema: `AltCLIPTextModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `AltCLIPTextConfig` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modeling_olmo3.py

- **File**: `venv\Lib\site-packages\transformers\models\olmo3\modeling_olmo3.py`
- **Captured**: 4/28/2026, 1:05:04 PM
- **Category**: bugfix
**Summary:** Modified modeling_olmo3.py: 508 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\olmo3\modeling_olmo3.py` (+508 / -0)
**Schema: `Olmo3PreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Olmo3Config` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_skip_keys_device_placement` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `_supports_flex_attn` | `unknown` | ✓ | - |
| `_can_compile_fullgraph` | `unknown` | ✓ | - |
| `_supports_attention_backend` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modular_olmo3.py

- **File**: `venv\Lib\site-packages\transformers\models\olmo3\modular_olmo3.py`
- **Captured**: 4/28/2026, 1:05:03 PM
- **Category**: bugfix
**Summary:** Modified modular_olmo3.py: 246 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\olmo3\modular_olmo3.py` (+246 / -0)
**Schema: `Olmo3PreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `pass` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in streamers.py

- **File**: `venv\Lib\site-packages\transformers\generation\streamers.py`
- **Captured**: 4/28/2026, 1:05:01 PM
- **Category**: bugfix
**Summary:** Modified streamers.py: 329 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\generation\streamers.py` (+329 / -0)
**Schema: `TextStreamer`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Simple` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `Parameters` | `tokenizer` | ✓ | - |
| `Examples` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in utils.py

- **File**: `venv\Lib\site-packages\transformers\generation\utils.py`
- **Captured**: 4/28/2026, 1:04:59 PM
- **Category**: bugfix
**Summary:** Modified utils.py: 3892 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\generation\utils.py` (+3892 / -0)
**Schema: `GenerateDecoderOnlyOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Outputs` | `unknown` | ✓ | - |
| `Args` | `sequences` | ✓ | - |
| `sequences` | `torch` | ✓ | - |
| `scores` | `tuple[torch` | ✓ | - |
| `logits` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[tuple[torch` | ✓ | - |
| `hidden_states` | `tuple[tuple[torch` | ✓ | - |
| `past_key_values` | `Cache` | ✓ | - |

**Schema: `GenerateEncoderDecoderOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Outputs` | `unknown` | ✓ | - |
| `Args` | `sequences` | ✓ | - |
| `sequences` | `torch` | ✓ | - |
| `scores` | `tuple[torch` | ✓ | - |
| `logits` | `tuple[torch` | ✓ | - |
| `encoder_attentions` | `tuple[torch` | ✓ | - |
| `encoder_hidden_states` | `tuple[torch` | ✓ | - |
| `decoder_attentions` | `tuple[tuple[torch` | ✓ | - |
| `cross_attentions` | `tuple[tuple[torch` | ✓ | - |
| `decoder_hidden_states` | `tuple[tuple[torch` | ✓ | - |
| `past_key_values` | `Cache` | ✓ | - |

**Schema: `GenerateBeamDecoderOnlyOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Outputs` | `unknown` | ✓ | - |
| `Args` | `sequences` | ✓ | - |
| `sequences` | `torch` | ✓ | - |
| `sequences_scores` | `torch` | ✓ | - |
| `scores` | `tuple[torch` | ✓ | - |
| `logits` | `tuple[torch` | ✓ | - |
| `beam_indices` | `torch` | ✓ | - |
| `attentions` | `tuple[tuple[torch` | ✓ | - |
| `hidden_states` | `tuple[tuple[torch` | ✓ | - |
| `past_key_values` | `Cache` | ✓ | - |

**Schema: `GenerateBeamEncoderDecoderOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Outputs` | `unknown` | ✓ | - |
| `Args` | `sequences` | ✓ | - |
| `sequences` | `torch` | ✓ | - |
| `sequences_scores` | `torch` | ✓ | - |
| `scores` | `tuple[torch` | ✓ | - |
| `logits` | `tuple[torch` | ✓ | - |
| `beam_indices` | `torch` | ✓ | - |
| `encoder_attentions` | `tuple[torch` | ✓ | - |
| `encoder_hidden_states` | `tuple[torch` | ✓ | - |
| `decoder_attentions` | `tuple[tuple[torch` | ✓ | - |
| `cross_attentions` | `tuple[tuple[torch` | ✓ | - |
| `decoder_hidden_states` | `tuple[tuple[torch` | ✓ | - |
| `past_key_values` | `Cache` | ✓ | - |

### [New] [bugfix] Changes in watermarking.py

- **File**: `venv\Lib\site-packages\transformers\generation\watermarking.py`
- **Captured**: 4/28/2026, 1:04:57 PM
- **Category**: bugfix
**Summary:** Modified watermarking.py: 549 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\generation\watermarking.py` (+549 / -0)
**Schema: `BayesianWatermarkDetectorModelOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Base` | `unknown` | ✓ | - |
| `Args` | `loss` | ✓ | - |
| `loss` | `torch` | ✓ | - |
| `posterior_probabilities` | `torch` | ✓ | - |

**Schema: `BayesianDetectorModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `Bayesian` | `unknown` | ✓ | - |
| `This` | `unknown` | ✓ | - |
| `posterior` | `unknown` | ✓ | - |
| `BayesianScore` | `unknown` | ✓ | - |
| `Paper` | `unknown` | ✓ | - |
| `Note` | `unknown` | ✓ | - |
| `g` | `unknown` | ✓ | - |
| `This` | `unknown` | ✓ | - |
| `library` | `unknown` | ✓ | - |
| `etc` | `unknown` | ✓ | - |
| `This` | `unknown` | ✓ | - |
| `Use` | `unknown` | ✓ | - |
| `and` | `unknown` | ✓ | - |
| `Parameters` | `config` | ✓ | - |
| `config` | `BayesianDetectorConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modeling_apertus.py

- **File**: `venv\Lib\site-packages\transformers\models\apertus\modeling_apertus.py`
- **Captured**: 4/28/2026, 1:04:56 PM
- **Category**: bugfix
**Summary:** Modified modeling_apertus.py: 506 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\apertus\modeling_apertus.py` (+506 / -0)
**Schema: `ApertusPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `ApertusConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_skip_keys_device_placement` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `_supports_flex_attn` | `unknown` | ✓ | - |
| `_can_compile_fullgraph` | `unknown` | ✓ | - |
| `_supports_attention_backend` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |

**Schema: `ApertusForCausalLM`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_tied_weights_keys` | `unknown` | ✓ | - |
| `_tp_plan` | `unknown` | ✓ | - |
| `_pp_plan` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modeling_olmoe.py

- **File**: `venv\Lib\site-packages\transformers\models\olmoe\modeling_olmoe.py`
- **Captured**: 4/28/2026, 1:04:52 PM
- **Category**: bugfix
**Summary:** Modified modeling_olmoe.py: 709 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\olmoe\modeling_olmoe.py` (+709 / -0)
**Schema: `OlmoePreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `OlmoeConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_skip_keys_device_placement` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |
| `_supports_attention_backend` | `unknown` | ✓ | - |

**Schema: `OlmoeModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `gate_logits` | `torch` | ✓ | - |
| `num_experts` | `int` | ✓ | - |
| `top_k` | `unknown` | ✓ | - |
| `attention_mask` | `torch` | ✓ | - |
| `r` | `unknown` | ✓ | - |
| `Computes` | `unknown` | ✓ | - |
| `See` | `unknown` | ✓ | - |
| `function` | `unknown` | ✓ | - |
| `experts` | `unknown` | ✓ | - |
| `Args` | `gate_logits` | ✓ | - |
| `Returns` | `The auxiliary loss` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `routing_weights` | `unknown` | ✓ | - |
| `_` | `unknown` | ✓ | - |
| `expert_mask` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `else` | `batch_size, sequence_length` | ✓ | - |
| `overall_loss` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modular_olmoe.py

- **File**: `venv\Lib\site-packages\transformers\models\olmoe\modular_olmoe.py`
- **Captured**: 4/28/2026, 1:04:50 PM
- **Category**: bugfix
**Summary:** Modified modular_olmoe.py: 280 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\olmoe\modular_olmoe.py` (+280 / -0)
**Schema: `OlmoePreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `OlmoeConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_skip_keys_device_placement` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |
| `_supports_attention_backend` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modeling_arcee.py

- **File**: `venv\Lib\site-packages\transformers\models\arcee\modeling_arcee.py`
- **Captured**: 4/28/2026, 1:04:48 PM
- **Category**: bugfix
**Summary:** Modified modeling_arcee.py: 521 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\arcee\modeling_arcee.py` (+521 / -0)
**Schema: `ArceePreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `ArceeConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_skip_keys_device_placement` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `_supports_flex_attn` | `unknown` | ✓ | - |
| `_can_compile_fullgraph` | `unknown` | ✓ | - |
| `_supports_attention_backend` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |

**Schema: `ArceeForCausalLM`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_tied_weights_keys` | `unknown` | ✓ | - |
| `_tp_plan` | `unknown` | ✓ | - |
| `_pp_plan` | `unknown` | ✓ | - |

**Schema: `ArceeForSequenceClassification`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `pass` | `unknown` | ✓ | - |

**Schema: `ArceeForQuestionAnswering`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `base_model_prefix` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in hyperparameter_search.py

- **File**: `venv\Lib\site-packages\transformers\hyperparameter_search.py`
- **Captured**: 4/28/2026, 1:04:46 PM
- **Category**: bugfix
**Summary:** Modified hyperparameter_search.py: 124 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\hyperparameter_search.py` (+124 / -0)
**Schema: `OptunaBackend`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `name` | `unknown` | ✓ | - |

**Schema: `RayTuneBackend`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `name` | `unknown` | ✓ | - |
| `pip_package` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in image_processing_base.py

- **File**: `venv\Lib\site-packages\transformers\image_processing_base.py`
- **Captured**: 4/28/2026, 1:04:45 PM
- **Category**: bugfix
**Summary:** Modified image_processing_base.py: 495 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\image_processing_base.py` (+495 / -0)
**Schema: `BatchFeature`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `Holds` | `unknown` | ✓ | - |
| `This` | `unknown` | ✓ | - |
| `Args` | `data` | ✓ | - |

### [New] [bugfix] Changes in httpclient_test.py

- **File**: `venv\Lib\site-packages\tornado\test\httpclient_test.py`
- **Captured**: 4/28/2026, 1:04:41 PM
- **Category**: bugfix
**Summary:** Modified httpclient_test.py: 958 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\tornado\test\httpclient_test.py` (+958 / -0)
**API Endpoints** (`httpclient_test.py`):

| Method | Route | Handler | Middleware |
|--------|-------|---------|------------|
| `URL("COUNTDOWN", COUNT` | `countdown` | - | - |
| `URL("/HELLO", HELLOWORLDHANDLER` | `/hello` | - | - |
| `URL("/POST", POSTHANDLER` | `/post` | - | - |
| `URL("/PUT", PUTHANDLER` | `/put` | - | - |
| `URL("/REDIRECT", REDIRECTHANDLER` | `/redirect` | - | - |
| `URL("/REDIRECT_WITHOUT_LOCATION", REDIRECTWITHOUTLOCATIONHANDLER` | `/redirect_without_location` | - | - |
| `URL("/CHUNK", CHUNKHANDLER` | `/chunk` | - | auth |
| `URL("/AUTH", AUTHHANDLER` | `/auth` | - | auth |
| `URL("/COUNTDOWN/([0-9]+)", COUNTDOWNHANDLER` | `/countdown/([0-9]+)` | - | auth |
| `URL("/ECHOPOST", ECHOPOSTHANDLER` | `/echopost` | - | - |
| `URL("/USER_AGENT", USERAGENTHANDLER` | `/user_agent` | - | - |
| `URL("/304_WITH_CONTENT_LENGTH", CONTENTLENGTH304HANDLER` | `/304_with_content_length` | - | - |
| `URL("/ALL_METHODS", ALLMETHODSHANDLER` | `/all_methods` | - | - |
| `URL("/PATCH", PATCHHANDLER` | `/patch` | - | - |
| `URL("/SET_HEADER", SETHEADERHANDLER` | `/set_header` | - | - |
| `URL("/INVALID_GZIP", INVALIDGZIPHANDLER` | `/invalid_gzip` | - | - |
| `URL("/HEADER-ENCODING", HEADERENCODINGHANDLER` | `/header-encoding` | - | - |

### [New] [bugfix] Changes in simple_httpclient_test.py

- **File**: `venv\Lib\site-packages\tornado\test\simple_httpclient_test.py`
- **Captured**: 4/28/2026, 1:04:39 PM
- **Category**: bugfix
**Summary:** Modified simple_httpclient_test.py: 867 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\tornado\test\simple_httpclient_test.py` (+867 / -0)
**API Endpoints** (`simple_httpclient_test.py`):

| Method | Route | Handler | Middleware |
|--------|-------|---------|------------|
| `URL(
                    "/TRIGGER",
                    TRIGGERHANDLER` | `/trigger` | - | - |
| `URL("/CHUNK", CHUNKHANDLER` | `/chunk` | - | - |
| `URL("/COUNTDOWN/([0-9]+)", COUNTDOWNHANDLER` | `/countdown/([0-9]+)` | - | - |
| `URL("/HELLO", HELLOWORLDHANDLER` | `/hello` | - | - |
| `URL("/CONTENT_LENGTH", CONTENTLENGTHHANDLER` | `/content_length` | - | - |
| `URL("/HEAD", HEADHANDLER` | `/head` | - | - |
| `URL("/OPTIONS", OPTIONSHANDLER` | `/options` | - | - |
| `URL("/NO_CONTENT", NOCONTENTHANDLER` | `/no_content` | - | - |
| `URL("/SEE_OTHER_POST", SEEOTHERPOSTHANDLER` | `/see_other_post` | - | - |
| `URL("/SEE_OTHER_GET", SEEOTHERGETHANDLER` | `/see_other_get` | - | - |
| `URL("/HOST_ECHO", HOSTECHOHANDLER` | `/host_echo` | - | - |
| `URL("/NO_CONTENT_LENGTH", NOCONTENTLENGTHHANDLER` | `/no_content_length` | - | - |
| `URL("/ECHO_POST", ECHOPOSTHANDLER` | `/echo_post` | - | - |
| `URL("/RESPOND_IN_PREPARE", RESPONDINPREPAREHANDLER` | `/respond_in_prepare` | - | - |
| `URL("/REDIRECT", REDIRECTHANDLER` | `/redirect` | - | - |
| `URL("/USER_AGENT", USERAGENTHANDLER` | `/user_agent` | - | - |

### [New] [bugfix] Changes in sounddevice.py

- **File**: `venv\Lib\site-packages\sounddevice.py`
- **Captured**: 4/28/2026, 1:04:37 PM
- **Category**: bugfix
**Summary:** Modified sounddevice.py: 2976 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\sounddevice.py` (+2976 / -0)
**Schema: `RawInputStream`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `read` | `unknown` | ✓ | - |

**Schema: `RawOutputStream`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `write` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modeling_olmo_hybrid.py

- **File**: `venv\Lib\site-packages\transformers\models\olmo_hybrid\modeling_olmo_hybrid.py`
- **Captured**: 4/28/2026, 1:04:35 PM
- **Category**: bugfix
**Summary:** Modified modeling_olmo_hybrid.py: 1107 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\olmo_hybrid\modeling_olmo_hybrid.py` (+1107 / -0)
**Schema: `OlmoHybridPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `OlmoHybridConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_skip_keys_device_placement` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `_keys_to_ignore_on_load_unexpected` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |
| `_is_stateful` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modular_olmo_hybrid.py

- **File**: `venv\Lib\site-packages\transformers\models\olmo_hybrid\modular_olmo_hybrid.py`
- **Captured**: 4/28/2026, 1:04:33 PM
- **Category**: bugfix
**Summary:** Modified modular_olmo_hybrid.py: 788 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\olmo_hybrid\modular_olmo_hybrid.py` (+788 / -0)
**Schema: `OlmoHybridPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_is_stateful` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modeling_aria.py

- **File**: `venv\Lib\site-packages\transformers\models\aria\modeling_aria.py`
- **Captured**: 4/28/2026, 1:04:31 PM
- **Category**: bugfix
**Summary:** Modified modeling_aria.py: 1211 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\aria\modeling_aria.py` (+1211 / -0)
**Schema: `AriaTextPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `AriaTextConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_skip_keys_device_placement` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `_supports_attention_backend` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |

**Schema: `AriaPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `AriaConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_skip_keys_device_placement` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `_supports_flex_attn` | `unknown` | ✓ | - |
| `_can_compile_fullgraph` | `unknown` | ✓ | - |
| `_supports_attention_backend` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |

**Schema: `AriaTextForCausalLM`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_tied_weights_keys` | `unknown` | ✓ | - |
| `_tp_plan` | `unknown` | ✓ | - |
| `_pp_plan` | `unknown` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `Base` | `unknown` | ✓ | - |

**Schema: `AriaCausalLMOutputWithPast`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `loss` | `unknown` | ✓ | - |
| `logits` | `unknown` | ✓ | - |
| `past_key_values` | `unknown` | ✓ | - |
| `image_hidden_states` | `unknown` | ✓ | - |
| `loss` | `torch` | ✓ | - |
| `logits` | `torch` | ✓ | - |
| `past_key_values` | `Cache` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[torch` | ✓ | - |
| `image_hidden_states` | `torch` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `Base` | `unknown` | ✓ | - |

**Schema: `AriaModelOutputWithPast`** (pydantic)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `past_key_values` | `unknown` | ✓ | - |
| `image_hidden_states` | `unknown` | ✓ | - |
| `image_hidden_states` | `torch` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |

**Schema: `AriaModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `custom_intro` | `unknown` | ✓ | - |
| `Aria` | `unknown` | ✓ | - |
| `This` | `unknown` | ✓ | - |
| `to` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modular_aria.py

- **File**: `venv\Lib\site-packages\transformers\models\aria\modular_aria.py`
- **Captured**: 4/28/2026, 1:04:29 PM
- **Category**: bugfix
**Summary:** Modified modular_aria.py: 1157 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\aria\modular_aria.py` (+1157 / -0)
**Schema: `AriaTextPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `AriaTextConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_skip_keys_device_placement` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `_supports_attention_backend` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |

**Schema: `AriaPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `AriaConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `_can_compile_fullgraph` | `unknown` | ✓ | - |
| `_supports_attention_backend` | `unknown` | ✓ | - |

**Schema: `AriaTextForCausalLM`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_tied_weights_keys` | `unknown` | ✓ | - |

**Schema: `AriaModelOutputWithPast`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `pass` | `unknown` | ✓ | - |

**Schema: `AriaModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `custom_intro` | `unknown` | ✓ | - |
| `Aria` | `unknown` | ✓ | - |
| `This` | `unknown` | ✓ | - |
| `to` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in websocket_test.py

- **File**: `venv\Lib\site-packages\tornado\test\websocket_test.py`
- **Captured**: 4/28/2026, 1:04:25 PM
- **Category**: bugfix
**Summary:** Modified websocket_test.py: 990 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\tornado\test\websocket_test.py` (+990 / -0)
**Schema: `CompressionTestMixin`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `MESSAGE` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in web_test.py

- **File**: `venv\Lib\site-packages\tornado\test\web_test.py`
- **Captured**: 4/28/2026, 1:04:23 PM
- **Category**: bugfix
**Summary:** Modified web_test.py: 3418 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\tornado\test\web_test.py` (+3418 / -0)
**API Endpoints** (`web_test.py`):

| Method | Route | Handler | Middleware |
|--------|-------|---------|------------|
| `URL("/TYPECHECK/(.*)", TYPECHECKHANDLER` | `/typecheck/(.*)` | - | - |
| `URL("/DECODE_ARG/(.*)", DECODEARGHANDLER` | `/decode_arg/(.*)` | - | - |
| `URL("/DECODE_ARG_KW/(?P<ARG>.*)", DECODEARGHANDLER` | `/decode_arg_kw/(?P<arg>.*)` | - | - |
| `URL("/LINKIFY", LINKIFYHANDLER` | `/linkify` | - | - |
| `URL("/UIMODULE_RESOURCES", UIMODULERESOURCEHANDLER` | `/uimodule_resources` | - | - |
| `URL("/OPTIONAL_PATH/(.+)?", OPTIONALPATHHANDLER` | `/optional_path/(.+)?` | - | - |
| `URL("/MULTI_HEADER", MULTIHEADERHANDLER` | `/multi_header` | - | - |
| `URL("/REDIRECT", REDIRECTHANDLER` | `/redirect` | - | - |
| `URL(
                "/WEB_REDIRECT_PERMANENT",
                WEBREDIRECTHANDLER` | `/web_redirect_permanent` | - | - |
| `URL(
                "/WEB_REDIRECT",
                WEBREDIRECTHANDLER` | `/web_redirect` | - | - |
| `URL(
                "//WEB_REDIRECT_DOUBLE_SLASH",
                WEBREDIRECTHANDLER` | `//web_redirect_double_slash` | - | - |
| `URL("/HEADER_INJECTION", HEADERINJECTIONHANDLER` | `/header_injection` | - | - |
| `URL("/GET_ARGUMENT", GETARGUMENTHANDLER` | `/get_argument` | - | - |
| `URL("/GET_ARGUMENTS", GETARGUMENTSHANDLER` | `/get_arguments` | - | - |
| `URL("/SET_HEADER", SETHEADERHANDLER` | `/set_header` | - | - |
| `URL("DECODE_ARG", 42` | `decode_arg` | - | - |
| `URL("DECODE_ARG", B` | `decode_arg` | - | - |
| `URL("/DEFAULT", DEFAULTHANDLER` | `/default` | - | - |
| `URL("/WRITE_ERROR", WRITEERRORHANDLER` | `/write_error` | - | - |
| `URL("/FAILED_WRITE_ERROR", FAILEDWRITEERRORHANDLER` | `/failed_write_error` | - | - |

### [New] [bugfix] Changes in modeling_omdet_turbo.py

- **File**: `venv\Lib\site-packages\transformers\models\omdet_turbo\modeling_omdet_turbo.py`
- **Captured**: 4/28/2026, 1:04:21 PM
- **Category**: bugfix
**Summary:** Modified modeling_omdet_turbo.py: 1658 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\omdet_turbo\modeling_omdet_turbo.py` (+1658 / -0)
**Schema: `OmDetTurboEncoderOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `last_hidden_state` | `unknown` | ✓ | - |
| `extracted_states` | `unknown` | ✓ | - |
| `last_hidden_state` | `torch` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[torch` | ✓ | - |
| `extracted_states` | `tuple[torch` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `Base` | `unknown` | ✓ | - |

**Schema: `OmDetTurboDecoderOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `last_hidden_state` | `unknown` | ✓ | - |
| `decoder_coords` | `unknown` | ✓ | - |
| `encoder_coord_logits` | `unknown` | ✓ | - |
| `init_reference_points` | `unknown` | ✓ | - |
| `intermediate_reference_points` | `unknown` | ✓ | - |
| `last_hidden_state` | `torch` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[tuple[torch` | ✓ | - |
| `decoder_coords` | `torch` | ✓ | - |
| `encoder_coord_logits` | `torch` | ✓ | - |
| `init_reference_points` | `torch` | ✓ | - |
| `intermediate_reference_points` | `tuple[tuple[torch` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `Output` | `unknown` | ✓ | - |

**Schema: `OmDetTurboObjectDetectionOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `loss` | `unknown` | ✓ | - |
| `decoder_coord_logits` | `unknown` | ✓ | - |
| `init_reference_points` | `unknown` | ✓ | - |
| `intermediate_reference_points` | `unknown` | ✓ | - |
| `encoder_coord_logits` | `unknown` | ✓ | - |
| `encoder_extracted_states` | `unknown` | ✓ | - |
| `decoder_hidden_states` | `unknown` | ✓ | - |
| `decoder_attentions` | `unknown` | ✓ | - |
| `encoder_hidden_states` | `unknown` | ✓ | - |
| `encoder_attentions` | `unknown` | ✓ | - |
| `loss` | `torch` | ✓ | - |
| `decoder_coord_logits` | `torch` | ✓ | - |
| `init_reference_points` | `torch` | ✓ | - |
| `intermediate_reference_points` | `tuple[tuple[torch` | ✓ | - |
| `encoder_coord_logits` | `torch` | ✓ | - |
| `encoder_extracted_states` | `torch` | ✓ | - |
| `decoder_hidden_states` | `tuple[torch` | ✓ | - |
| `decoder_attentions` | `tuple[tuple[torch` | ✓ | - |
| `encoder_hidden_states` | `tuple[torch` | ✓ | - |
| `encoder_attentions` | `tuple[tuple[torch` | ✓ | - |

**Schema: `OmDetTurboPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `OmDetTurboConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `main_input_name` | `unknown` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `a` | `unknown` | ✓ | - |
| `b` | `unknown` | ✓ | - |
| `logit_scale` | `unknown` | ✓ | - |
| `logits_per_image` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `logit_scale` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `elif` | `unknown` | ✓ | - |
| `else` | `raise Exception` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `x` | `unknown` | ✓ | - |
| `x1` | `unknown` | ✓ | - |
| `x2` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |

**Schema: `OmDetTurboDecoder`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `custom_intro` | `unknown` | ✓ | - |
| `OmDetTurbo` | `unknown` | ✓ | - |
| `bounding` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modeling_audioflamingo3.py

- **File**: `venv\Lib\site-packages\transformers\models\audioflamingo3\modeling_audioflamingo3.py`
- **Captured**: 4/28/2026, 1:04:18 PM
- **Category**: bugfix
**Summary:** Modified modeling_audioflamingo3.py: 595 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\audioflamingo3\modeling_audioflamingo3.py` (+595 / -0)
**Schema: `AudioFlamingo3PreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `AudioFlamingo3Config` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_skip_keys_device_placement` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |

**Schema: `AudioFlamingo3Encoder`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `AudioFlamingo3` | `unknown` | ✓ | - |
| `config` | `AudioFlamingo3EncoderConfig` | ✓ | - |
| `main_input_name` | `unknown` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in base.py

- **File**: `venv\Lib\site-packages\sqlalchemy\dialects\mssql\base.py`
- **Captured**: 4/28/2026, 1:04:15 PM
- **Category**: bugfix
**Summary:** Modified base.py: 4115 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\sqlalchemy\dialects\mssql\base.py` (+4115 / -0)
**Schema: `TestTable`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `from` | `unknown` | ✓ | - |
| `INSERT` | `unknown` | ✓ | - |
| `As` | `unknown` | ✓ | - |
| `appended` | `unknown` | ✓ | - |
| `fetched` | `unknown` | ✓ | - |
| `an` | `unknown` | ✓ | - |
| `statement` | `unknown` | ✓ | - |
| `the` | `unknown` | ✓ | - |
| `is` | `unknown` | ✓ | - |
| `m` | `unknown` | ✓ | - |
| `t` | `unknown` | ✓ | - |
| `m` | `unknown` | ✓ | - |
| `with` | `unknown` | ✓ | - |
| `CREATE` | `unknown` | ✓ | - |
| `COMMIT` | `unknown` | ✓ | - |
| `INSERT` | `unknown` | ✓ | - |
| `SET` | `unknown` | ✓ | - |
| `COMMIT` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `in` | `unknown` | ✓ | - |
| `render` | `unknown` | ✓ | - |
| `first` | `unknown` | ✓ | - |
| `my_table` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `Column` | `unknown` | ✓ | - |
| `login` | `unknown` | ✓ | - |
| `select` | `unknown` | ✓ | - |
| `SELECT` | `unknown` | ✓ | - |
| `select` | `unknown` | ✓ | - |
| `SELECT` | `unknown` | ✓ | - |
| `ROW_NUMBER` | `unknown` | ✓ | - |
| `mssql_rn` | `unknown` | ✓ | - |
| `anon_1` | `unknown` | ✓ | - |
| `e` | `unknown` | ✓ | - |
| `the` | `unknown` | ✓ | - |
| `engine` | `unknown` | ✓ | - |
| `connection` | `unknown` | ✓ | - |
| `connection` | `unknown` | ✓ | - |

**Schema: `MyClass`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `driver` | `unknown` | ✓ | - |
| `versioning` | `unknown` | ✓ | - |
| `Enabling` | `unknown` | ✓ | - |
| `ALTER` | `unknown` | ✓ | - |
| `ALTER` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |

**Schema: `_MSDateTime`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `pass` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in websocket.py

- **File**: `venv\Lib\site-packages\tornado\websocket.py`
- **Captured**: 4/28/2026, 1:04:10 PM
- **Category**: bugfix
**Summary:** Modified websocket.py: 1726 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\tornado\websocket.py` (+1726 / -0)

### [New] [bugfix] Changes in modeling_oneformer.py

- **File**: `venv\Lib\site-packages\transformers\models\oneformer\modeling_oneformer.py`
- **Captured**: 4/28/2026, 1:04:08 PM
- **Category**: bugfix
**Summary:** Modified modeling_oneformer.py: 3183 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\oneformer\modeling_oneformer.py` (+3183 / -0)
**Schema: `OneFormerTransformerDecoderOutput`** (pydantic)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `object_queries` | `unknown` | ✓ | - |
| `contrastive_logits` | `unknown` | ✓ | - |
| `prediction_masks` | `unknown` | ✓ | - |
| `auxiliary_predictions` | `unknown` | ✓ | - |
| `object_queries` | `torch` | ✓ | - |
| `contrastive_logits` | `torch` | ✓ | - |
| `prediction_masks` | `torch` | ✓ | - |
| `auxiliary_predictions` | `tuple[dict[str, torch` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `OneFormer` | `unknown` | ✓ | - |
| `the` | `unknown` | ✓ | - |

**Schema: `OneFormerPixelDecoderOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `multi_scale_features` | `unknown` | ✓ | - |
| `mask_features` | `unknown` | ✓ | - |
| `attentions` | `unknown` | ✓ | - |
| `multi_scale_features` | `tuple[torch` | ✓ | - |
| `mask_features` | `torch` | ✓ | - |
| `attentions` | `tuple[torch` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `OneFormer` | `unknown` | ✓ | - |
| `Deformable` | `unknown` | ✓ | - |

**Schema: `OneFormerPixelLevelModuleOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `encoder_features` | `unknown` | ✓ | - |
| `decoder_features` | `unknown` | ✓ | - |
| `decoder_last_feature` | `unknown` | ✓ | - |
| `encoder_features` | `list[torch` | ✓ | - |
| `decoder_features` | `list[torch` | ✓ | - |
| `decoder_last_feature` | `torch` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `Class` | `unknown` | ✓ | - |

**Schema: `OneFormerModelOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `encoder_hidden_states` | `unknown` | ✓ | - |
| `pixel_decoder_hidden_states` | `unknown` | ✓ | - |
| `transformer_decoder_hidden_states` | `unknown` | ✓ | - |
| `transformer_decoder_object_queries` | `unknown` | ✓ | - |
| `transformer_decoder_contrastive_queries` | `unknown` | ✓ | - |
| `transformer_decoder_mask_predictions` | `unknown` | ✓ | - |
| `transformer_decoder_auxiliary_predictions` | `unknown` | ✓ | - |
| `text_queries` | `unknown` | ✓ | - |
| `task_token` | `unknown` | ✓ | - |
| `attentions` | `unknown` | ✓ | - |
| `encoder_hidden_states` | `tuple[torch` | ✓ | - |
| `pixel_decoder_hidden_states` | `tuple[torch` | ✓ | - |
| `transformer_decoder_hidden_states` | `torch` | ✓ | - |
| `transformer_decoder_object_queries` | `torch` | ✓ | - |
| `transformer_decoder_contrastive_queries` | `torch` | ✓ | - |
| `transformer_decoder_mask_predictions` | `torch` | ✓ | - |
| `transformer_decoder_auxiliary_predictions` | `tuple[dict[str, torch` | ✓ | - |
| `text_queries` | `torch` | ✓ | - |
| `task_token` | `torch` | ✓ | - |
| `attentions` | `tuple[torch` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `Class` | `unknown` | ✓ | - |
| `This` | `unknown` | ✓ | - |

**Schema: `OneFormerForUniversalSegmentationOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `loss` | `unknown` | ✓ | - |
| `masks_queries_logits` | `unknown` | ✓ | - |
| `auxiliary_predictions` | `unknown` | ✓ | - |
| `encoder_hidden_states` | `unknown` | ✓ | - |
| `pixel_decoder_hidden_states` | `unknown` | ✓ | - |
| `transformer_decoder_hidden_states` | `unknown` | ✓ | - |
| `transformer_decoder_object_queries` | `unknown` | ✓ | - |
| `transformer_decoder_contrastive_queries` | `unknown` | ✓ | - |
| `transformer_decoder_mask_predictions` | `unknown` | ✓ | - |
| `transformer_decoder_auxiliary_predictions` | `unknown` | ✓ | - |
| `text_queries` | `unknown` | ✓ | - |
| `task_token` | `unknown` | ✓ | - |
| `attentions` | `unknown` | ✓ | - |
| `loss` | `torch` | ✓ | - |
| `masks_queries_logits` | `torch` | ✓ | - |
| `auxiliary_predictions` | `list[dict[str, torch` | ✓ | - |
| `encoder_hidden_states` | `tuple[torch` | ✓ | - |
| `pixel_decoder_hidden_states` | `list[torch` | ✓ | - |
| `transformer_decoder_hidden_states` | `torch` | ✓ | - |
| `transformer_decoder_object_queries` | `torch` | ✓ | - |
| `transformer_decoder_contrastive_queries` | `torch` | ✓ | - |
| `transformer_decoder_mask_predictions` | `torch` | ✓ | - |
| `transformer_decoder_auxiliary_predictions` | `list[dict[str, torch` | ✓ | - |
| `text_queries` | `torch` | ✓ | - |
| `task_token` | `torch` | ✓ | - |
| `attentions` | `tuple[tuple[torch` | ✓ | - |

**Schema: `OneFormerPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `OneFormerConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `main_input_name` | `unknown` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |

**Schema: `OneFormerModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `main_input_name` | `unknown` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `OneFormer` | `unknown` | ✓ | - |

### [New] [enhancement] Changes in server.py

- **File**: `venv\Lib\site-packages\transformers\cli\serving\server.py`
- **Captured**: 4/28/2026, 1:04:05 PM
- **Category**: enhancement
**Summary:** Modified server.py: 128 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\cli\serving\server.py` (+128 / -0)
**API Endpoints** (`server.py`):

| Method | Route | Handler | Middleware |
|--------|-------|---------|------------|
| `POST` | `/v1/chat/completions` | post | - |
| `POST` | `/v1/responses` | post | - |
| `POST` | `/v1/audio/transcriptions` | post | - |
| `POST` | `/load_model` | post | - |
| `POST` | `/reset` | post | - |
| `GET` | `/v1/models` | get | - |
| `OPTIONS` | `/v1/models` | options | - |
| `GET` | `/health` | get | - |

### [New] [bugfix] Changes in transcription.py

- **File**: `venv\Lib\site-packages\transformers\cli\serving\transcription.py`
- **Captured**: 4/28/2026, 1:04:04 PM
- **Category**: bugfix
**Summary:** Modified transcription.py: 186 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\cli\serving\transcription.py` (+186 / -0)
**Schema: `TransformersTranscriptionCreateParams`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `stream` | `bool` | ✓ | - |

### [New] [bugfix] Changes in utils.py

- **File**: `venv\Lib\site-packages\transformers\cli\serving\utils.py`
- **Captured**: 4/28/2026, 1:04:02 PM
- **Category**: bugfix
**Summary:** Modified utils.py: 957 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\cli\serving\utils.py` (+957 / -0)
**Schema: `GenerateManager`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `async` | `unknown` | ✓ | - |

**Schema: `CBGenerateManager`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Translates` | `unknown` | ✓ | - |
| `token` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `sampling` | `unknown` | ✓ | - |
| `async` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in plot_curve.py

- **File**: `venv\Lib\site-packages\sympy\plotting\pygletplot\plot_curve.py`
- **Captured**: 4/28/2026, 1:04:00 PM
- **Category**: bugfix
**Summary:** Modified plot_curve.py: 83 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\sympy\plotting\pygletplot\plot_curve.py` (+83 / -0)
**Schema: `PlotCurve`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `style_override` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in base.py

- **File**: `venv\Lib\site-packages\sqlalchemy\dialects\mysql\base.py`
- **Captured**: 4/28/2026, 1:03:58 PM
- **Category**: bugfix
**Summary:** Modified base.py: 3950 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\sqlalchemy\dialects\mysql\base.py` (+3950 / -0)
**Schema: `MyClass`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `mysql` | `unknown` | ✓ | - |
| `Query` | `unknown` | ✓ | - |
| `mysql` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `m` | `unknown` | ✓ | - |
| `t` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `e` | `unknown` | ✓ | - |
| `m` | `unknown` | ✓ | - |
| `CREATE` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `SET_RE` | `unknown` | ✓ | - |
| `r` | `unknown` | ✓ | - |
| `_IntegerType` | `_IntegerType,` | ✓ | - |
| `_NumericType` | `_NumericType,` | ✓ | - |
| `_FloatType` | `_FloatType,` | ✓ | - |
| `sqltypes` | `unknown` | ✓ | - |
| `sqltypes` | `unknown` | ✓ | - |
| `sqltypes` | `unknown` | ✓ | - |
| `sqltypes` | `unknown` | ✓ | - |
| `sqltypes` | `unknown` | ✓ | - |
| `sqltypes` | `unknown` | ✓ | - |
| `sqltypes` | `unknown` | ✓ | - |
| `sqltypes` | `unknown` | ✓ | - |
| `sqltypes` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in data_collator.py

- **File**: `venv\Lib\site-packages\transformers\data\data_collator.py`
- **Captured**: 4/28/2026, 1:03:55 PM
- **Category**: bugfix
**Summary:** Modified data_collator.py: 1463 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\data\data_collator.py` (+1463 / -0)
**Schema: `DataCollatorForWholeWordMask`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Data` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `elif` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `elif` | `unknown` | ✓ | - |
| `else` | `return np` | ✓ | - |

**Schema: `DataCollatorForSOP`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Data` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in repmatrix.py

- **File**: `venv\Lib\site-packages\sympy\matrices\repmatrix.py`
- **Captured**: 4/28/2026, 1:03:53 PM
- **Category**: bugfix
**Summary:** Modified repmatrix.py: 1035 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\sympy\matrices\repmatrix.py` (+1035 / -0)
**Schema: `RepMatrix`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `The` | `unknown` | ✓ | - |
| `SparseMatrix` | `unknown` | ✓ | - |
| `DomainMatrix` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modeling_openai.py

- **File**: `venv\Lib\site-packages\transformers\models\openai\modeling_openai.py`
- **Captured**: 4/28/2026, 1:03:47 PM
- **Category**: bugfix
**Summary:** Modified modeling_openai.py: 729 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\openai\modeling_openai.py` (+729 / -0)
**Schema: `OpenAIGPTPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `OpenAIGPTConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `Base` | `unknown` | ✓ | - |

**Schema: `OpenAIGPTDoubleHeadsModelOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `loss` | `unknown` | ✓ | - |
| `mc_loss` | `unknown` | ✓ | - |
| `logits` | `unknown` | ✓ | - |
| `mc_logits` | `unknown` | ✓ | - |
| `loss` | `torch` | ✓ | - |
| `mc_loss` | `torch` | ✓ | - |
| `logits` | `torch` | ✓ | - |
| `mc_logits` | `torch` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[torch` | ✓ | - |

**Schema: `OpenAIGPTModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `custom_intro` | `unknown` | ✓ | - |
| `OpenAI` | `unknown` | ✓ | - |
| `embeddings` | `unknown` | ✓ | - |

**Schema: `OpenAIGPTLMHeadModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_tied_weights_keys` | `unknown` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `RocStories` | `unknown` | ✓ | - |
| `input` | `unknown` | ✓ | - |
| `input` | `unknown` | ✓ | - |

**Schema: `OpenAIGPTDoubleHeadsModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_tied_weights_keys` | `unknown` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `models` | `unknown` | ✓ | - |
| `last` | `unknown` | ✓ | - |
| `token` | `unknown` | ✓ | - |
| `it` | `unknown` | ✓ | - |
| `the` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modeling_opt.py

- **File**: `venv\Lib\site-packages\transformers\models\opt\modeling_opt.py`
- **Captured**: 4/28/2026, 1:03:43 PM
- **Category**: bugfix
**Summary:** Modified modeling_opt.py: 752 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\opt\modeling_opt.py` (+752 / -0)
**Schema: `OPTPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `OPTConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_supports_attention_backend` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `_supports_flex_attn` | `unknown` | ✓ | - |
| `_can_compile_fullgraph` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |

**Schema: `OPTDecoder`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Transformer` | `unknown` | ✓ | - |
| `Args` | `config` | ✓ | - |

**Schema: `OPTForCausalLM`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_tied_weights_keys` | `unknown` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `Since` | `unknown` | ✓ | - |
| `no` | `unknown` | ✓ | - |
| `padding` | `unknown` | ✓ | - |
| `each` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in series.py

- **File**: `venv\Lib\site-packages\sympy\plotting\series.py`
- **Captured**: 4/28/2026, 1:03:40 PM
- **Category**: bugfix
**Summary:** Modified series.py: 2592 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\sympy\plotting\series.py` (+2592 / -0)
**Schema: `Line2DBaseSeries`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `is_2Dline` | `unknown` | ✓ | - |
| `_dim` | `unknown` | ✓ | - |
| `_N` | `unknown` | ✓ | - |

**Schema: `ParametricLineBaseSeries`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `is_parametric` | `unknown` | ✓ | - |

**Schema: `Parametric2DLineSeries`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `over` | `unknown` | ✓ | - |
| `is_2Dline` | `unknown` | ✓ | - |

**Schema: `Line3DBaseSeries`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Most` | `unknown` | ✓ | - |
| `is_2Dline` | `unknown` | ✓ | - |
| `is_3Dline` | `unknown` | ✓ | - |
| `_dim` | `unknown` | ✓ | - |

**Schema: `Parametric3DLineSeries`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `expressions` | `unknown` | ✓ | - |
| `is_2Dline` | `unknown` | ✓ | - |
| `is_3Dline` | `unknown` | ✓ | - |

**Schema: `SurfaceBaseSeries`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `is_3Dsurface` | `unknown` | ✓ | - |

**Schema: `SurfaceOver2DRangeSeries`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `range` | `unknown` | ✓ | - |

**Schema: `ParametricSurfaceSeries`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `expressions` | `unknown` | ✓ | - |
| `is_parametric` | `unknown` | ✓ | - |

**Schema: `GenericDataSeries`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Notes` | `unknown` | ✓ | - |
| `This` | `unknown` | ✓ | - |
| `annotations` | `unknown` | ✓ | - |
| `user` | `unknown` | ✓ | - |
| `combining` | `unknown` | ✓ | - |
| `consideration` | `unknown` | ✓ | - |
| `Also` | `unknown` | ✓ | - |
| `keyword` | `unknown` | ✓ | - |
| `requires` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `numerical` | `unknown` | ✓ | - |
| `plots` | `unknown` | ✓ | - |
| `libraries` | `unknown` | ✓ | - |
| `Instead` | `unknown` | ✓ | - |
| `in` | `unknown` | ✓ | - |
| `created` | `unknown` | ✓ | - |
| `Becomes` | `unknown` | ✓ | - |
| `Which` | `unknown` | ✓ | - |
| `full` | `unknown` | ✓ | - |
| `is_generic` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modeling_ovis2.py

- **File**: `venv\Lib\site-packages\transformers\models\ovis2\modeling_ovis2.py`
- **Captured**: 4/28/2026, 1:03:37 PM
- **Category**: bugfix
**Summary:** Modified modeling_ovis2.py: 743 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\ovis2\modeling_ovis2.py` (+743 / -0)
**Schema: `BaseModelOutputWithVisualIndicatorFeatures`** (pydantic)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `visual_indicator_features` | `unknown` | ✓ | - |
| `visual_indicator_features` | `torch` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `Base` | `unknown` | ✓ | - |

**Schema: `Ovis2ModelOutputWithPast`** (pydantic)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `past_key_values` | `unknown` | ✓ | - |
| `image_hidden_states` | `unknown` | ✓ | - |
| `image_hidden_states` | `torch` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `Base` | `unknown` | ✓ | - |

**Schema: `Ovis2CausalLMOutputWithPast`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `loss` | `unknown` | ✓ | - |
| `logits` | `unknown` | ✓ | - |
| `past_key_values` | `unknown` | ✓ | - |
| `image_hidden_states` | `unknown` | ✓ | - |
| `loss` | `torch` | ✓ | - |
| `logits` | `torch` | ✓ | - |
| `past_key_values` | `Cache` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[torch` | ✓ | - |
| `image_hidden_states` | `torch` | ✓ | - |

**Schema: `Ovis2PreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Ovis2Config` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_skip_keys_device_placement` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_supports_flex_attn` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `_can_compile_fullgraph` | `unknown` | ✓ | - |
| `_supports_attention_backend` | `unknown` | ✓ | - |
| `y_soft` | `unknown` | ✓ | - |
| `index` | `unknown` | ✓ | - |
| `y_hard` | `unknown` | ✓ | - |
| `ret` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |

**Schema: `Ovis2VisionModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Ovis2VisionConfig` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modular_ovis2.py

- **File**: `venv\Lib\site-packages\transformers\models\ovis2\modular_ovis2.py`
- **Captured**: 4/28/2026, 1:03:35 PM
- **Category**: bugfix
**Summary:** Modified modular_ovis2.py: 449 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\ovis2\modular_ovis2.py` (+449 / -0)
**Schema: `BaseModelOutputWithVisualIndicatorFeatures`** (pydantic)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `visual_indicator_features` | `unknown` | ✓ | - |
| `visual_indicator_features` | `torch` | ✓ | - |

**Schema: `Ovis2ModelOutputWithPast`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `pass` | `unknown` | ✓ | - |

**Schema: `Ovis2PreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Ovis2Config` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_skip_keys_device_placement` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_supports_flex_attn` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `_can_compile_fullgraph` | `unknown` | ✓ | - |
| `_supports_attention_backend` | `unknown` | ✓ | - |

**Schema: `Ovis2VisionModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Ovis2VisionConfig` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in hstore.py

- **File**: `venv\Lib\site-packages\sqlalchemy\dialects\postgresql\hstore.py`
- **Captured**: 4/28/2026, 1:03:33 PM
- **Category**: bugfix
**Summary:** Modified hstore.py: 407 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\sqlalchemy\dialects\postgresql\hstore.py` (+407 / -0)
**Schema: `MyClass`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `hashable` | `unknown` | ✓ | - |
| `text_type` | `unknown` | ✓ | - |
| `comparator_factory` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in named_types.py

- **File**: `venv\Lib\site-packages\sqlalchemy\dialects\postgresql\named_types.py`
- **Captured**: 4/28/2026, 1:03:31 PM
- **Category**: bugfix
**Summary:** Modified named_types.py: 525 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\sqlalchemy\dialects\postgresql\named_types.py` (+525 / -0)
**Schema: `NamedType`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `DDLGenerator` | `Type[NamedTypeGenerator]` | ✓ | - |
| `DDLDropper` | `Type[NamedTypeDropper]` | ✓ | - |
| `create_type` | `bool` | ✓ | - |

**Schema: `DOMAIN`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `A` | `unknown` | ✓ | - |
| `that` | `unknown` | ✓ | - |
| `See` | `unknown` | ✓ | - |
| `DDLGenerator` | `unknown` | ✓ | - |
| `DDLDropper` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in session.py

- **File**: `venv\Lib\site-packages\sqlalchemy\ext\asyncio\session.py`
- **Captured**: 4/28/2026, 1:03:24 PM
- **Category**: bugfix
**Summary:** Modified session.py: 1948 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\sqlalchemy\ext\asyncio\session.py` (+1948 / -0)
**Schema: `Base`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `In` | `unknown` | ✓ | - |
| `the` | `unknown` | ✓ | - |
| `This` | `unknown` | ✓ | - |
| `yield` | `unknown` | ✓ | - |
| `which` | `unknown` | ✓ | - |
| `accessed` | `unknown` | ✓ | - |
| `The` | `attr` | ✓ | - |
| `attribute` | `unknown` | ✓ | - |
| `Session` | `unknown` | ✓ | - |
| `methods` | `unknown` | ✓ | - |
| `attributes` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modeling_owlv2.py

- **File**: `venv\Lib\site-packages\transformers\models\owlv2\modeling_owlv2.py`
- **Captured**: 4/28/2026, 1:03:21 PM
- **Category**: bugfix
**Summary:** Modified modeling_owlv2.py: 1555 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\owlv2\modeling_owlv2.py` (+1555 / -0)
**Schema: `Owlv2Output`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `loss` | `unknown` | ✓ | - |
| `logits_per_image` | `unknown` | ✓ | - |
| `logits_per_text` | `unknown` | ✓ | - |
| `text_embeds` | `unknown` | ✓ | - |
| `image_embeds` | `unknown` | ✓ | - |
| `text_model_output` | `unknown` | ✓ | - |
| `vision_model_output` | `unknown` | ✓ | - |
| `loss` | `torch` | ✓ | - |
| `logits_per_image` | `torch` | ✓ | - |
| `logits_per_text` | `torch` | ✓ | - |
| `text_embeds` | `torch` | ✓ | - |
| `image_embeds` | `torch` | ✓ | - |
| `text_model_output` | `BaseModelOutputWithPooling` | ✓ | - |
| `vision_model_output` | `BaseModelOutputWithPooling` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `else` | `return t if t` | ✓ | - |
| `Computes` | `unknown` | ✓ | - |
| `Args` | `boxes` | ✓ | - |
| `Returns` | `unknown` | ✓ | - |
| `boxes` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `area1` | `unknown` | ✓ | - |
| `area2` | `unknown` | ✓ | - |
| `left_top` | `unknown` | ✓ | - |
| `right_bottom` | `unknown` | ✓ | - |
| `width_height` | `unknown` | ✓ | - |
| `inter` | `unknown` | ✓ | - |
| `union` | `unknown` | ✓ | - |
| `iou` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `Generalized` | `unknown` | ✓ | - |
| `Returns` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `iou` | `unknown` | ✓ | - |
| `top_left` | `unknown` | ✓ | - |
| `bottom_right` | `unknown` | ✓ | - |
| `width_height` | `unknown` | ✓ | - |
| `area` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `Output` | `unknown` | ✓ | - |

**Schema: `Owlv2ObjectDetectionOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `loss` | `unknown` | ✓ | - |
| `loss_dict` | `unknown` | ✓ | - |
| `logits` | `unknown` | ✓ | - |
| `objectness_logits` | `unknown` | ✓ | - |
| `pred_boxes` | `unknown` | ✓ | - |
| `text_embeds` | `unknown` | ✓ | - |
| `image_embeds` | `unknown` | ✓ | - |
| `text_model_output` | `unknown` | ✓ | - |
| `vision_model_output` | `unknown` | ✓ | - |
| `loss` | `torch` | ✓ | - |
| `loss_dict` | `dict` | ✓ | - |
| `logits` | `torch` | ✓ | - |
| `objectness_logits` | `torch` | ✓ | - |
| `pred_boxes` | `torch` | ✓ | - |
| `text_embeds` | `torch` | ✓ | - |
| `image_embeds` | `torch` | ✓ | - |
| `text_model_output` | `BaseModelOutputWithPooling` | ✓ | - |
| `vision_model_output` | `BaseModelOutputWithPooling` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `Output` | `unknown` | ✓ | - |

**Schema: `Owlv2ImageGuidedObjectDetectionOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `logits` | `unknown` | ✓ | - |
| `image_embeds` | `unknown` | ✓ | - |
| `query_image_embeds` | `unknown` | ✓ | - |
| `target_pred_boxes` | `unknown` | ✓ | - |
| `query_pred_boxes` | `unknown` | ✓ | - |
| `text_model_output` | `unknown` | ✓ | - |
| `vision_model_output` | `unknown` | ✓ | - |
| `logits` | `torch` | ✓ | - |
| `image_embeds` | `torch` | ✓ | - |
| `query_image_embeds` | `torch` | ✓ | - |
| `target_pred_boxes` | `torch` | ✓ | - |
| `query_pred_boxes` | `torch` | ✓ | - |
| `text_model_output` | `BaseModelOutputWithPooling` | ✓ | - |
| `vision_model_output` | `BaseModelOutputWithPooling` | ✓ | - |

**Schema: `Owlv2PreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Owlv2Config` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_supports_flex_attn` | `unknown` | ✓ | - |
| `_supports_attention_backend` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |
| `_keys_to_ignore_on_load_unexpected` | `unknown` | ✓ | - |

**Schema: `Owlv2TextModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Owlv2TextConfig` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |

**Schema: `Owlv2VisionModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Owlv2VisionConfig` | ✓ | - |
| `main_input_name` | `unknown` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |

**Schema: `Owlv2Model`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Owlv2Config` | ✓ | - |

### [New] [bugfix] Changes in logic.py

- **File**: `venv\Lib\site-packages\sympy\core\logic.py`
- **Captured**: 4/28/2026, 1:03:15 PM
- **Category**: bugfix
**Summary:** Modified logic.py: 426 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\sympy\core\logic.py` (+426 / -0)
**Schema: `And`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `op_x_notx` | `unknown` | ✓ | - |

**Schema: `Or`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `op_x_notx` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modeling_owlvit.py

- **File**: `venv\Lib\site-packages\transformers\models\owlvit\modeling_owlvit.py`
- **Captured**: 4/28/2026, 1:03:11 PM
- **Category**: bugfix
**Summary:** Modified modeling_owlvit.py: 1493 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\owlvit\modeling_owlvit.py` (+1493 / -0)
**Schema: `OwlViTOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `loss` | `unknown` | ✓ | - |
| `logits_per_image` | `unknown` | ✓ | - |
| `logits_per_text` | `unknown` | ✓ | - |
| `text_embeds` | `unknown` | ✓ | - |
| `image_embeds` | `unknown` | ✓ | - |
| `text_model_output` | `unknown` | ✓ | - |
| `vision_model_output` | `unknown` | ✓ | - |
| `loss` | `torch` | ✓ | - |
| `logits_per_image` | `torch` | ✓ | - |
| `logits_per_text` | `torch` | ✓ | - |
| `text_embeds` | `torch` | ✓ | - |
| `image_embeds` | `torch` | ✓ | - |
| `text_model_output` | `BaseModelOutputWithPooling` | ✓ | - |
| `vision_model_output` | `BaseModelOutputWithPooling` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `else` | `return t if t` | ✓ | - |
| `Computes` | `unknown` | ✓ | - |
| `Args` | `boxes` | ✓ | - |
| `Returns` | `unknown` | ✓ | - |
| `boxes` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `area1` | `unknown` | ✓ | - |
| `area2` | `unknown` | ✓ | - |
| `left_top` | `unknown` | ✓ | - |
| `right_bottom` | `unknown` | ✓ | - |
| `width_height` | `unknown` | ✓ | - |
| `inter` | `unknown` | ✓ | - |
| `union` | `unknown` | ✓ | - |
| `iou` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `Generalized` | `unknown` | ✓ | - |
| `Returns` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `iou` | `unknown` | ✓ | - |
| `top_left` | `unknown` | ✓ | - |
| `bottom_right` | `unknown` | ✓ | - |
| `width_height` | `unknown` | ✓ | - |
| `area` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `Output` | `unknown` | ✓ | - |

**Schema: `OwlViTObjectDetectionOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `loss` | `unknown` | ✓ | - |
| `loss_dict` | `unknown` | ✓ | - |
| `logits` | `unknown` | ✓ | - |
| `pred_boxes` | `unknown` | ✓ | - |
| `text_embeds` | `unknown` | ✓ | - |
| `image_embeds` | `unknown` | ✓ | - |
| `text_model_output` | `unknown` | ✓ | - |
| `vision_model_output` | `unknown` | ✓ | - |
| `loss` | `torch` | ✓ | - |
| `loss_dict` | `dict` | ✓ | - |
| `logits` | `torch` | ✓ | - |
| `pred_boxes` | `torch` | ✓ | - |
| `text_embeds` | `torch` | ✓ | - |
| `image_embeds` | `torch` | ✓ | - |
| `text_model_output` | `BaseModelOutputWithPooling` | ✓ | - |
| `vision_model_output` | `BaseModelOutputWithPooling` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `Output` | `unknown` | ✓ | - |

**Schema: `OwlViTImageGuidedObjectDetectionOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `logits` | `unknown` | ✓ | - |
| `image_embeds` | `unknown` | ✓ | - |
| `query_image_embeds` | `unknown` | ✓ | - |
| `target_pred_boxes` | `unknown` | ✓ | - |
| `query_pred_boxes` | `unknown` | ✓ | - |
| `text_model_output` | `unknown` | ✓ | - |
| `vision_model_output` | `unknown` | ✓ | - |
| `logits` | `torch` | ✓ | - |
| `image_embeds` | `torch` | ✓ | - |
| `query_image_embeds` | `torch` | ✓ | - |
| `target_pred_boxes` | `torch` | ✓ | - |
| `query_pred_boxes` | `torch` | ✓ | - |
| `text_model_output` | `BaseModelOutputWithPooling` | ✓ | - |
| `vision_model_output` | `BaseModelOutputWithPooling` | ✓ | - |

**Schema: `OwlViTPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `OwlViTConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_supports_flex_attn` | `unknown` | ✓ | - |
| `_supports_attention_backend` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |
| `_keys_to_ignore_on_load_unexpected` | `unknown` | ✓ | - |

**Schema: `OwlViTTextModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `OwlViTTextConfig` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |

**Schema: `OwlViTVisionModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `OwlViTVisionConfig` | ✓ | - |
| `main_input_name` | `unknown` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |

**Schema: `OwlViTModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `OwlViTConfig` | ✓ | - |

### [New] [bugfix] Changes in compiler.py

- **File**: `venv\Lib\site-packages\sqlalchemy\sql\compiler.py`
- **Captured**: 4/28/2026, 1:03:09 PM
- **Category**: bugfix
**Summary:** Modified compiler.py: 8084 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\sqlalchemy\sql\compiler.py` (+8084 / -0)
**Schema: `_CompilerStackEntry`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `compile_state` | `CompileState` | ✓ | - |
| `need_result_map_for_nested` | `bool` | ✓ | - |
| `need_result_map_for_compound` | `bool` | ✓ | - |
| `select_0` | `ReturnsRows` | ✓ | - |
| `insert_from_select` | `Select[Any]` | ✓ | - |

### [New] [bugfix] Changes in ddl.py

- **File**: `venv\Lib\site-packages\sqlalchemy\sql\ddl.py`
- **Captured**: 4/28/2026, 1:03:06 PM
- **Category**: bugfix
**Summary:** Modified ddl.py: 1445 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\sqlalchemy\sql\ddl.py` (+1445 / -0)
**Schema: `ExecutableDDLElement`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `This` | `unknown` | ✓ | - |
| `as` | `unknown` | ✓ | - |
| `etc` | `unknown` | ✓ | - |
| `introduced` | `unknown` | ✓ | - |
| `itself` | `unknown` | ✓ | - |
| `_ddl_if` | `Optional[DDLIf]` | ✓ | - |
| `target` | `Union[SchemaItem, str, None]` | ✓ | - |
| `DDLElement` | `unknown` | ✓ | - |

**Schema: `CreateSchema`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `The` | `unknown` | ✓ | - |
| `stringify_dialect` | `unknown` | ✓ | - |

**Schema: `DropSchema`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `The` | `unknown` | ✓ | - |
| `stringify_dialect` | `unknown` | ✓ | - |

**Schema: `_DropView`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Used` | `unknown` | ✓ | - |
| `This` | `unknown` | ✓ | - |

**Schema: `CreateConstraint`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `element` | `Constraint` | ✓ | - |

**Schema: `CreateColumn`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `as` | `unknown` | ✓ | - |
| `via` | `unknown` | ✓ | - |
| `This` | `unknown` | ✓ | - |
| `of` | `unknown` | ✓ | - |
| `compiler` | `unknown` | ✓ | - |
| `to` | `unknown` | ✓ | - |
| `Typical` | `unknown` | ✓ | - |
| `object` | `unknown` | ✓ | - |
| `is` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `as` | `unknown` | ✓ | - |
| `Above` | `unknown` | ✓ | - |
| `collection` | `unknown` | ✓ | - |
| `The` | `class` | ✓ | - |
| `columns` | `unknown` | ✓ | - |
| `creating` | `unknown` | ✓ | - |
| `This` | `unknown` | ✓ | - |
| `as` | `unknown` | ✓ | - |
| `For` | `unknown` | ✓ | - |
| `which` | `unknown` | ✓ | - |
| `rendering` | `unknown` | ✓ | - |
| `backend` | `unknown` | ✓ | - |
| `triggered` | `unknown` | ✓ | - |
| `on` | `unknown` | ✓ | - |
| `Above` | `unknown` | ✓ | - |
| `which` | `unknown` | ✓ | - |
| `will` | `unknown` | ✓ | - |
| `element` | `Column[Any]` | ✓ | - |

**Schema: `DropTableComment`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Note` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in dml.py

- **File**: `venv\Lib\site-packages\sqlalchemy\sql\dml.py`
- **Captured**: 4/28/2026, 1:03:04 PM
- **Category**: bugfix
**Summary:** Modified dml.py: 1854 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\sqlalchemy\sql\dml.py` (+1854 / -0)
**Schema: `ValuesBase`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `INSERT` | `unknown` | ✓ | - |
| `_supports_multi_parameters` | `unknown` | ✓ | - |
| `select` | `Optional[Select[Any]]` | ✓ | - |
| `_post_values_clause` | `Optional[ClauseElement]` | ✓ | - |
| `constructs` | `unknown` | ✓ | - |
| `_values` | `Optional[util` | ✓ | - |
| `_multi_values` | `Tuple[` | ✓ | - |
| `_ordered_values` | `Optional[List[Tuple[_DMLColumnElement, Any]]]` | ✓ | - |
| `_select_names` | `Optional[List[str]]` | ✓ | - |
| `_inline` | `bool` | ✓ | - |

**Schema: `Insert`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `The` | `class` | ✓ | - |
| `_supports_multi_parameters` | `unknown` | ✓ | - |
| `select` | `unknown` | ✓ | - |
| `_sort_by_parameter_order` | `bool` | ✓ | - |
| `is_insert` | `unknown` | ✓ | - |
| `table` | `TableClause` | ✓ | - |
| `_traverse_internals` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |

**Schema: `Update`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `The` | `class` | ✓ | - |
| `is_update` | `unknown` | ✓ | - |
| `_traverse_internals` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |

**Schema: `Delete`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `The` | `class` | ✓ | - |
| `is_delete` | `unknown` | ✓ | - |
| `_traverse_internals` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in schema.py

- **File**: `venv\Lib\site-packages\sqlalchemy\sql\schema.py`
- **Captured**: 4/28/2026, 1:03:01 PM
- **Category**: bugfix
**Summary:** Modified schema.py: 6226 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\sqlalchemy\sql\schema.py` (+6226 / -0)
**Schema: `SchemaItem`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `create_drop_stringify_dialect` | `unknown` | ✓ | - |
| `_use_schema_map` | `unknown` | ✓ | - |

**Schema: `HasSchemaAttr`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `schema` | `Optional[str]` | ✓ | - |

**Schema: `Table`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `e` | `unknown` | ✓ | - |
| `The` | `class` | ✓ | - |
| `object` | `unknown` | ✓ | - |
| `on` | `unknown` | ✓ | - |
| `constructor` | `unknown` | ✓ | - |
| `a` | `unknown` | ✓ | - |
| `object` | `unknown` | ✓ | - |
| `the` | `class` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `_columns` | `DedupeColumnCollection[Column[Any]]` | ✓ | - |
| `_sentinel_column` | `Optional[Column[Any]]` | ✓ | - |
| `constraints` | `Set[Constraint]` | ✓ | - |
| `indexes` | `Set[Index]` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |

**Schema: `Column`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `inherit_cache` | `unknown` | ✓ | - |
| `key` | `str` | ✓ | - |
| `table` | `Table` | ✓ | - |
| `constraints` | `Set[Constraint]` | ✓ | - |
| `foreign_keys` | `Set[ForeignKey]` | ✓ | - |
| `index` | `Optional[bool]` | ✓ | - |
| `unique` | `Optional[bool]` | ✓ | - |
| `computed` | `Optional[Computed]` | ✓ | - |
| `identity` | `Optional[Identity]` | ✓ | - |
| `name` | `Optional[str]` | ✓ | - |
| `type_` | `Optional[_TypeEngineArgument[_T]]` | ✓ | - |
| `omit_from_statements` | `bool` | ✓ | - |
| `dedicated` | `unknown` | ✓ | - |
| `inserts` | `unknown` | ✓ | - |
| `don` | `unknown` | ✓ | - |
| `Adding` | `unknown` | ✓ | - |
| `corresponding` | `unknown` | ✓ | - |
| `it` | `unknown` | ✓ | - |
| `For` | `unknown` | ✓ | - |
| `section` | `ref` | ✓ | - |
| `The` | `class` | ✓ | - |
| `return` | `unknown` | ✓ | - |

**Schema: `ForeignKey`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `object` | `unknown` | ✓ | - |
| `e` | `unknown` | ✓ | - |
| `Note` | `unknown` | ✓ | - |
| `a` | `unknown` | ✓ | - |
| `is` | `unknown` | ✓ | - |
| `object` | `unknown` | ✓ | - |
| `a` | `unknown` | ✓ | - |
| `in` | `unknown` | ✓ | - |
| `when` | `class` | ✓ | - |
| `present` | `unknown` | ✓ | - |
| `associated` | `unknown` | ✓ | - |
| `Note` | `unknown` | ✓ | - |
| `that` | `unknown` | ✓ | - |
| `columns` | `unknown` | ✓ | - |
| `the` | `class` | ✓ | - |
| `to` | `unknown` | ✓ | - |
| `are` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `object` | `unknown` | ✓ | - |
| `of` | `unknown` | ✓ | - |
| `Further` | `unknown` | ✓ | - |
| `parent` | `Column[Any]` | ✓ | - |
| `_table_column` | `Optional[Column[Any]]` | ✓ | - |
| `target_fullname` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |

**Schema: `DefaultGenerator`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `This` | `unknown` | ✓ | - |
| `It` | `unknown` | ✓ | - |
| `is_sequence` | `unknown` | ✓ | - |
| `is_identity` | `unknown` | ✓ | - |
| `is_clause_element` | `unknown` | ✓ | - |
| `is_callable` | `unknown` | ✓ | - |
| `is_scalar` | `unknown` | ✓ | - |
| `has_arg` | `unknown` | ✓ | - |
| `is_sentinel` | `unknown` | ✓ | - |
| `column` | `Optional[Column[Any]]` | ✓ | - |

**Schema: `Sequence`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `The` | `class` | ✓ | - |
| `parameters` | `unknown` | ✓ | - |
| `a` | `unknown` | ✓ | - |
| `or` | `class` | ✓ | - |
| `rendering` | `unknown` | ✓ | - |
| `for` | `unknown` | ✓ | - |
| `The` | `class` | ✓ | - |
| `When` | `unknown` | ✓ | - |
| `target` | `unknown` | ✓ | - |
| `be` | `unknown` | ✓ | - |
| `the` | `class` | ✓ | - |
| `is_sequence` | `unknown` | ✓ | - |
| `column` | `Optional[Column[Any]]` | ✓ | - |
| `data_type` | `Optional[TypeEngine[int]]` | ✓ | - |

**Schema: `FetchedValue`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Use` | `class` | ✓ | - |
| `to` | `unknown` | ✓ | - |
| `E` | `unknown` | ✓ | - |
| `Would` | `unknown` | ✓ | - |
| `will` | `unknown` | ✓ | - |
| `INSERT` | `unknown` | ✓ | - |
| `reflected` | `unknown` | ✓ | - |
| `has_argument` | `unknown` | ✓ | - |
| `is_clause_element` | `unknown` | ✓ | - |
| `is_identity` | `unknown` | ✓ | - |
| `column` | `Optional[Column[Any]]` | ✓ | - |

**Schema: `Constraint`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `constraint` | `unknown` | ✓ | - |
| `objects` | `unknown` | ✓ | - |
| `_creation_order` | `int` | ✓ | - |
| `_column_flag` | `bool` | ✓ | - |

**Schema: `Index`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Defines` | `unknown` | ✓ | - |
| `E` | `unknown` | ✓ | - |
| `For` | `unknown` | ✓ | - |
| `For` | `unknown` | ✓ | - |
| `Functional` | `unknown` | ✓ | - |
| `An` | `class` | ✓ | - |
| `either` | `unknown` | ✓ | - |
| `the` | `unknown` | ✓ | - |
| `of` | `unknown` | ✓ | - |
| `To` | `unknown` | ✓ | - |
| `table` | `Optional[Table]` | ✓ | - |
| `expressions` | `_typing_Sequence[Union[str, ColumnElement[Any]]]` | ✓ | - |
| `_table_bound_expressions` | `_typing_Sequence[ColumnElement[Any]]` | ✓ | - |
| `_NamingSchemaCallable` | `unknown` | ✓ | - |
| `Callable` | `unknown` | ✓ | - |
| `Callable` | `unknown` | ✓ | - |

**Schema: `MetaData`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `objects` | `unknown` | ✓ | - |
| `constructs` | `unknown` | ✓ | - |
| `Holds` | `unknown` | ✓ | - |
| `an` | `unknown` | ✓ | - |
| `in` | `unknown` | ✓ | - |
| `execution` | `unknown` | ✓ | - |
| `The` | `class` | ✓ | - |
| `Construction` | `unknown` | ✓ | - |
| `object` | `unknown` | ✓ | - |
| `either` | `unknown` | ✓ | - |
| `tables` | `util` | ✓ | - |
| `objects` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `attribute` | `unknown` | ✓ | - |
| `for` | `unknown` | ✓ | - |
| `this` | `unknown` | ✓ | - |
| `as` | `attr` | ✓ | - |
| `it` | `unknown` | ✓ | - |
| `form` | `unknown` | ✓ | - |

**Schema: `Computed`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `The` | `class` | ✓ | - |
| `argument` | `unknown` | ✓ | - |
| `See` | `unknown` | ✓ | - |
| `column` | `Optional[Column[Any]]` | ✓ | - |

### [New] [bugfix] Changes in selectable.py

- **File**: `venv\Lib\site-packages\sqlalchemy\sql\selectable.py`
- **Captured**: 4/28/2026, 1:02:59 PM
- **Category**: bugfix
**Summary:** Modified selectable.py: 7266 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\sqlalchemy\sql\selectable.py` (+7266 / -0)
**Schema: `SelectStatementGrouping`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `This` | `unknown` | ✓ | - |
| `an` | `unknown` | ✓ | - |
| `compound` | `unknown` | ✓ | - |
| `_traverse_internals` | `_TraverseInternalsType` | ✓ | - |
| `_is_select_container` | `unknown` | ✓ | - |
| `element` | `_SB` | ✓ | - |
| `if` | `unknown` | ✓ | - |

**Schema: `GenerativeSelect`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `added` | `unknown` | ✓ | - |
| `This` | `unknown` | ✓ | - |
| `where` | `unknown` | ✓ | - |
| `rendering` | `unknown` | ✓ | - |
| `while` | `unknown` | ✓ | - |
| `and` | `unknown` | ✓ | - |
| `represents` | `unknown` | ✓ | - |
| `only` | `unknown` | ✓ | - |
| `_order_by_clauses` | `Tuple[ColumnElement[Any],` | ✓ | - |
| `_group_by_clauses` | `Tuple[ColumnElement[Any],` | ✓ | - |
| `_limit_clause` | `Optional[ColumnElement[Any]]` | ✓ | - |
| `_offset_clause` | `Optional[ColumnElement[Any]]` | ✓ | - |
| `_fetch_clause` | `Optional[ColumnElement[Any]]` | ✓ | - |
| `_fetch_clause_options` | `Optional[Dict[str, bool]]` | ✓ | - |
| `_for_update_arg` | `Optional[ForUpdateArg]` | ✓ | - |

**Schema: `TextualSelect`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `interface` | `unknown` | ✓ | - |
| `This` | `unknown` | ✓ | - |
| `and` | `unknown` | ✓ | - |
| `The` | `class` | ✓ | - |
| `method` | `unknown` | ✓ | - |
| `_label_style` | `unknown` | ✓ | - |
| `_traverse_internals` | `_TraverseInternalsType` | ✓ | - |
| `_is_textual` | `unknown` | ✓ | - |
| `is_text` | `unknown` | ✓ | - |
| `is_select` | `unknown` | ✓ | - |
| `TextAsFrom` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in sqltypes.py

- **File**: `venv\Lib\site-packages\sqlalchemy\sql\sqltypes.py`
- **Captured**: 4/28/2026, 1:02:57 PM
- **Category**: bugfix
**Summary:** Modified sqltypes.py: 3931 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\sqlalchemy\sql\sqltypes.py` (+3931 / -0)
**Schema: `SchemaType`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `associated` | `unknown` | ✓ | - |
| `Supports` | `unknown` | ✓ | - |
| `as` | `unknown` | ✓ | - |
| `constraints` | `unknown` | ✓ | - |
| `surrounding` | `unknown` | ✓ | - |
| `_use_schema_map` | `unknown` | ✓ | - |
| `name` | `Optional[str]` | ✓ | - |
| `_EnumTupleArg` | `unknown` | ✓ | - |

**Schema: `Enum`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `The` | `class` | ✓ | - |
| `which` | `unknown` | ✓ | - |
| `The` | `class` | ✓ | - |
| `type` | `unknown` | ✓ | - |
| `An` | `unknown` | ✓ | - |
| `when` | `unknown` | ✓ | - |
| `see` | `unknown` | ✓ | - |
| `The` | `class` | ✓ | - |
| `values` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `against` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `plain` | `unknown` | ✓ | - |
| `set` | `unknown` | ✓ | - |
| `not` | `unknown` | ✓ | - |
| `impacts` | `unknown` | ✓ | - |
| `use` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `alternatively` | `unknown` | ✓ | - |
| `of` | `unknown` | ✓ | - |
| `When` | `unknown` | ✓ | - |
| `both` | `unknown` | ✓ | - |
| `a` | `unknown` | ✓ | - |
| `Above` | `unknown` | ✓ | - |
| `are` | `unknown` | ✓ | - |
| `indicated` | `unknown` | ✓ | - |
| `therefore` | `unknown` | ✓ | - |
| `In` | `unknown` | ✓ | - |
| `this` | `unknown` | ✓ | - |
| `with` | `unknown` | ✓ | - |
| `values` | `unknown` | ✓ | - |
| `a` | `unknown` | ✓ | - |
| `values_callable` | `Optional[Callable[[Type[enum` | ✓ | - |
| `_valid_lookup` | `Dict[Union[enum` | ✓ | - |
| `_object_lookup` | `Dict[Optional[str], Union[enum` | ✓ | - |
| `comparator_factory` | `unknown` | ✓ | - |

**Schema: `Boolean`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `and` | `unknown` | ✓ | - |
| `The` | `class` | ✓ | - |
| `that` | `unknown` | ✓ | - |
| `backends` | `unknown` | ✓ | - |
| `or` | `unknown` | ✓ | - |
| `don` | `unknown` | ✓ | - |
| `also` | `unknown` | ✓ | - |
| `native` | `unknown` | ✓ | - |
| `_strict_bools` | `unknown` | ✓ | - |

**Schema: `ARRAY`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `standard` | `unknown` | ✓ | - |
| `which` | `unknown` | ✓ | - |
| `arrays` | `unknown` | ✓ | - |
| `some` | `unknown` | ✓ | - |
| `for` | `unknown` | ✓ | - |
| `An` | `class` | ✓ | - |
| `of` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `meaning` | `unknown` | ✓ | - |
| `with` | `unknown` | ✓ | - |
| `construct` | `unknown` | ✓ | - |
| `The` | `class` | ✓ | - |
| `of` | `unknown` | ✓ | - |
| `Sending` | `unknown` | ✓ | - |
| `datatype` | `unknown` | ✓ | - |
| `is` | `unknown` | ✓ | - |
| `For` | `unknown` | ✓ | - |
| `dimension` | `unknown` | ✓ | - |
| `SQL` | `unknown` | ✓ | - |
| `constructs` | `unknown` | ✓ | - |
| `SELECT` | `unknown` | ✓ | - |
| `as` | `unknown` | ✓ | - |
| `method` | `unknown` | ✓ | - |
| `Indexed` | `unknown` | ✓ | - |
| `for` | `unknown` | ✓ | - |
| `The` | `class` | ✓ | - |
| `_is_array` | `unknown` | ✓ | - |
| `zero_indexes` | `unknown` | ✓ | - |
| `on` | `unknown` | ✓ | - |
| `comparator_factory` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in type_api.py

- **File**: `venv\Lib\site-packages\sqlalchemy\sql\type_api.py`
- **Captured**: 4/28/2026, 1:02:56 PM
- **Category**: bugfix
**Summary:** Modified type_api.py: 2369 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\sqlalchemy\sql\type_api.py` (+2369 / -0)
**Schema: `_TypeMemoDict`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `literal` | `Optional[_LiteralProcessorType[Any]]` | ✓ | - |
| `bind` | `Optional[_BindProcessorType[Any]]` | ✓ | - |
| `sentinel` | `Optional[_SentinelProcessorType[Any]]` | ✓ | - |
| `custom` | `Dict[Any, object]` | ✓ | - |

**Schema: `TypeDecorator`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `to` | `unknown` | ✓ | - |
| `This` | `unknown` | ✓ | - |
| `built` | `unknown` | ✓ | - |
| `the` | `unknown` | ✓ | - |
| `Typical` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `method` | `unknown` | ✓ | - |
| `given` | `unknown` | ✓ | - |
| `The` | `attr` | ✓ | - |
| `custom` | `class` | ✓ | - |
| `This` | `unknown` | ✓ | - |
| `when` | `unknown` | ✓ | - |
| `that` | `unknown` | ✓ | - |
| `to` | `unknown` | ✓ | - |
| `every` | `unknown` | ✓ | - |
| `See` | `attr` | ✓ | - |
| `Types` | `unknown` | ✓ | - |
| `used` | `unknown` | ✓ | - |
| `method` | `unknown` | ✓ | - |
| `Python` | `unknown` | ✓ | - |
| `expression` | `unknown` | ✓ | - |
| `Above` | `unknown` | ✓ | - |
| `we` | `unknown` | ✓ | - |
| `by` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `coerce` | `unknown` | ✓ | - |
| `However` | `unknown` | ✓ | - |
| `incoming` | `unknown` | ✓ | - |
| `we` | `unknown` | ✓ | - |
| `Our` | `unknown` | ✓ | - |
| `This` | `unknown` | ✓ | - |
| `that` | `unknown` | ✓ | - |
| `that` | `unknown` | ✓ | - |
| `value` | `unknown` | ✓ | - |
| `_is_type_decorator` | `unknown` | ✓ | - |
| `impl` | `Union[TypeEngine[Any], Type[TypeEngine[Any]]]` | ✓ | - |
| `coerce_to_is_types` | `Sequence[Type[Any]]` | ✓ | - |
| `level` | `unknown` | ✓ | - |
| `For` | `unknown` | ✓ | - |
| `as` | `unknown` | ✓ | - |
| `Custom` | `class` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `constants` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in automap.py

- **File**: `venv\Lib\site-packages\sqlalchemy\ext\automap.py`
- **Captured**: 4/28/2026, 1:02:53 PM
- **Category**: bugfix
**Summary:** Modified automap.py: 1702 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\sqlalchemy\ext\automap.py` (+1702 / -0)
**Schema: `User`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `engine` | `unknown` | ✓ | - |
| `Base` | `unknown` | ✓ | - |
| `Address` | `unknown` | ✓ | - |
| `u1` | `unknown` | ✓ | - |
| `print` | `unknown` | ✓ | - |
| `a1` | `unknown` | ✓ | - |
| `print` | `unknown` | ✓ | - |
| `import` | `unknown` | ✓ | - |
| `import` | `unknown` | ✓ | - |
| `_pluralizer` | `unknown` | ✓ | - |

**Schema: `Employee`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `CREATE` | `unknown` | ✓ | - |
| `CREATE` | `unknown` | ✓ | - |
| `Base` | `unknown` | ✓ | - |
| `Base` | `unknown` | ✓ | - |
| `Base` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `Base` | `unknown` | ✓ | - |
| `Base` | `unknown` | ✓ | - |
| `a1` | `unknown` | ✓ | - |
| `a2` | `unknown` | ✓ | - |
| `u1` | `unknown` | ✓ | - |
| `assert` | `unknown` | ✓ | - |
| `Base` | `unknown` | ✓ | - |
| `may` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `_KT` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in extensions.py

- **File**: `venv\Lib\site-packages\sqlalchemy\ext\declarative\extensions.py`
- **Captured**: 4/28/2026, 1:02:52 PM
- **Category**: bugfix
**Summary:** Modified extensions.py: 565 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\sqlalchemy\ext\declarative\extensions.py` (+565 / -0)
**Schema: `Employee`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `The` | `unknown` | ✓ | - |
| `actual` | `unknown` | ✓ | - |
| `discriminator` | `unknown` | ✓ | - |

**Schema: `AbstractConcreteBase`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `function` | `unknown` | ✓ | - |
| `to` | `unknown` | ✓ | - |
| `a` | `unknown` | ✓ | - |
| `immediately` | `unknown` | ✓ | - |
| `declarative` | `unknown` | ✓ | - |
| `mapped` | `unknown` | ✓ | - |
| `mapped` | `unknown` | ✓ | - |
| `own` | `unknown` | ✓ | - |
| `immediately` | `unknown` | ✓ | - |
| `Example` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `at` | `unknown` | ✓ | - |
| `or` | `unknown` | ✓ | - |
| `and` | `unknown` | ✓ | - |
| `after` | `unknown` | ✓ | - |
| `not` | `unknown` | ✓ | - |
| `Using` | `unknown` | ✓ | - |
| `that` | `unknown` | ✓ | - |
| `we` | `unknown` | ✓ | - |
| `When` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in row.py

- **File**: `venv\Lib\site-packages\sqlalchemy\engine\row.py`
- **Captured**: 4/28/2026, 1:02:49 PM
- **Category**: bugfix
**Summary:** Modified row.py: 401 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\sqlalchemy\engine\row.py` (+401 / -0)
**Schema: `Row`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `The` | `class` | ✓ | - |
| `typically` | `unknown` | ✓ | - |
| `tuple` | `unknown` | ✓ | - |
| `The` | `class` | ✓ | - |
| `tuple` | `unknown` | ✓ | - |
| `such` | `unknown` | ✓ | - |
| `attribute` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `BaseRowProxy` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in base.py

- **File**: `venv\Lib\site-packages\sqlalchemy\testing\fixtures\base.py`
- **Captured**: 4/28/2026, 1:02:47 PM
- **Category**: bugfix
**Summary:** Modified base.py: 385 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\sqlalchemy\testing\fixtures\base.py` (+385 / -0)
**Schema: `Base`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_connection_fixture_connection` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in sql.py

- **File**: `venv\Lib\site-packages\sqlalchemy\testing\fixtures\sql.py`
- **Captured**: 4/28/2026, 1:02:45 PM
- **Category**: bugfix
**Summary:** Modified sql.py: 483 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\sqlalchemy\testing\fixtures\sql.py` (+483 / -0)
**Schema: `TablesTest`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `run_setup_bind` | `unknown` | ✓ | - |
| `run_create_tables` | `unknown` | ✓ | - |
| `run_inserts` | `unknown` | ✓ | - |
| `run_deletes` | `unknown` | ✓ | - |
| `run_dispose_bind` | `unknown` | ✓ | - |
| `bind` | `unknown` | ✓ | - |
| `_tables_metadata` | `unknown` | ✓ | - |
| `tables` | `unknown` | ✓ | - |
| `other` | `unknown` | ✓ | - |
| `sequences` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modeling_paddleocr_vl.py

- **File**: `venv\Lib\site-packages\transformers\models\paddleocr_vl\modeling_paddleocr_vl.py`
- **Captured**: 4/28/2026, 1:02:43 PM
- **Category**: bugfix
**Summary:** Modified modeling_paddleocr_vl.py: 1736 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\paddleocr_vl\modeling_paddleocr_vl.py` (+1736 / -0)
**Schema: `PaddleOCRVLPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `PaddleOCRVLConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_skip_keys_device_placement` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `_supports_flex_attn` | `unknown` | ✓ | - |
| `_can_compile_fullgraph` | `unknown` | ✓ | - |
| `_supports_attention_backend` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |

**Schema: `PaddleOCRVisionTransformer`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `PaddleOCRVisionConfig` | ✓ | - |
| `main_input_name` | `unknown` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |

**Schema: `PaddleOCRVisionModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `PaddleOCRVisionConfig` | ✓ | - |
| `main_input_name` | `unknown` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `Base` | `unknown` | ✓ | - |

**Schema: `PaddleOCRVLModelOutputWithPast`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `past_key_values` | `unknown` | ✓ | - |
| `rope_deltas` | `unknown` | ✓ | - |
| `last_hidden_state` | `torch` | ✓ | - |
| `past_key_values` | `Cache` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[torch` | ✓ | - |
| `rope_deltas` | `torch` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `Base` | `unknown` | ✓ | - |

**Schema: `PaddleOCRVLCausalLMOutputWithPast`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `loss` | `unknown` | ✓ | - |
| `logits` | `unknown` | ✓ | - |
| `past_key_values` | `unknown` | ✓ | - |
| `rope_deltas` | `unknown` | ✓ | - |
| `loss` | `torch` | ✓ | - |
| `logits` | `torch` | ✓ | - |
| `past_key_values` | `Cache` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[torch` | ✓ | - |
| `rope_deltas` | `torch` | ✓ | - |

**Schema: `PaddleOCRVLModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `base_model_prefix` | `unknown` | ✓ | - |
| `accepts_loss_kwargs` | `unknown` | ✓ | - |
| `_keys_to_ignore_on_load_unexpected` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modular_paddleocr_vl.py

- **File**: `venv\Lib\site-packages\transformers\models\paddleocr_vl\modular_paddleocr_vl.py`
- **Captured**: 4/28/2026, 1:02:42 PM
- **Category**: bugfix
**Summary:** Modified modular_paddleocr_vl.py: 1211 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\paddleocr_vl\modular_paddleocr_vl.py` (+1211 / -0)
**Schema: `PaddleOCRVLPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `PaddleOCRVLConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_skip_keys_device_placement` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `_supports_flex_attn` | `unknown` | ✓ | - |
| `_can_compile_fullgraph` | `unknown` | ✓ | - |
| `_supports_attention_backend` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |

**Schema: `PaddleOCRVisionTransformer`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `PaddleOCRVisionConfig` | ✓ | - |
| `main_input_name` | `unknown` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |

**Schema: `PaddleOCRVisionModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `PaddleOCRVisionConfig` | ✓ | - |
| `main_input_name` | `unknown` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |

**Schema: `PaddleOCRVLModelOutputWithPast`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `pass` | `unknown` | ✓ | - |

**Schema: `PaddleOCRVLModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_keys_to_ignore_on_load_unexpected` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in hybrid.py

- **File**: `venv\Lib\site-packages\sqlalchemy\ext\hybrid.py`
- **Captured**: 4/28/2026, 1:02:40 PM
- **Category**: bugfix
**Summary:** Modified hybrid.py: 1536 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\sqlalchemy\ext\hybrid.py` (+1536 / -0)
**Schema: `Base`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `5` | `unknown` | ✓ | - |
| `FROM` | `unknown` | ✓ | - |
| `FROM` | `unknown` | ✓ | - |
| `WHERE` | `unknown` | ✓ | - |
| `FROM` | `unknown` | ✓ | - |
| `WHERE` | `unknown` | ✓ | - |
| `True` | `unknown` | ✓ | - |
| `False` | `unknown` | ✓ | - |
| `True` | `unknown` | ✓ | - |
| `False` | `unknown` | ✓ | - |
| `FROM` | `unknown` | ✓ | - |
| `WHERE` | `unknown` | ✓ | - |
| `interval` | `unknown` | ✓ | - |
| `interval_1` | `unknown` | ✓ | - |
| `FROM` | `unknown` | ✓ | - |
| `WHERE` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `for` | `unknown` | ✓ | - |
| `not` | `unknown` | ✓ | - |
| `FROM` | `unknown` | ✓ | - |
| `WHERE` | `unknown` | ✓ | - |
| `less` | `unknown` | ✓ | - |
| `while` | `unknown` | ✓ | - |
| `use` | `unknown` | ✓ | - |
| `Defining` | `unknown` | ✓ | - |
| `5` | `unknown` | ✓ | - |
| `17` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `stmt` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `UPDATE` | `unknown` | ✓ | - |
| `Working` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `stated` | `unknown` | ✓ | - |
| `demand` | `unknown` | ✓ | - |
| `not` | `unknown` | ✓ | - |
| `collection` | `unknown` | ✓ | - |
| `account` | `unknown` | ✓ | - |
| `FROM` | `unknown` | ✓ | - |
| `WHERE` | `unknown` | ✓ | - |
| `account` | `unknown` | ✓ | - |
| `FROM` | `unknown` | ✓ | - |
| `WHERE` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `FROM` | `unknown` | ✓ | - |
| `WHERE` | `unknown` | ✓ | - |
| `in` | `unknown` | ✓ | - |
| `They` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `FROM` | `unknown` | ✓ | - |
| `WHERE` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `FROM` | `unknown` | ✓ | - |
| `WHERE` | `unknown` | ✓ | - |
| `lower` | `unknown` | ✓ | - |
| `FROM` | `unknown` | ✓ | - |
| `WHERE` | `unknown` | ✓ | - |
| `True` | `unknown` | ✓ | - |
| `False` | `unknown` | ✓ | - |
| `someword` | `unknown` | ✓ | - |
| `on` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in indexable.py

- **File**: `venv\Lib\site-packages\sqlalchemy\ext\indexable.py`
- **Captured**: 4/28/2026, 1:02:38 PM
- **Category**: bugfix
**Summary:** Modified indexable.py: 365 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\sqlalchemy\ext\indexable.py` (+365 / -0)
**Schema: `Person`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `AttributeError` | `unknown` | ✓ | - |
| `None` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `Base` | `unknown` | ✓ | - |
| `q` | `unknown` | ✓ | - |
| `SELECT` | `unknown` | ✓ | - |
| `FROM` | `unknown` | ✓ | - |
| `WHERE` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `Base` | `unknown` | ✓ | - |
| `SELECT` | `unknown` | ✓ | - |
| `FROM` | `unknown` | ✓ | - |
| `WHERE` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in mutable.py

- **File**: `venv\Lib\site-packages\sqlalchemy\ext\mutable.py`
- **Captured**: 4/28/2026, 1:02:37 PM
- **Category**: bugfix
**Summary:** Modified mutable.py: 1086 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\sqlalchemy\ext\mutable.py` (+1086 / -0)
**Schema: `Base`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `True` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `MutableDict` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |

**Schema: `Base`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `BEGIN` | `unknown` | ✓ | - |
| `INSERT` | `unknown` | ✓ | - |
| `True` | `unknown` | ✓ | - |
| `UPDATE` | `unknown` | ✓ | - |
| `COMMIT` | `unknown` | ✓ | - |

**Schema: `Mutable`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `events` | `unknown` | ✓ | - |
| `See` | `unknown` | ✓ | - |

**Schema: `MutableComposite`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `events` | `unknown` | ✓ | - |
| `owning` | `unknown` | ✓ | - |
| `See` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `_setup_composite_listener` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in index.html

- **File**: `venv\Lib\site-packages\streamlit\static\index.html`
- **Captured**: 4/28/2026, 1:02:33 PM
- **Category**: bugfix
**Summary:** Modified index.html: 87 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\streamlit\static\index.html` (+87 / -0)

### [New] [bugfix] Changes in orderinglist.py

- **File**: `venv\Lib\site-packages\sqlalchemy\ext\orderinglist.py`
- **Captured**: 4/28/2026, 1:02:27 PM
- **Category**: bugfix
**Summary:** Modified orderinglist.py: 440 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\sqlalchemy\ext\orderinglist.py` (+440 / -0)
**Schema: `Slide`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `from` | `unknown` | ✓ | - |
| `Base` | `unknown` | ✓ | - |
| `s` | `unknown` | ✓ | - |
| `s` | `unknown` | ✓ | - |
| `s` | `unknown` | ✓ | - |
| `s` | `unknown` | ✓ | - |
| `s` | `unknown` | ✓ | - |
| `s` | `unknown` | ✓ | - |
| `attr` | `str,` | ✓ | - |
| `count_from` | `Optional[int]` | ✓ | - |
| `ordering_func` | `Optional[OrderingFunc[_T]]` | ✓ | - |
| `reorder_on_append` | `bool` | ✓ | - |
| `Returns` | `unknown` | ✓ | - |
| `relationship` | `unknown` | ✓ | - |
| `Additional` | `unknown` | ✓ | - |
| `kw` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `try` | `f` | ✓ | - |
| `except` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `Keyword` | `unknown` | ✓ | - |
| `count_from` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modeling_paligemma.py

- **File**: `venv\Lib\site-packages\transformers\models\paligemma\modeling_paligemma.py`
- **Captured**: 4/28/2026, 1:02:23 PM
- **Category**: bugfix
**Summary:** Modified modeling_paligemma.py: 558 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\paligemma\modeling_paligemma.py` (+558 / -0)
**Schema: `PaligemmaModelOutputWithPast`** (pydantic)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `image_hidden_states` | `unknown` | ✓ | - |
| `image_hidden_states` | `torch` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `Base` | `unknown` | ✓ | - |

**Schema: `PaliGemmaCausalLMOutputWithPast`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `loss` | `unknown` | ✓ | - |
| `logits` | `unknown` | ✓ | - |
| `past_key_values` | `unknown` | ✓ | - |
| `image_hidden_states` | `unknown` | ✓ | - |
| `loss` | `torch` | ✓ | - |
| `logits` | `torch` | ✓ | - |
| `past_key_values` | `Cache` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[torch` | ✓ | - |
| `image_hidden_states` | `torch` | ✓ | - |

**Schema: `PaliGemmaPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `PaliGemmaConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_skip_keys_device_placement` | `unknown` | ✓ | - |
| `_can_compile_fullgraph` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `_supports_flex_attn` | `unknown` | ✓ | - |
| `_supports_attention_backend` | `unknown` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |

**Schema: `PaliGemmaModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `accepts_loss_kwargs` | `unknown` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in DeckGlJsonChart.DputmGud.js

- **File**: `venv\Lib\site-packages\streamlit\static\static\js\DeckGlJsonChart.DputmGud.js`
- **Captured**: 4/28/2026, 1:02:15 PM
- **Category**: bugfix
**Summary:** Modified DeckGlJsonChart.DputmGud.js: 5858 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\streamlit\static\static\js\DeckGlJsonChart.DputmGud.js` (+5858 / -0)
**API Endpoints** (`DeckGlJsonChart.DputmGud.js`):

| Method | Route | Handler | Middleware |
|--------|-------|---------|------------|
| `URL(`GETCAPABILITIES`,N` | `GetCapabilities` | o | - |
| `URL(`GETMAP`,N` | `GetMap` | o | - |
| `URL(`GETFEATUREINFO`,I` | `GetFeatureInfo` | o | - |
| `URL(`DESCRIBELAYER`,N` | `DescribeLayer` | o | - |
| `URL(`GETLEGENDGRAPHIC`,N` | `GetLegendGraphic` | o | - |
| `URL(`EXPORTIMAGE`,R` | `exportImage` | o | - |

### [New] [bugfix] Changes in embed.BwU7eQR9.js

- **File**: `venv\Lib\site-packages\streamlit\static\static\js\embed.BwU7eQR9.js`
- **Captured**: 4/28/2026, 1:02:11 PM
- **Category**: bugfix
**Summary:** Modified embed.BwU7eQR9.js: 191 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\streamlit\static\static\js\embed.BwU7eQR9.js` (+191 / -0)

### [New] [bugfix] Changes in GraphVizChart.DB7xGpeO.js

- **File**: `venv\Lib\site-packages\streamlit\static\static\js\GraphVizChart.DB7xGpeO.js`
- **Captured**: 4/28/2026, 1:02:04 PM
- **Category**: bugfix
**Summary:** Modified GraphVizChart.DB7xGpeO.js: 3 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\streamlit\static\static\js\GraphVizChart.DB7xGpeO.js` (+3 / -0)
**API Endpoints** (`GraphVizChart.DB7xGpeO.js`):

| Method | Route | Handler | Middleware |
|--------|-------|---------|------------|
| `PATH(`/`,R` | `/` | O | - |

### [New] [bugfix] Changes in index.k-9rUdPI.js

- **File**: `venv\Lib\site-packages\streamlit\static\static\js\index.k-9rUdPI.js`
- **Captured**: 4/28/2026, 1:01:58 PM
- **Category**: bugfix
**Summary:** Modified index.k-9rUdPI.js: 25 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\streamlit\static\static\js\index.k-9rUdPI.js` (+25 / -0)
**API Endpoints** (`index.k-9rUdPI.js`):

| Method | Route | Handler | Middleware |
|--------|-------|---------|------------|
| `URL(`../MEDIA/FIREWORKS.B4D-_KUE.GIF`,IMPORT` | `../media/fireworks.B4d-_KUe.gif` | Op | - |
| `URL(`../MEDIA/SNOWFLAKE.JU2JBHL8.SVG`,IMPORT` | `../media/snowflake.JU2jBHL8.svg` | Op | - |

### [New] [bugfix] Changes in PlotlyChart.CBOrhmVc.js

- **File**: `venv\Lib\site-packages\streamlit\static\static\js\PlotlyChart.CBOrhmVc.js`
- **Captured**: 4/28/2026, 1:01:49 PM
- **Category**: bugfix
**Summary:** Modified PlotlyChart.CBOrhmVc.js: 3790 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\streamlit\static\static\js\PlotlyChart.CBOrhmVc.js` (+3790 / -0)

### [New] [bugfix] Changes in reactJsonViewCompat.C6CTzcn3.js

- **File**: `venv\Lib\site-packages\streamlit\static\static\js\reactJsonViewCompat.C6CTzcn3.js`
- **Captured**: 4/28/2026, 1:01:33 PM
- **Category**: bugfix
**Summary:** Modified reactJsonViewCompat.C6CTzcn3.js: 13 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\streamlit\static\static\js\reactJsonViewCompat.C6CTzcn3.js` (+13 / -0)

### [New] [bugfix] Changes in Snow.a4omAiaI.js

- **File**: `venv\Lib\site-packages\streamlit\static\static\js\Snow.a4omAiaI.js`
- **Captured**: 4/28/2026, 1:01:28 PM
- **Category**: bugfix
**Summary:** Modified Snow.a4omAiaI.js: 7 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\streamlit\static\static\js\Snow.a4omAiaI.js` (+7 / -0)
**API Endpoints** (`Snow.a4omAiaI.js`):

| Method | Route | Handler | Middleware |
|--------|-------|---------|------------|
| `URL(`../MEDIA/FLAKE-0.DGWAVVM5.PNG`,IMPORT` | `../media/flake-0.DgWaVvm5.png` | r | - |
| `URL(`../MEDIA/FLAKE-1.B2R5AHMK.PNG`,IMPORT` | `../media/flake-1.B2r5AHMK.png` | r | - |
| `URL(`../MEDIA/FLAKE-2.BNWSEXPC.PNG`,IMPORT` | `../media/flake-2.BnWSExPC.png` | r | - |

### [New] [bugfix] Changes in old_polynomialring.py

- **File**: `venv\Lib\site-packages\sympy\polys\domains\old_polynomialring.py`
- **Captured**: 4/28/2026, 1:01:17 PM
- **Category**: bugfix
**Summary:** Modified old_polynomialring.py: 491 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\sympy\polys\domains\old_polynomialring.py` (+491 / -0)
**Schema: `GlobalPolynomialRing`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `is_PolynomialRing` | `unknown` | ✓ | - |
| `dtype` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in test_dialect.py

- **File**: `venv\Lib\site-packages\sqlalchemy\testing\suite\test_dialect.py`
- **Captured**: 4/28/2026, 1:01:14 PM
- **Category**: bugfix
**Summary:** Modified test_dialect.py: 777 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\sqlalchemy\testing\suite\test_dialect.py` (+777 / -0)
**Schema: `FutureWeCanSetDefaultSchemaWEventsTest`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `pass` | `unknown` | ✓ | - |

**Schema: `DifficultParametersTest`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `tough_parameters` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in test_types.py

- **File**: `venv\Lib\site-packages\sqlalchemy\testing\suite\test_types.py`
- **Captured**: 4/28/2026, 1:01:13 PM
- **Category**: bugfix
**Summary:** Modified test_types.py: 2148 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\sqlalchemy\testing\suite\test_types.py` (+2148 / -0)
**Schema: `_UnicodeFixture`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `data` | `unknown` | ✓ | - |

**Schema: `IntervalTest`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `datatype` | `unknown` | ✓ | - |
| `data` | `unknown` | ✓ | - |

**Schema: `_DateFixture`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `compare` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modeling_parakeet.py

- **File**: `venv\Lib\site-packages\transformers\models\parakeet\modeling_parakeet.py`
- **Captured**: 4/28/2026, 1:01:11 PM
- **Category**: bugfix
**Summary:** Modified modeling_parakeet.py: 816 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\parakeet\modeling_parakeet.py` (+816 / -0)
**Schema: `ParakeetEncoderModelOutput`** (pydantic)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `attention_mask` | `torch` | ✓ | - |

**Schema: `ParakeetPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `ParakeetCTCConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `main_input_name` | `unknown` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_supports_flat_attention_mask` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `_supports_flex_attn` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_can_compile_fullgraph` | `unknown` | ✓ | - |
| `_supports_attention_backend` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |

**Schema: `ParakeetEncoder`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `ParakeetEncoderConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |

**Schema: `ParakeetGenerateOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Outputs` | `unknown` | ✓ | - |
| `Args` | `sequences` | ✓ | - |
| `sequences` | `torch` | ✓ | - |
| `logits` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[tuple[torch` | ✓ | - |
| `hidden_states` | `tuple[tuple[torch` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `Parakeet` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modular_parakeet.py

- **File**: `venv\Lib\site-packages\transformers\models\parakeet\modular_parakeet.py`
- **Captured**: 4/28/2026, 1:01:10 PM
- **Category**: bugfix
**Summary:** Modified modular_parakeet.py: 655 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\parakeet\modular_parakeet.py` (+655 / -0)
**Schema: `ParakeetEncoderModelOutput`** (pydantic)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `attention_mask` | `torch` | ✓ | - |

**Schema: `ParakeetPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `ParakeetCTCConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `main_input_name` | `unknown` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_supports_flat_attention_mask` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `_supports_flex_attn` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_can_compile_fullgraph` | `unknown` | ✓ | - |
| `_supports_attention_backend` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |

**Schema: `ParakeetEncoder`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `ParakeetEncoderConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |

**Schema: `ParakeetGenerateOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Outputs` | `unknown` | ✓ | - |
| `Args` | `sequences` | ✓ | - |
| `sequences` | `torch` | ✓ | - |
| `logits` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[tuple[torch` | ✓ | - |
| `hidden_states` | `tuple[tuple[torch` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `Parakeet` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in base.py

- **File**: `venv\Lib\site-packages\sqlalchemy\orm\base.py`
- **Captured**: 4/28/2026, 1:01:08 PM
- **Category**: bugfix
**Summary:** Modified base.py: 972 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\sqlalchemy\orm\base.py` (+972 / -0)
**Schema: `Mapped`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `This` | `unknown` | ✓ | - |
| `attribute` | `unknown` | ✓ | - |
| `checkers` | `unknown` | ✓ | - |
| `are` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `the` | `ref` | ✓ | - |
| `of` | `class` | ✓ | - |
| `the` | `unknown` | ✓ | - |
| `and` | `func` | ✓ | - |
| `if` | `unknown` | ✓ | - |

**Schema: `DynamicMapped`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `The` | `class` | ✓ | - |
| `to` | `unknown` | ✓ | - |
| `for` | `unknown` | ✓ | - |
| `E` | `unknown` | ✓ | - |
| `See` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in decl_api.py

- **File**: `venv\Lib\site-packages\sqlalchemy\orm\decl_api.py`
- **Captured**: 4/28/2026, 1:01:06 PM
- **Category**: bugfix
**Summary:** Modified decl_api.py: 2005 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\sqlalchemy\orm\decl_api.py` (+2005 / -0)
**Schema: `MyClass`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `The` | `ref` | ✓ | - |
| `is` | `unknown` | ✓ | - |
| `feature` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |

**Schema: `Employee`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `explicitly` | `unknown` | ✓ | - |
| `runtime` | `unknown` | ✓ | - |
| `typing` | `unknown` | ✓ | - |
| `having` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |

**Schema: `MyModel`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `The` | `func` | ✓ | - |
| `the` | `unknown` | ✓ | - |
| `the` | `ref` | ✓ | - |
| `SQLAlchemy` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `else` | `metadata` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `else` | `type_annotation_map` | ✓ | - |
| `reg` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `else` | `reg` | ✓ | - |
| `cls` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |

**Schema: `Base`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `The` | `unknown` | ✓ | - |
| `mappings` | `unknown` | ✓ | - |
| `method` | `unknown` | ✓ | - |
| `When` | `unknown` | ✓ | - |
| `provided` | `unknown` | ✓ | - |
| `registry` | `unknown` | ✓ | - |
| `collection` | `unknown` | ✓ | - |
| `Class` | `unknown` | ✓ | - |
| `In` | `unknown` | ✓ | - |
| `hierarchy` | `unknown` | ✓ | - |
| `when` | `unknown` | ✓ | - |
| `constructor` | `unknown` | ✓ | - |
| `instance` | `unknown` | ✓ | - |
| `super` | `unknown` | ✓ | - |
| `directly` | `unknown` | ✓ | - |
| `method` | `unknown` | ✓ | - |
| `The` | `class` | ✓ | - |
| `Mapped` | `unknown` | ✓ | - |
| `remains` | `unknown` | ✓ | - |
| `Note` | `unknown` | ✓ | - |
| `would` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `cls_dict` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in interfaces.py

- **File**: `venv\Lib\site-packages\sqlalchemy\orm\interfaces.py`
- **Captured**: 4/28/2026, 1:01:05 PM
- **Category**: bugfix
**Summary:** Modified interfaces.py: 1497 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\sqlalchemy\orm\interfaces.py` (+1497 / -0)
**Schema: `SomeMappedClass`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Note` | `unknown` | ✓ | - |
| `simpler` | `unknown` | ✓ | - |
| `_parententity` | `_InternalEntityType[Any]` | ✓ | - |
| `_adapt_to_entity` | `Optional[AliasedInsp[Any]]` | ✓ | - |
| `prop` | `RODescriptorReference[MapperProperty[_T_co]]` | ✓ | - |
| `any_op` | `unknown` | ✓ | - |
| `has_op` | `unknown` | ✓ | - |
| `of_type_op` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in mapper.py

- **File**: `venv\Lib\site-packages\sqlalchemy\orm\mapper.py`
- **Captured**: 4/28/2026, 1:01:03 PM
- **Category**: bugfix
**Summary:** Modified mapper.py: 4445 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\sqlalchemy\orm\mapper.py` (+4445 / -0)
**Schema: `User`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `is_mapper` | `unknown` | ✓ | - |
| `represents_outer_join` | `unknown` | ✓ | - |
| `registry` | `_RegistryType` | ✓ | - |
| `_delete_orphans` | `List[Tuple[str, Type[Any]]]` | ✓ | - |
| `_dependency_processors` | `List[DependencyProcessor]` | ✓ | - |
| `_memoized_values` | `Dict[Any, Callable[[], Any]]` | ✓ | - |
| `_inheriting_mappers` | `util` | ✓ | - |
| `_all_tables` | `Set[TableClause]` | ✓ | - |
| `_polymorphic_attr_key` | `Optional[str]` | ✓ | - |
| `_pks_by_table` | `Dict[FromClause, OrderedSet[ColumnClause[Any]]]` | ✓ | - |
| `_cols_by_table` | `Dict[FromClause, OrderedSet[ColumnElement[Any]]]` | ✓ | - |
| `_props` | `util` | ✓ | - |
| `_init_properties` | `Dict[str, MapperProperty[Any]]` | ✓ | - |
| `_columntoproperty` | `_ColumnMapping` | ✓ | - |
| `_set_polymorphic_identity` | `Optional[Callable[[InstanceState[_O]], None]]` | ✓ | - |
| `_validate_polymorphic_identity` | `Optional[` | ✓ | - |
| `tables` | `Sequence[TableClause]` | ✓ | - |
| `or` | `class` | ✓ | - |
| `is` | `unknown` | ✓ | - |
| `If` | `unknown` | ✓ | - |
| `representing` | `unknown` | ✓ | - |
| `objects` | `unknown` | ✓ | - |
| `This` | `unknown` | ✓ | - |
| `Behavior` | `unknown` | ✓ | - |
| `validators` | `util` | ✓ | - |
| `using` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `mapped` | `unknown` | ✓ | - |
| `always_refresh` | `bool` | ✓ | - |
| `allow_partial_pks` | `bool` | ✓ | - |
| `version_id_col` | `Optional[ColumnElement[Any]]` | ✓ | - |
| `with_polymorphic` | `Optional[` | ✓ | - |
| `version_id_generator` | `Optional[Union[Literal[False], Callable[[Any], Any]]]` | ✓ | - |
| `local_table` | `FromClause` | ✓ | - |
| `Typically` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `selectable` | `unknown` | ✓ | - |
| `managing` | `unknown` | ✓ | - |
| `non` | `unknown` | ✓ | - |
| `as` | `attr` | ✓ | - |
| `this` | `class` | ✓ | - |
| `persist_selectable` | `FromClause` | ✓ | - |
| `is` | `unknown` | ✓ | - |
| `Typically` | `unknown` | ✓ | - |
| `The` | `attr` | ✓ | - |
| `represents` | `unknown` | ✓ | - |
| `scenario` | `unknown` | ✓ | - |
| `alternate` | `unknown` | ✓ | - |
| `will` | `unknown` | ✓ | - |
| `inherits` | `Optional[Mapper[Any]]` | ✓ | - |
| `inherits` | `unknown` | ✓ | - |
| `inherit_condition` | `Optional[ColumnElement[bool]]` | ✓ | - |
| `configured` | `bool` | ✓ | - |
| `This` | `unknown` | ✓ | - |
| `Behavior` | `unknown` | ✓ | - |
| `concrete` | `bool` | ✓ | - |
| `inheritance` | `unknown` | ✓ | - |
| `This` | `unknown` | ✓ | - |
| `Behavior` | `unknown` | ✓ | - |
| `primary_key` | `Tuple[ColumnElement[Any],` | ✓ | - |
| `objects` | `unknown` | ✓ | - |
| `perspective` | `unknown` | ✓ | - |
| `This` | `unknown` | ✓ | - |
| `In` | `unknown` | ✓ | - |
| `primary` | `unknown` | ✓ | - |
| `tables` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `collection` | `unknown` | ✓ | - |
| `features` | `unknown` | ✓ | - |
| `This` | `unknown` | ✓ | - |
| `Behavior` | `unknown` | ✓ | - |
| `and` | `unknown` | ✓ | - |
| `This` | `unknown` | ✓ | - |
| `Behavior` | `unknown` | ✓ | - |
| `single` | `bool` | ✓ | - |
| `inheritance` | `unknown` | ✓ | - |
| `This` | `unknown` | ✓ | - |
| `Behavior` | `unknown` | ✓ | - |
| `non_primary` | `bool` | ✓ | - |
| `mapper` | `unknown` | ✓ | - |
| `persistence` | `unknown` | ✓ | - |
| `This` | `unknown` | ✓ | - |
| `Behavior` | `unknown` | ✓ | - |
| `polymorphic_on` | `Optional[KeyedColumnElement[Any]]` | ✓ | - |
| `for` | `unknown` | ✓ | - |
| `This` | `unknown` | ✓ | - |
| `may` | `unknown` | ✓ | - |
| `This` | `unknown` | ✓ | - |
| `Behavior` | `unknown` | ✓ | - |
| `polymorphic_map` | `Dict[Any, Mapper[Any]]` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `type` | `unknown` | ✓ | - |
| `An` | `unknown` | ✓ | - |
| `polymorphic` | `unknown` | ✓ | - |
| `result` | `unknown` | ✓ | - |
| `This` | `unknown` | ✓ | - |
| `Behavior` | `unknown` | ✓ | - |
| `polymorphic_identity` | `Optional[Any]` | ✓ | - |
| `Used` | `unknown` | ✓ | - |
| `comparable` | `unknown` | ✓ | - |
| `This` | `unknown` | ✓ | - |
| `Behavior` | `unknown` | ✓ | - |
| `base_mapper` | `Mapper[Any]` | ✓ | - |
| `In` | `unknown` | ✓ | - |
| `the` | `class` | ✓ | - |
| `objects` | `unknown` | ✓ | - |
| `This` | `unknown` | ✓ | - |
| `Behavior` | `unknown` | ✓ | - |
| `columns` | `ReadOnlyColumnCollection[str, Column[Any]]` | ✓ | - |
| `objects` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `any` | `class` | ✓ | - |
| `except` | `unknown` | ✓ | - |
| `this` | `unknown` | ✓ | - |
| `by` | `func` | ✓ | - |
| `This` | `unknown` | ✓ | - |
| `Behavior` | `unknown` | ✓ | - |
| `c` | `ReadOnlyColumnCollection[str, Column[Any]]` | ✓ | - |
| `_validate_polymorphic_identity` | `unknown` | ✓ | - |
| `with_polymorphic_mappers` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in query.py

- **File**: `venv\Lib\site-packages\sqlalchemy\orm\query.py`
- **Captured**: 4/28/2026, 1:01:02 PM
- **Category**: bugfix
**Summary:** Modified query.py: 3467 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\sqlalchemy\orm\query.py` (+3467 / -0)
**Schema: `Part`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `apply_labels` | `unknown` | ✓ | - |
| `_values` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modeling_patchtsmixer.py

- **File**: `venv\Lib\site-packages\transformers\models\patchtsmixer\modeling_patchtsmixer.py`
- **Captured**: 4/28/2026, 1:00:57 PM
- **Category**: bugfix
**Summary:** Modified modeling_patchtsmixer.py: 2122 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\patchtsmixer\modeling_patchtsmixer.py` (+2122 / -0)
**Schema: `PatchTSMixerPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `PatchTSMixerConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `main_input_name` | `unknown` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |

**Schema: `PatchTSMixerEncoderOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `last_hidden_state` | `unknown` | ✓ | - |
| `hidden_states` | `unknown` | ✓ | - |
| `last_hidden_state` | `torch` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |

**Schema: `PatchTSMixerEncoder`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Encoder` | `unknown` | ✓ | - |
| `Args` | `config` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `Base` | `unknown` | ✓ | - |

**Schema: `PatchTSMixerModelOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `last_hidden_state` | `unknown` | ✓ | - |
| `hidden_states` | `unknown` | ✓ | - |
| `patch_input` | `unknown` | ✓ | - |
| `mask` | `unknown` | ✓ | - |
| `loc` | `unknown` | ✓ | - |
| `scale` | `unknown` | ✓ | - |
| `last_hidden_state` | `torch` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `patch_input` | `torch` | ✓ | - |
| `mask` | `torch` | ✓ | - |
| `loc` | `torch` | ✓ | - |
| `scale` | `torch` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |

**Schema: `PatchTSMixerModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `custom_intro` | `unknown` | ✓ | - |
| `Output` | `unknown` | ✓ | - |

**Schema: `PatchTSMixerForPreTrainingOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `loss` | `unknown` | ✓ | - |
| `prediction_outputs` | `unknown` | ✓ | - |
| `last_hidden_state` | `unknown` | ✓ | - |
| `hidden_states` | `unknown` | ✓ | - |
| `loss` | `torch` | ✓ | - |
| `prediction_outputs` | `torch` | ✓ | - |
| `last_hidden_state` | `torch` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |

**Schema: `PatchTSMixerForPretraining`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `custom_intro` | `unknown` | ✓ | - |
| `Output` | `unknown` | ✓ | - |

**Schema: `PatchTSMixerForPredictionOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `loss` | `unknown` | ✓ | - |
| `prediction_outputs` | `unknown` | ✓ | - |
| `last_hidden_state` | `unknown` | ✓ | - |
| `hidden_states` | `unknown` | ✓ | - |
| `loc` | `unknown` | ✓ | - |
| `scale` | `unknown` | ✓ | - |
| `loss` | `torch` | ✓ | - |
| `prediction_outputs` | `torch` | ✓ | - |
| `last_hidden_state` | `torch` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `loc` | `torch` | ✓ | - |
| `scale` | `torch` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `Base` | `unknown` | ✓ | - |
| `distribution` | `unknown` | ✓ | - |

**Schema: `SamplePatchTSMixerPredictionOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `sequences` | `unknown` | ✓ | - |
| `sequences` | `torch` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `Base` | `unknown` | ✓ | - |
| `distribution` | `unknown` | ✓ | - |

**Schema: `SamplePatchTSMixerRegressionOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `sequences` | `unknown` | ✓ | - |
| `sequences` | `torch` | ✓ | - |
| `Computes` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `Computes` | `unknown` | ✓ | - |
| `meaning` | `unknown` | ✓ | - |
| `Args` | `input_tensor` | ✓ | - |
| `Returns` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `else` | `return input_tensor` | ✓ | - |

**Schema: `PatchTSMixerForPrediction`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `Args` | `config` | ✓ | - |
| `Returns` | `unknown` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `Output` | `unknown` | ✓ | - |

**Schema: `PatchTSMixerForTimeSeriesClassificationOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `loss` | `unknown` | ✓ | - |
| `prediction_outputs` | `unknown` | ✓ | - |
| `last_hidden_state` | `unknown` | ✓ | - |
| `hidden_states` | `unknown` | ✓ | - |
| `loss` | `torch` | ✓ | - |
| `prediction_outputs` | `torch` | ✓ | - |
| `last_hidden_state` | `torch` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |

**Schema: `PatchTSMixerForTimeSeriesClassification`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `Args` | `config` | ✓ | - |
| `Returns` | `unknown` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `Output` | `unknown` | ✓ | - |

**Schema: `PatchTSMixerForRegressionOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `loss` | `unknown` | ✓ | - |
| `regression_outputs` | `unknown` | ✓ | - |
| `last_hidden_state` | `unknown` | ✓ | - |
| `hidden_states` | `unknown` | ✓ | - |
| `loss` | `torch` | ✓ | - |
| `regression_outputs` | `torch` | ✓ | - |
| `last_hidden_state` | `torch` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |

### [New] [bugfix] Changes in modeling_patchtst.py

- **File**: `venv\Lib\site-packages\transformers\models\patchtst\modeling_patchtst.py`
- **Captured**: 4/28/2026, 1:00:54 PM
- **Category**: bugfix
**Summary:** Modified modeling_patchtst.py: 1974 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\patchtst\modeling_patchtst.py` (+1974 / -0)
**Schema: `PatchTSTPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `PatchTSTConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `main_input_name` | `unknown` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `_supports_flex_attn` | `unknown` | ✓ | - |

**Schema: `PatchTSTEncoder`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `PatchTST` | `unknown` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `Base` | `unknown` | ✓ | - |

**Schema: `PatchTSTModelOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `last_hidden_state` | `unknown` | ✓ | - |
| `hidden_states` | `unknown` | ✓ | - |
| `mask` | `unknown` | ✓ | - |
| `loc` | `unknown` | ✓ | - |
| `scale` | `unknown` | ✓ | - |
| `patch_input` | `unknown` | ✓ | - |
| `last_hidden_state` | `torch` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[torch` | ✓ | - |
| `mask` | `torch` | ✓ | - |
| `loc` | `torch` | ✓ | - |
| `scale` | `torch` | ✓ | - |
| `patch_input` | `torch` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `Output` | `unknown` | ✓ | - |

**Schema: `PatchTSTForPretrainingOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `loss` | `unknown` | ✓ | - |
| `prediction_output` | `unknown` | ✓ | - |
| `loss` | `torch` | ✓ | - |
| `prediction_output` | `torch` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[torch` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `Output` | `unknown` | ✓ | - |

**Schema: `PatchTSTForRegressionOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `loss` | `unknown` | ✓ | - |
| `regression_outputs` | `unknown` | ✓ | - |
| `loss` | `torch` | ✓ | - |
| `regression_outputs` | `torch` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[torch` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `Output` | `unknown` | ✓ | - |

**Schema: `PatchTSTForPredictionOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `loss` | `unknown` | ✓ | - |
| `prediction_outputs` | `unknown` | ✓ | - |
| `attentions` | `unknown` | ✓ | - |
| `loc` | `unknown` | ✓ | - |
| `scale` | `unknown` | ✓ | - |
| `loss` | `torch` | ✓ | - |
| `prediction_outputs` | `torch` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[torch` | ✓ | - |
| `loc` | `torch` | ✓ | - |
| `scale` | `torch` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `Output` | `unknown` | ✓ | - |

**Schema: `PatchTSTForClassificationOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `loss` | `unknown` | ✓ | - |
| `prediction_logits` | `unknown` | ✓ | - |
| `loss` | `torch` | ✓ | - |
| `prediction_logits` | `torch` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[torch` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `Base` | `unknown` | ✓ | - |
| `distribution` | `unknown` | ✓ | - |

**Schema: `SamplePatchTSTOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `sequences` | `unknown` | ✓ | - |
| `sequences` | `torch` | ✓ | - |
| `Computes` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `Computes` | `unknown` | ✓ | - |
| `meaning` | `unknown` | ✓ | - |
| `Args` | `input_tensor` | ✓ | - |
| `Returns` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `else` | `return input_tensor` | ✓ | - |

**Schema: `PatchTSTForClassification`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `custom_intro` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in _collections.py

- **File**: `venv\Lib\site-packages\sqlalchemy\util\_collections.py`
- **Captured**: 4/28/2026, 1:00:50 PM
- **Category**: bugfix
**Summary:** Modified _collections.py: 713 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\sqlalchemy\util\_collections.py` (+713 / -0)
**Schema: `User`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `But` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `all` | `unknown` | ✓ | - |
| `is` | `unknown` | ✓ | - |
| `Background` | `unknown` | ✓ | - |
| `https` | `unknown` | ✓ | - |
| `overlap` | `unknown` | ✓ | - |
| `result` | `unknown` | ✓ | - |
| `current` | `unknown` | ✓ | - |
| `while` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `elif` | `unknown` | ✓ | - |
| `else` | `return immutabledict` | ✓ | - |
| `EMPTY_DICT` | `immutabledict[Any, Any]` | ✓ | - |

**Schema: `FacadeDict`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_DT` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modeling_pegasus.py

- **File**: `venv\Lib\site-packages\transformers\models\pegasus\modeling_pegasus.py`
- **Captured**: 4/28/2026, 1:00:49 PM
- **Category**: bugfix
**Summary:** Modified modeling_pegasus.py: 1133 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\pegasus\modeling_pegasus.py` (+1133 / -0)
**Schema: `PegasusPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `PegasusConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `_supports_flex_attn` | `unknown` | ✓ | - |
| `_can_compile_fullgraph` | `unknown` | ✓ | - |

**Schema: `PegasusEncoder`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Transformer` | `unknown` | ✓ | - |
| `Args` | `config` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |

**Schema: `PegasusDecoder`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Transformer` | `unknown` | ✓ | - |
| `Args` | `config` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |

**Schema: `PegasusModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_tied_weights_keys` | `unknown` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |

**Schema: `PegasusForConditionalGeneration`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `base_model_prefix` | `unknown` | ✓ | - |
| `_keys_to_ignore_on_load_missing` | `unknown` | ✓ | - |
| `_tied_weights_keys` | `unknown` | ✓ | - |

**Schema: `PegasusDecoderWrapper`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `This` | `unknown` | ✓ | - |
| `used` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modeling_pegasus_x.py

- **File**: `venv\Lib\site-packages\transformers\models\pegasus_x\modeling_pegasus_x.py`
- **Captured**: 4/28/2026, 1:00:41 PM
- **Category**: bugfix
**Summary:** Modified modeling_pegasus_x.py: 1353 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\pegasus_x\modeling_pegasus_x.py` (+1353 / -0)
**Schema: `PegasusXPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `PegasusXConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `_supports_flex_attn` | `unknown` | ✓ | - |
| `_can_compile_fullgraph` | `unknown` | ✓ | - |

**Schema: `PegasusXEncoder`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_can_record_outputs` | `unknown` | ✓ | - |
| `Transformer` | `unknown` | ✓ | - |
| `Args` | `config` | ✓ | - |

**Schema: `PegasusXDecoder`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Transformer` | `unknown` | ✓ | - |
| `Args` | `config` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |

**Schema: `PegasusXModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_tied_weights_keys` | `unknown` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |

**Schema: `PegasusXForConditionalGeneration`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `base_model_prefix` | `unknown` | ✓ | - |
| `_tied_weights_keys` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modeling_perceiver.py

- **File**: `venv\Lib\site-packages\transformers\models\perceiver\modeling_perceiver.py`
- **Captured**: 4/28/2026, 1:00:37 PM
- **Category**: bugfix
**Summary:** Modified modeling_perceiver.py: 3303 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\perceiver\modeling_perceiver.py` (+3303 / -0)
**Schema: `PerceiverModelOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `logits` | `unknown` | ✓ | - |
| `logits` | `torch` | ✓ | - |
| `last_hidden_state` | `torch` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[torch` | ✓ | - |
| `cross_attentions` | `tuple[torch` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `Base` | `unknown` | ✓ | - |

**Schema: `PerceiverDecoderOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `logits` | `unknown` | ✓ | - |
| `logits` | `torch` | ✓ | - |
| `cross_attentions` | `tuple[torch` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `Base` | `unknown` | ✓ | - |

**Schema: `PerceiverMaskedLMOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `loss` | `unknown` | ✓ | - |
| `logits` | `unknown` | ✓ | - |
| `loss` | `torch` | ✓ | - |
| `logits` | `torch` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[torch` | ✓ | - |
| `cross_attentions` | `tuple[torch` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `Base` | `unknown` | ✓ | - |
| `autoencoding` | `unknown` | ✓ | - |

**Schema: `PerceiverClassifierOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `loss` | `unknown` | ✓ | - |
| `logits` | `unknown` | ✓ | - |
| `loss` | `torch` | ✓ | - |
| `logits` | `torch` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[torch` | ✓ | - |
| `cross_attentions` | `tuple[torch` | ✓ | - |

**Schema: `PerceiverPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `PerceiverConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `main_input_name` | `unknown` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |

**Schema: `PerceiverModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `custom_intro` | `unknown` | ✓ | - |
| `Example` | `unknown` | ✓ | - |

**Schema: `PerceiverForMaskedLM`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `custom_intro` | `unknown` | ✓ | - |
| `Example` | `unknown` | ✓ | - |

**Schema: `PerceiverForSequenceClassification`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `custom_intro` | `unknown` | ✓ | - |
| `This` | `unknown` | ✓ | - |
| `the` | `unknown` | ✓ | - |

**Schema: `PerceiverForImageClassificationLearned`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `custom_intro` | `unknown` | ✓ | - |
| `This` | `unknown` | ✓ | - |
| `79` | `unknown` | ✓ | - |

**Schema: `PerceiverForImageClassificationFourier`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `custom_intro` | `unknown` | ✓ | - |
| `This` | `unknown` | ✓ | - |
| `of` | `unknown` | ✓ | - |

**Schema: `PerceiverForImageClassificationConvProcessing`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `custom_intro` | `unknown` | ✓ | - |
| `input` | `unknown` | ✓ | - |
| `representation` | `unknown` | ✓ | - |
| `As` | `unknown` | ✓ | - |
| `of` | `unknown` | ✓ | - |
| `using` | `unknown` | ✓ | - |

**Schema: `PerceiverForOpticalFlow`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `custom_intro` | `unknown` | ✓ | - |
| `preprocess` | `unknown` | ✓ | - |
| `preprocess` | `unknown` | ✓ | - |
| `each` | `unknown` | ✓ | - |
| `the` | `unknown` | ✓ | - |
| `created` | `unknown` | ✓ | - |
| `computationally` | `unknown` | ✓ | - |
| `representation` | `unknown` | ✓ | - |
| `input` | `unknown` | ✓ | - |
| `modalities` | `unknown` | ✓ | - |
| `is` | `unknown` | ✓ | - |
| `Finally` | `unknown` | ✓ | - |
| `actual` | `unknown` | ✓ | - |
| `postprocessor` | `unknown` | ✓ | - |
| `Note` | `unknown` | ✓ | - |

**Schema: `PerceiverForMultimodalAutoencoding`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `position_encoding_type` | `unknown` | ✓ | - |
| `out_channels` | `unknown` | ✓ | - |
| `project_pos_dim` | `unknown` | ✓ | - |
| `trainable_position_encoding_kwargs` | `unknown` | ✓ | - |
| `fourier_position_encoding_kwargs` | `unknown` | ✓ | - |
| `Builds` | `unknown` | ✓ | - |
| `Args` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `elif` | `unknown` | ✓ | - |
| `else` | `raise ValueError` | ✓ | - |
| `positions_projection` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |

### [bugfix] Changes in index-IVqHpmXj.js

- **File**: `frontend\dist\assets\index-IVqHpmXj.js`
- **Captured**: 4/28/2026, 1:00:34 PM
- **Category**: bugfix
**Summary:** Modified index-IVqHpmXj.js: 31 lines added, 0 lines removed.
**Files Modified:**
  - `frontend\dist\assets\index-IVqHpmXj.js` (+31 / -0)

### [bugfix] Changes in Workflows-CO3Czt_R.js

- **File**: `frontend\dist\assets\Workflows-CO3Czt_R.js`
- **Captured**: 4/28/2026, 1:00:32 PM
- **Category**: bugfix
**Summary:** Modified Workflows-CO3Czt_R.js: 7 lines added, 0 lines removed.
**Files Modified:**
  - `frontend\dist\assets\Workflows-CO3Czt_R.js` (+7 / -0)

### [New] [bugfix] Changes in modeling_perception_lm.py

- **File**: `venv\Lib\site-packages\transformers\models\perception_lm\modeling_perception_lm.py`
- **Captured**: 4/28/2026, 1:00:26 PM
- **Category**: bugfix
**Summary:** Modified modeling_perception_lm.py: 457 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\perception_lm\modeling_perception_lm.py` (+457 / -0)
**Schema: `PerceptionLMPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `PerceptionLMConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_skip_keys_device_placement` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `_can_compile_fullgraph` | `unknown` | ✓ | - |
| `_supports_flex_attn` | `unknown` | ✓ | - |
| `_supports_attention_backend` | `unknown` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `Base` | `unknown` | ✓ | - |

**Schema: `PerceptionLMModelOutputWithPast`** (pydantic)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `past_key_values` | `unknown` | ✓ | - |
| `image_hidden_states` | `unknown` | ✓ | - |
| `video_hidden_states` | `unknown` | ✓ | - |
| `image_hidden_states` | `torch` | ✓ | - |
| `video_hidden_states` | `torch` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `Base` | `unknown` | ✓ | - |

**Schema: `PerceptionLMCausalLMOutputWithPast`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `loss` | `unknown` | ✓ | - |
| `logits` | `unknown` | ✓ | - |
| `past_key_values` | `unknown` | ✓ | - |
| `image_hidden_states` | `unknown` | ✓ | - |
| `video_hidden_states` | `unknown` | ✓ | - |
| `loss` | `torch` | ✓ | - |
| `logits` | `torch` | ✓ | - |
| `past_key_values` | `Cache` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[torch` | ✓ | - |
| `image_hidden_states` | `torch` | ✓ | - |
| `video_hidden_states` | `torch` | ✓ | - |

### [New] [bugfix] Changes in modular_perception_lm.py

- **File**: `venv\Lib\site-packages\transformers\models\perception_lm\modular_perception_lm.py`
- **Captured**: 4/28/2026, 1:00:24 PM
- **Category**: bugfix
**Summary:** Modified modular_perception_lm.py: 415 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\perception_lm\modular_perception_lm.py` (+415 / -0)
**Schema: `PerceptionLMPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `base_model_prefix` | `unknown` | ✓ | - |

**Schema: `PerceptionLMModelOutputWithPast`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `past_key_values` | `unknown` | ✓ | - |
| `image_hidden_states` | `unknown` | ✓ | - |
| `video_hidden_states` | `unknown` | ✓ | - |
| `video_hidden_states` | `torch` | ✓ | - |

### [New] [bugfix] Changes in authentication.py

- **File**: `venv\Lib\site-packages\starlette\authentication.py`
- **Captured**: 4/28/2026, 1:00:20 PM
- **Category**: bugfix
**Summary:** Modified authentication.py: 143 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\starlette\authentication.py` (+143 / -0)

### [New] [bugfix] Changes in exceptions.py

- **File**: `venv\Lib\site-packages\starlette\middleware\exceptions.py`
- **Captured**: 4/28/2026, 1:00:18 PM
- **Category**: bugfix
**Summary:** Modified exceptions.py: 74 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\starlette\middleware\exceptions.py` (+74 / -0)

### [New] [bugfix] Changes in exponential.py

- **File**: `venv\Lib\site-packages\sympy\functions\elementary\exponential.py`
- **Captured**: 4/28/2026, 1:00:15 PM
- **Category**: bugfix
**Summary:** Modified exponential.py: 1287 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\sympy\functions\elementary\exponential.py` (+1287 / -0)
**Schema: `exp_polar`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `Represent` | `unknown` | ✓ | - |
| `Explanation` | `unknown` | ✓ | - |
| `the` | `unknown` | ✓ | - |
| `Examples` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `1` | `unknown` | ✓ | - |
| `exp_polar` | `unknown` | ✓ | - |
| `apart` | `unknown` | ✓ | - |
| `exp_polar` | `unknown` | ✓ | - |
| `See` | `unknown` | ✓ | - |
| `sympy` | `unknown` | ✓ | - |
| `polar_lift` | `unknown` | ✓ | - |
| `principal_branch` | `unknown` | ✓ | - |
| `is_polar` | `unknown` | ✓ | - |
| `is_comparable` | `unknown` | ✓ | - |

**Schema: `exp`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `The` | `unknown` | ✓ | - |
| `Examples` | `unknown` | ✓ | - |
| `exp` | `unknown` | ✓ | - |
| `exp` | `unknown` | ✓ | - |
| `Parameters` | `unknown` | ✓ | - |
| `arg` | `Expr` | ✓ | - |
| `See` | `unknown` | ✓ | - |
| `log` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in miscellaneous.py

- **File**: `venv\Lib\site-packages\sympy\functions\elementary\miscellaneous.py`
- **Captured**: 4/28/2026, 1:00:14 PM
- **Category**: bugfix
**Summary:** Modified miscellaneous.py: 916 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\sympy\functions\elementary\miscellaneous.py` (+916 / -0)
**Schema: `Max`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `Return` | `unknown` | ✓ | - |
| `When` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `When` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `In` | `unknown` | ✓ | - |
| `is` | `unknown` | ✓ | - |
| `than` | `unknown` | ✓ | - |
| `If` | `unknown` | ✓ | - |
| `evaluated` | `unknown` | ✓ | - |
| `Assumptions` | `unknown` | ✓ | - |
| `Also` | `unknown` | ✓ | - |
| `It` | `unknown` | ✓ | - |
| `with` | `unknown` | ✓ | - |
| `Examples` | `unknown` | ✓ | - |
| `Max` | `unknown` | ✓ | - |
| `3` | `unknown` | ✓ | - |
| `p` | `unknown` | ✓ | - |
| `Max` | `unknown` | ✓ | - |
| `True` | `unknown` | ✓ | - |
| `Max` | `unknown` | ✓ | - |
| `Max` | `unknown` | ✓ | - |
| `oo` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `directed` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `in` | `unknown` | ✓ | - |
| `If` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `with` | `unknown` | ✓ | - |
| `each` | `unknown` | ✓ | - |
| `symbol` | `unknown` | ✓ | - |
| `Also` | `unknown` | ✓ | - |
| `and` | `unknown` | ✓ | - |
| `For` | `unknown` | ✓ | - |
| `and` | `unknown` | ✓ | - |
| `Assumption` | `unknown` | ✓ | - |
| `References` | `unknown` | ✓ | - |
| `See` | `unknown` | ✓ | - |
| `Min` | `find minimum values` | ✓ | - |
| `zero` | `unknown` | ✓ | - |
| `identity` | `unknown` | ✓ | - |

**Schema: `Min`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Return` | `unknown` | ✓ | - |
| `It` | `unknown` | ✓ | - |
| `with` | `unknown` | ✓ | - |
| `Examples` | `unknown` | ✓ | - |
| `Min` | `unknown` | ✓ | - |
| `Min` | `unknown` | ✓ | - |
| `Min` | `unknown` | ✓ | - |
| `See` | `unknown` | ✓ | - |
| `Max` | `find maximum values` | ✓ | - |
| `zero` | `unknown` | ✓ | - |
| `identity` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modeling_persimmon.py

- **File**: `venv\Lib\site-packages\transformers\models\persimmon\modeling_persimmon.py`
- **Captured**: 4/28/2026, 1:00:11 PM
- **Category**: bugfix
**Summary:** Modified modeling_persimmon.py: 554 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\persimmon\modeling_persimmon.py` (+554 / -0)
**Schema: `PersimmonPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `PersimmonConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_skip_keys_device_placement` | `unknown` | ✓ | - |
| `_can_compile_fullgraph` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_supports_attention_backend` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |

**Schema: `PersimmonModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Transformer` | `unknown` | ✓ | - |
| `Args` | `config` | ✓ | - |

**Schema: `PersimmonForCausalLM`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_tied_weights_keys` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in routing.py

- **File**: `venv\Lib\site-packages\starlette\routing.py`
- **Captured**: 4/28/2026, 1:00:08 PM
- **Category**: bugfix
**Summary:** Modified routing.py: 748 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\starlette\routing.py` (+748 / -0)
**Schema: `Route`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `async` | `unknown` | ✓ | - |

**Schema: `WebSocketRoute`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `async` | `unknown` | ✓ | - |

**Schema: `Mount`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `async` | `unknown` | ✓ | - |

**Schema: `Host`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `async` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modeling_pe_audio.py

- **File**: `venv\Lib\site-packages\transformers\models\pe_audio\modeling_pe_audio.py`
- **Captured**: 4/28/2026, 1:00:06 PM
- **Category**: bugfix
**Summary:** Modified modeling_pe_audio.py: 825 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\pe_audio\modeling_pe_audio.py` (+825 / -0)
**Schema: `PeAudioPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `PeAudioConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_skip_keys_device_placement` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `_supports_flex_attn` | `unknown` | ✓ | - |
| `_can_compile_fullgraph` | `unknown` | ✓ | - |
| `_supports_attention_backend` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `Class` | `unknown` | ✓ | - |

**Schema: `PeAudioEncoderOutput`** (pydantic)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `codec_features` | `torch` | ✓ | - |
| `output_mask` | `tuple[torch` | ✓ | - |

**Schema: `PeAudioEncoder`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `PeAudioEncoderConfig` | ✓ | - |
| `main_input_name` | `unknown` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |

**Schema: `PeAudioOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `loss` | `torch` | ✓ | - |
| `logits_audio_text` | `torch` | ✓ | - |
| `text_audio_embeds` | `torch` | ✓ | - |
| `audio_embeds` | `torch` | ✓ | - |
| `text_outputs` | `BaseModelOutputWithPooling` | ✓ | - |
| `audio_outputs` | `BaseModelOutputWithPooling` | ✓ | - |

### [New] [bugfix] Changes in modular_pe_audio.py

- **File**: `venv\Lib\site-packages\transformers\models\pe_audio\modular_pe_audio.py`
- **Captured**: 4/28/2026, 1:00:05 PM
- **Category**: bugfix
**Summary:** Modified modular_pe_audio.py: 307 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\pe_audio\modular_pe_audio.py` (+307 / -0)
**Schema: `PeAudioPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `base_model_prefix` | `unknown` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `Class` | `unknown` | ✓ | - |

**Schema: `PeAudioEncoderOutput`** (pydantic)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `codec_features` | `torch` | ✓ | - |
| `output_mask` | `tuple[torch` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |

**Schema: `PeAudioOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `loss` | `torch` | ✓ | - |
| `logits_audio_text` | `torch` | ✓ | - |
| `text_audio_embeds` | `torch` | ✓ | - |
| `audio_embeds` | `torch` | ✓ | - |
| `text_outputs` | `BaseModelOutputWithPooling` | ✓ | - |
| `audio_outputs` | `BaseModelOutputWithPooling` | ✓ | - |

### [New] [bugfix] Changes in ast.py

- **File**: `venv\Lib\site-packages\sympy\codegen\ast.py`
- **Captured**: 4/28/2026, 1:00:03 PM
- **Category**: bugfix
**Summary:** Modified ast.py: 1907 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\sympy\codegen\ast.py` (+1907 / -0)
**Schema: `Assignment`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Represents` | `unknown` | ✓ | - |
| `Parameters` | `unknown` | ✓ | - |
| `lhs` | `Expr` | ✓ | - |
| `rhs` | `Expr` | ✓ | - |
| `Examples` | `unknown` | ✓ | - |
| `Assignment` | `unknown` | ✓ | - |
| `Assignment` | `unknown` | ✓ | - |
| `Assignment` | `unknown` | ✓ | - |
| `Assignment` | `unknown` | ✓ | - |
| `op` | `unknown` | ✓ | - |

**Schema: `AugmentedAssignment`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Base` | `unknown` | ✓ | - |
| `Attributes` | `unknown` | ✓ | - |
| `binop` | `str` | ✓ | - |
| `binop` | `str` | ✓ | - |

**Schema: `_SizedIntType`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_fields` | `unknown` | ✓ | - |
| `_construct_nbits` | `unknown` | ✓ | - |

**Schema: `FloatType`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Base` | `unknown` | ✓ | - |
| `Parameters` | `unknown` | ✓ | - |
| `name` | `str` | ✓ | - |
| `nbits` | `integer` | ✓ | - |
| `nmant` | `integer` | ✓ | - |
| `nexp` | `integer` | ✓ | - |
| `Examples` | `unknown` | ✓ | - |
| `65504` | `unknown` | ✓ | - |
| `True` | `unknown` | ✓ | - |
| `True` | `unknown` | ✓ | - |
| `True` | `unknown` | ✓ | - |
| `True` | `unknown` | ✓ | - |
| `1` | `unknown` | ✓ | - |
| `Traceback` | `unknown` | ✓ | - |
| `ValueError` | `Maximum value for data type smaller than new value` | ✓ | - |
| `_fields` | `unknown` | ✓ | - |
| `_construct_nbits` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in polyerrors.py

- **File**: `venv\Lib\site-packages\sympy\polys\polyerrors.py`
- **Captured**: 4/28/2026, 12:59:59 PM
- **Category**: bugfix
**Summary:** Modified polyerrors.py: 184 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\sympy\polys\polyerrors.py` (+184 / -0)
**Schema: `HeuristicGCDFailed`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `pass` | `unknown` | ✓ | - |

**Schema: `ModularGCDFailed`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `pass` | `unknown` | ✓ | - |

**Schema: `HomomorphismFailed`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `pass` | `unknown` | ✓ | - |

**Schema: `IsomorphismFailed`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `pass` | `unknown` | ✓ | - |

**Schema: `ExtraneousFactors`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `pass` | `unknown` | ✓ | - |

**Schema: `EvaluationFailed`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `pass` | `unknown` | ✓ | - |

**Schema: `RefinementFailed`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `pass` | `unknown` | ✓ | - |

**Schema: `CoercionFailed`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `pass` | `unknown` | ✓ | - |

**Schema: `NotInvertible`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `pass` | `unknown` | ✓ | - |

**Schema: `NotReversible`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `pass` | `unknown` | ✓ | - |

**Schema: `NotAlgebraic`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `pass` | `unknown` | ✓ | - |

**Schema: `DomainError`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `pass` | `unknown` | ✓ | - |

**Schema: `PolynomialError`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `pass` | `unknown` | ✓ | - |

**Schema: `UnificationFailed`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `pass` | `unknown` | ✓ | - |

**Schema: `GeneratorsError`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `pass` | `unknown` | ✓ | - |

**Schema: `OptionError`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `pass` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in test_decomp_update.py

- **File**: `venv\Lib\site-packages\scipy\linalg\tests\test_decomp_update.py`
- **Captured**: 4/28/2026, 12:59:51 PM
- **Category**: bugfix
**Summary:** Modified test_decomp_update.py: 1701 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\scipy\linalg\tests\test_decomp_update.py` (+1701 / -0)
**Schema: `TestQRdelete_f`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `dtype` | `unknown` | ✓ | - |

**Schema: `TestQRdelete_F`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `dtype` | `unknown` | ✓ | - |

**Schema: `TestQRdelete_d`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `dtype` | `unknown` | ✓ | - |

**Schema: `TestQRdelete_D`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `dtype` | `unknown` | ✓ | - |

**Schema: `TestQRinsert_f`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `dtype` | `unknown` | ✓ | - |

**Schema: `TestQRinsert_F`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `dtype` | `unknown` | ✓ | - |

**Schema: `TestQRinsert_d`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `dtype` | `unknown` | ✓ | - |

**Schema: `TestQRinsert_D`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `dtype` | `unknown` | ✓ | - |

**Schema: `TestQRupdate_f`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `dtype` | `unknown` | ✓ | - |

**Schema: `TestQRupdate_F`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `dtype` | `unknown` | ✓ | - |

**Schema: `TestQRupdate_d`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `dtype` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in test_fblas.py

- **File**: `venv\Lib\site-packages\scipy\linalg\tests\test_fblas.py`
- **Captured**: 4/28/2026, 12:59:49 PM
- **Category**: bugfix
**Summary:** Modified test_fblas.py: 603 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\scipy\linalg\tests\test_fblas.py` (+603 / -0)
**Schema: `TestDaxpy`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `blas_func` | `unknown` | ✓ | - |
| `dtype` | `unknown` | ✓ | - |
| `try` | `class TestCaxpy` | ✓ | - |

**Schema: `TestZaxpy`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `blas_func` | `unknown` | ✓ | - |
| `dtype` | `unknown` | ✓ | - |

**Schema: `TestDscal`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `blas_func` | `unknown` | ✓ | - |
| `dtype` | `unknown` | ✓ | - |
| `try` | `class TestCscal` | ✓ | - |

**Schema: `TestZscal`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `blas_func` | `unknown` | ✓ | - |
| `dtype` | `unknown` | ✓ | - |

**Schema: `TestDcopy`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `blas_func` | `unknown` | ✓ | - |
| `dtype` | `unknown` | ✓ | - |
| `try` | `class TestCcopy` | ✓ | - |

**Schema: `TestZcopy`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `blas_func` | `unknown` | ✓ | - |
| `dtype` | `unknown` | ✓ | - |

**Schema: `TestDswap`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `blas_func` | `unknown` | ✓ | - |
| `dtype` | `unknown` | ✓ | - |
| `try` | `class TestCswap` | ✓ | - |

**Schema: `TestZswap`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `blas_func` | `unknown` | ✓ | - |
| `dtype` | `unknown` | ✓ | - |

**Schema: `TestDgemv`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `blas_func` | `unknown` | ✓ | - |
| `dtype` | `unknown` | ✓ | - |
| `try` | `class TestCgemv` | ✓ | - |

**Schema: `TestZgemv`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `blas_func` | `unknown` | ✓ | - |
| `dtype` | `unknown` | ✓ | - |

**Schema: `TestSger`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `blas_func` | `unknown` | ✓ | - |
| `dtype` | `unknown` | ✓ | - |

**Schema: `TestDger`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `blas_func` | `unknown` | ✓ | - |
| `dtype` | `unknown` | ✓ | - |

**Schema: `TestCgeru`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `blas_func` | `unknown` | ✓ | - |
| `dtype` | `unknown` | ✓ | - |

**Schema: `TestZgeru`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `blas_func` | `unknown` | ✓ | - |
| `dtype` | `unknown` | ✓ | - |

**Schema: `TestCgerc`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `blas_func` | `unknown` | ✓ | - |
| `dtype` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in snowflake_connection.py

- **File**: `venv\Lib\site-packages\streamlit\connections\snowflake_connection.py`
- **Captured**: 4/28/2026, 12:59:46 PM
- **Category**: bugfix
**Summary:** Modified snowflake_connection.py: 772 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\streamlit\connections\snowflake_connection.py` (+772 / -0)
**Schema: `BaseSnowflakeConnection`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `This` | `unknown` | ✓ | - |
| `connections` | `unknown` | ✓ | - |
| `information` | `unknown` | ✓ | - |
| `description` | `unknown` | ✓ | - |

**Schema: `SnowflakeConnection`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `For` | `unknown` | ✓ | - |
| `SnowflakeConnection` | `unknown` | ✓ | - |
| `When` | `unknown` | ✓ | - |
| `role` | `unknown` | ✓ | - |
| `case` | `unknown` | ✓ | - |
| `for` | `unknown` | ✓ | - |
| `When` | `unknown` | ✓ | - |
| `enabled` | `unknown` | ✓ | - |
| `using` | `unknown` | ✓ | - |
| `to` | `unknown` | ✓ | - |
| `connection` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `can` | `unknown` | ✓ | - |
| `Snowflake` | `unknown` | ✓ | - |
| `Examples` | `unknown` | ✓ | - |
| `You` | `unknown` | ✓ | - |
| `For` | `unknown` | ✓ | - |
| `You` | `unknown` | ✓ | - |
| `keyword` | `unknown` | ✓ | - |
| `don` | `unknown` | ✓ | - |
| `the` | `unknown` | ✓ | - |
| `To` | `unknown` | ✓ | - |
| `for` | `unknown` | ✓ | - |
| `For` | `unknown` | ✓ | - |
| `local` | `unknown` | ✓ | - |
| `Because` | `unknown` | ✓ | - |
| `empty` | `unknown` | ✓ | - |
| `Streamlit` | `unknown` | ✓ | - |
| `Snowflake` | `unknown` | ✓ | - |
| `Snowflake` | `unknown` | ✓ | - |
| `which` | `unknown` | ✓ | - |
| `already` | `unknown` | ✓ | - |
| `the` | `unknown` | ✓ | - |
| `If` | `unknown` | ✓ | - |
| `If` | `unknown` | ✓ | - |
| `will` | `unknown` | ✓ | - |
| `If` | `unknown` | ✓ | - |
| `declare` | `unknown` | ✓ | - |
| `If` | `unknown` | ✓ | - |
| `connection` | `unknown` | ✓ | - |
| `declared` | `unknown` | ✓ | - |
| `You` | `unknown` | ✓ | - |
| `environment` | `unknown` | ✓ | - |
| `Snowflake` | `unknown` | ✓ | - |
| `This` | `unknown` | ✓ | - |
| `Additionally` | `unknown` | ✓ | - |
| `may` | `unknown` | ✓ | - |
| `of` | `unknown` | ✓ | - |
| `If` | `unknown` | ✓ | - |
| `environment` | `unknown` | ✓ | - |
| `connection` | `unknown` | ✓ | - |
| `Snowpark` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in oidc_mixin.py

- **File**: `venv\Lib\site-packages\streamlit\web\server\oidc_mixin.py`
- **Captured**: 4/28/2026, 12:59:42 PM
- **Category**: bugfix
**Summary:** Modified oidc_mixin.py: 139 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\streamlit\web\server\oidc_mixin.py` (+139 / -0)
**Schema: `TornadoOAuth2App`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `client_cls` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in _ode.py

- **File**: `venv\Lib\site-packages\scipy\integrate\_ode.py`
- **Captured**: 4/28/2026, 12:59:37 PM
- **Category**: bugfix
**Summary:** Modified _ode.py: 1410 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\scipy\integrate\_ode.py` (+1410 / -0)
**Schema: `vode`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `runner` | `unknown` | ✓ | - |
| `messages` | `unknown` | ✓ | - |
| `supports_run_relax` | `unknown` | ✓ | - |
| `supports_step` | `unknown` | ✓ | - |

**Schema: `dopri5`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `runner` | `unknown` | ✓ | - |
| `name` | `unknown` | ✓ | - |
| `supports_solout` | `unknown` | ✓ | - |
| `messages` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `IntegratorBase` | `unknown` | ✓ | - |

**Schema: `lsoda`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `runner` | `unknown` | ✓ | - |
| `messages` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modeling_pe_audio_video.py

- **File**: `venv\Lib\site-packages\transformers\models\pe_audio_video\modeling_pe_audio_video.py`
- **Captured**: 4/28/2026, 12:59:33 PM
- **Category**: bugfix
**Summary:** Modified modeling_pe_audio_video.py: 977 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\pe_audio_video\modeling_pe_audio_video.py` (+977 / -0)
**Schema: `PeAudioVideoPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `PeAudioVideoConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_skip_keys_device_placement` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `_supports_flex_attn` | `unknown` | ✓ | - |
| `_can_compile_fullgraph` | `unknown` | ✓ | - |
| `_supports_attention_backend` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `Class` | `unknown` | ✓ | - |

**Schema: `PeAudioVideoEncoderOutput`** (pydantic)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `audio_model_output` | `BaseModelOutputWithPooling` | ✓ | - |
| `video_model_output` | `BaseModelOutputWithPooling` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |

**Schema: `PeAudioVideoEncoder`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `PeAudioVideoEncoderConfig` | ✓ | - |
| `main_input_name` | `unknown` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `Class` | `unknown` | ✓ | - |

**Schema: `PeAudioVideoOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `audio_embeds` | `torch` | ✓ | - |
| `video_embeds` | `torch` | ✓ | - |
| `audio_video_embeds` | `torch` | ✓ | - |
| `text_audio_embeds` | `torch` | ✓ | - |
| `text_video_embeds` | `torch` | ✓ | - |
| `text_audio_video_embeds` | `torch` | ✓ | - |
| `audio_plus_text_embeds` | `torch` | ✓ | - |
| `video_plus_text_embeds` | `torch` | ✓ | - |
| `text_outputs` | `MaskedLMOutput` | ✓ | - |
| `audio_outputs` | `BaseModelOutputWithPooling` | ✓ | - |
| `video_outputs` | `BaseModelOutputWithPooling` | ✓ | - |
| `audio_video_outputs` | `BaseModelOutputWithPooling` | ✓ | - |
| `logits_audio_text` | `torch` | ✓ | - |
| `logits_video_text` | `torch` | ✓ | - |
| `logits_audio_video` | `torch` | ✓ | - |
| `logits_audio_video_text` | `torch` | ✓ | - |
| `logits_audio_plus_text_video` | `torch` | ✓ | - |
| `logits_video_plus_text_audio` | `torch` | ✓ | - |
| `audio_text_loss` | `torch` | ✓ | - |
| `video_text_loss` | `torch` | ✓ | - |
| `audio_video_loss` | `torch` | ✓ | - |
| `audio_video_text_loss` | `torch` | ✓ | - |
| `audio_plus_text_video_loss` | `torch` | ✓ | - |
| `video_plus_text_audio_loss` | `torch` | ✓ | - |
| `loss` | `torch` | ✓ | - |

**Schema: `AudioVideoEmbeddings`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `audio_embeds` | `torch` | ✓ | - |
| `video_embeds` | `torch` | ✓ | - |
| `audio_video_embeds` | `torch` | ✓ | - |

### [New] [bugfix] Changes in modular_pe_audio_video.py

- **File**: `venv\Lib\site-packages\transformers\models\pe_audio_video\modular_pe_audio_video.py`
- **Captured**: 4/28/2026, 12:59:32 PM
- **Category**: bugfix
**Summary:** Modified modular_pe_audio_video.py: 772 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\pe_audio_video\modular_pe_audio_video.py` (+772 / -0)
**Schema: `PeAudioVideoPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `PeAudioVideoConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_skip_keys_device_placement` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `_supports_flex_attn` | `unknown` | ✓ | - |
| `_can_compile_fullgraph` | `unknown` | ✓ | - |
| `_supports_attention_backend` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `Class` | `unknown` | ✓ | - |

**Schema: `PeAudioVideoEncoderOutput`** (pydantic)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `audio_model_output` | `BaseModelOutputWithPooling` | ✓ | - |
| `video_model_output` | `BaseModelOutputWithPooling` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |

**Schema: `PeAudioVideoEncoder`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `PeAudioVideoEncoderConfig` | ✓ | - |
| `main_input_name` | `unknown` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `Class` | `unknown` | ✓ | - |

**Schema: `PeAudioVideoOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `audio_embeds` | `torch` | ✓ | - |
| `video_embeds` | `torch` | ✓ | - |
| `audio_video_embeds` | `torch` | ✓ | - |
| `text_audio_embeds` | `torch` | ✓ | - |
| `text_video_embeds` | `torch` | ✓ | - |
| `text_audio_video_embeds` | `torch` | ✓ | - |
| `audio_plus_text_embeds` | `torch` | ✓ | - |
| `video_plus_text_embeds` | `torch` | ✓ | - |
| `text_outputs` | `MaskedLMOutput` | ✓ | - |
| `audio_outputs` | `BaseModelOutputWithPooling` | ✓ | - |
| `video_outputs` | `BaseModelOutputWithPooling` | ✓ | - |
| `audio_video_outputs` | `BaseModelOutputWithPooling` | ✓ | - |
| `logits_audio_text` | `torch` | ✓ | - |
| `logits_video_text` | `torch` | ✓ | - |
| `logits_audio_video` | `torch` | ✓ | - |
| `logits_audio_video_text` | `torch` | ✓ | - |
| `logits_audio_plus_text_video` | `torch` | ✓ | - |
| `logits_video_plus_text_audio` | `torch` | ✓ | - |
| `audio_text_loss` | `torch` | ✓ | - |
| `video_text_loss` | `torch` | ✓ | - |
| `audio_video_loss` | `torch` | ✓ | - |
| `audio_video_text_loss` | `torch` | ✓ | - |
| `audio_plus_text_video_loss` | `torch` | ✓ | - |
| `video_plus_text_audio_loss` | `torch` | ✓ | - |
| `loss` | `torch` | ✓ | - |

**Schema: `AudioVideoEmbeddings`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `audio_embeds` | `torch` | ✓ | - |
| `video_embeds` | `torch` | ✓ | - |
| `audio_video_embeds` | `torch` | ✓ | - |

### [New] [bugfix] Changes in test_basic.py

- **File**: `venv\Lib\site-packages\scipy\fftpack\tests\test_basic.py`
- **Captured**: 4/28/2026, 12:59:29 PM
- **Category**: bugfix
**Summary:** Modified test_basic.py: 878 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\scipy\fftpack\tests\test_basic.py` (+878 / -0)
**Schema: `TestSingleFFT`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `reason` | `unknown` | ✓ | - |

### [bugfix] Changes in Dashboard.jsx

- **File**: `frontend\src\pages\Dashboard.jsx`
- **Captured**: 4/28/2026, 12:59:28 PM
- **Category**: bugfix
**Summary:** Modified Dashboard.jsx: 634 lines added, 0 lines removed.
**Files Modified:**
  - `frontend\src\pages\Dashboard.jsx` (+634 / -0)

### [New] [bugfix] Changes in test_bsplines.py

- **File**: `venv\Lib\site-packages\scipy\interpolate\tests\test_bsplines.py`
- **Captured**: 4/28/2026, 12:59:19 PM
- **Category**: bugfix
**Summary:** Modified test_bsplines.py: 4330 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\scipy\interpolate\tests\test_bsplines.py` (+4331 / -0)
**Schema: `TestMakeSplrepPeriodic`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `bc_type` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modeling_pe_video.py

- **File**: `venv\Lib\site-packages\transformers\models\pe_video\modeling_pe_video.py`
- **Captured**: 4/28/2026, 12:59:13 PM
- **Category**: bugfix
**Summary:** Modified modeling_pe_video.py: 651 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\pe_video\modeling_pe_video.py` (+651 / -0)
**Schema: `PeVideoOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `loss` | `torch` | ✓ | - |
| `logits_video_text` | `torch` | ✓ | - |
| `text_video_embeds` | `torch` | ✓ | - |
| `video_embeds` | `torch` | ✓ | - |
| `text_outputs` | `BaseModelOutputWithPooling` | ✓ | - |
| `video_outputs` | `BaseModelOutputWithPooling` | ✓ | - |

**Schema: `PeVideoPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `PeVideoConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_skip_keys_device_placement` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `_supports_flex_attn` | `unknown` | ✓ | - |
| `_can_compile_fullgraph` | `unknown` | ✓ | - |
| `_supports_attention_backend` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |
| `main_input_name` | `unknown` | ✓ | - |

**Schema: `PeVideoEncoder`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `PeVideoEncoderConfig` | ✓ | - |
| `main_input_name` | `unknown` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modular_pe_video.py

- **File**: `venv\Lib\site-packages\transformers\models\pe_video\modular_pe_video.py`
- **Captured**: 4/28/2026, 12:59:11 PM
- **Category**: bugfix
**Summary:** Modified modular_pe_video.py: 238 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\pe_video\modular_pe_video.py` (+238 / -0)
**Schema: `PeVideoOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `loss` | `torch` | ✓ | - |
| `logits_video_text` | `torch` | ✓ | - |
| `text_video_embeds` | `torch` | ✓ | - |
| `video_embeds` | `torch` | ✓ | - |
| `text_outputs` | `BaseModelOutputWithPooling` | ✓ | - |
| `video_outputs` | `BaseModelOutputWithPooling` | ✓ | - |

**Schema: `PeVideoPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `base_model_prefix` | `unknown` | ✓ | - |
| `main_input_name` | `unknown` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in bessel.py

- **File**: `venv\Lib\site-packages\sympy\functions\special\bessel.py`
- **Captured**: 4/28/2026, 12:59:06 PM
- **Category**: bugfix
**Summary:** Modified bessel.py: 2209 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\sympy\functions\special\bessel.py` (+2209 / -0)
**Schema: `besselj`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `Bessel` | `unknown` | ✓ | - |
| `Explanation` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `satisfying` | `unknown` | ✓ | - |
| `with` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |

**Schema: `bessely`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `Bessel` | `unknown` | ✓ | - |
| `Explanation` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `where` | `unknown` | ✓ | - |
| `It` | `unknown` | ✓ | - |
| `Examples` | `unknown` | ✓ | - |
| `bessely` | `unknown` | ✓ | - |
| `sqrt` | `unknown` | ✓ | - |
| `See` | `unknown` | ✓ | - |
| `besselj` | `unknown` | ✓ | - |
| `References` | `unknown` | ✓ | - |
| `_a` | `unknown` | ✓ | - |
| `_b` | `unknown` | ✓ | - |

**Schema: `besseli`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `Modified` | `unknown` | ✓ | - |
| `Explanation` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `It` | `unknown` | ✓ | - |
| `where` | `unknown` | ✓ | - |
| `Examples` | `unknown` | ✓ | - |
| `besseli` | `unknown` | ✓ | - |
| `See` | `unknown` | ✓ | - |
| `besselj` | `unknown` | ✓ | - |
| `References` | `unknown` | ✓ | - |
| `_a` | `unknown` | ✓ | - |
| `_b` | `unknown` | ✓ | - |

**Schema: `besselk`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `Modified` | `unknown` | ✓ | - |
| `Explanation` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `where` | `unknown` | ✓ | - |
| `It` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `Examples` | `unknown` | ✓ | - |
| `See` | `unknown` | ✓ | - |
| `besselj` | `unknown` | ✓ | - |
| `References` | `unknown` | ✓ | - |
| `_a` | `unknown` | ✓ | - |
| `_b` | `unknown` | ✓ | - |

**Schema: `hankel1`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `Hankel` | `unknown` | ✓ | - |
| `Explanation` | `unknown` | ✓ | - |
| `This` | `unknown` | ✓ | - |
| `where` | `unknown` | ✓ | - |
| `It` | `unknown` | ✓ | - |
| `Examples` | `unknown` | ✓ | - |
| `hankel1` | `unknown` | ✓ | - |
| `See` | `unknown` | ✓ | - |
| `hankel2` | `unknown` | ✓ | - |
| `References` | `unknown` | ✓ | - |
| `_a` | `unknown` | ✓ | - |
| `_b` | `unknown` | ✓ | - |

**Schema: `hankel2`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `Hankel` | `unknown` | ✓ | - |
| `Explanation` | `unknown` | ✓ | - |
| `This` | `unknown` | ✓ | - |
| `where` | `unknown` | ✓ | - |
| `It` | `unknown` | ✓ | - |
| `Examples` | `unknown` | ✓ | - |
| `hankel2` | `unknown` | ✓ | - |
| `See` | `unknown` | ✓ | - |
| `hankel1` | `unknown` | ✓ | - |
| `References` | `unknown` | ✓ | - |
| `_a` | `unknown` | ✓ | - |
| `_b` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |

**Schema: `SphericalBesselBase`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Base` | `unknown` | ✓ | - |
| `These` | `unknown` | ✓ | - |
| `since` | `unknown` | ✓ | - |
| `ones` | `unknown` | ✓ | - |
| `To` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |

**Schema: `jn`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `Spherical` | `unknown` | ✓ | - |
| `Explanation` | `unknown` | ✓ | - |
| `This` | `unknown` | ✓ | - |
| `It` | `unknown` | ✓ | - |
| `where` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `calculated` | `unknown` | ✓ | - |
| `where` | `unknown` | ✓ | - |
| `Examples` | `unknown` | ✓ | - |
| `sin` | `unknown` | ✓ | - |
| `True` | `unknown` | ✓ | - |
| `sqrt` | `unknown` | ✓ | - |
| `0` | `unknown` | ✓ | - |
| `See` | `unknown` | ✓ | - |
| `besselj` | `unknown` | ✓ | - |
| `References` | `unknown` | ✓ | - |

**Schema: `yn`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `Spherical` | `unknown` | ✓ | - |
| `Explanation` | `unknown` | ✓ | - |
| `This` | `unknown` | ✓ | - |
| `linearly` | `unknown` | ✓ | - |
| `where` | `unknown` | ✓ | - |
| `For` | `unknown` | ✓ | - |
| `Examples` | `unknown` | ✓ | - |
| `True` | `unknown` | ✓ | - |
| `sqrt` | `unknown` | ✓ | - |
| `0` | `unknown` | ✓ | - |
| `See` | `unknown` | ✓ | - |
| `besselj` | `unknown` | ✓ | - |
| `References` | `unknown` | ✓ | - |

**Schema: `hn1`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `Spherical` | `unknown` | ✓ | - |
| `Explanation` | `unknown` | ✓ | - |
| `This` | `unknown` | ✓ | - |
| `where` | `unknown` | ✓ | - |
| `Bessel` | `unknown` | ✓ | - |
| `For` | `unknown` | ✓ | - |
| `Examples` | `unknown` | ✓ | - |
| `jn` | `unknown` | ✓ | - |
| `sin` | `unknown` | ✓ | - |
| `sqrt` | `unknown` | ✓ | - |
| `See` | `unknown` | ✓ | - |
| `hn2` | `unknown` | ✓ | - |
| `References` | `unknown` | ✓ | - |
| `_hankel_kind_sign` | `unknown` | ✓ | - |

**Schema: `hn2`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `Spherical` | `unknown` | ✓ | - |
| `Explanation` | `unknown` | ✓ | - |
| `This` | `unknown` | ✓ | - |
| `where` | `unknown` | ✓ | - |
| `Bessel` | `unknown` | ✓ | - |
| `For` | `unknown` | ✓ | - |
| `Examples` | `unknown` | ✓ | - |
| `jn` | `unknown` | ✓ | - |
| `sin` | `unknown` | ✓ | - |
| `I` | `unknown` | ✓ | - |
| `sqrt` | `unknown` | ✓ | - |
| `See` | `unknown` | ✓ | - |
| `hn1` | `unknown` | ✓ | - |
| `References` | `unknown` | ✓ | - |
| `_hankel_kind_sign` | `unknown` | ✓ | - |

**Schema: `airyai`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `Explanation` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `satisfying` | `unknown` | ✓ | - |
| `Equivalently` | `unknown` | ✓ | - |
| `Examples` | `unknown` | ✓ | - |
| `Create` | `unknown` | ✓ | - |
| `airyai` | `unknown` | ✓ | - |
| `Several` | `unknown` | ✓ | - |
| `3` | `unknown` | ✓ | - |
| `0` | `unknown` | ✓ | - |
| `0` | `unknown` | ✓ | - |
| `airyai` | `unknown` | ✓ | - |
| `Differentiation` | `unknown` | ✓ | - |
| `airyaiprime` | `unknown` | ✓ | - |
| `z` | `unknown` | ✓ | - |
| `Series` | `unknown` | ✓ | - |
| `3` | `unknown` | ✓ | - |
| `We` | `unknown` | ✓ | - |
| `on` | `unknown` | ✓ | - |
| `0` | `unknown` | ✓ | - |
| `Rewrite` | `unknown` | ✓ | - |
| `See` | `unknown` | ✓ | - |
| `airybi` | `Airy function of the second kind` | ✓ | - |
| `airyaiprime` | `Derivative of the Airy function of the first kind` | ✓ | - |
| `airybiprime` | `Derivative of the Airy function of the second kind` | ✓ | - |
| `References` | `unknown` | ✓ | - |
| `nargs` | `unknown` | ✓ | - |
| `unbranched` | `unknown` | ✓ | - |

**Schema: `airybi`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `Explanation` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `satisfying` | `unknown` | ✓ | - |
| `Equivalently` | `unknown` | ✓ | - |
| `Examples` | `unknown` | ✓ | - |
| `Create` | `unknown` | ✓ | - |
| `airybi` | `unknown` | ✓ | - |
| `Several` | `unknown` | ✓ | - |
| `3` | `unknown` | ✓ | - |
| `oo` | `unknown` | ✓ | - |
| `0` | `unknown` | ✓ | - |
| `airybi` | `unknown` | ✓ | - |
| `Differentiation` | `unknown` | ✓ | - |
| `airybiprime` | `unknown` | ✓ | - |
| `z` | `unknown` | ✓ | - |
| `Series` | `unknown` | ✓ | - |
| `3` | `unknown` | ✓ | - |
| `We` | `unknown` | ✓ | - |
| `on` | `unknown` | ✓ | - |
| `Rewrite` | `unknown` | ✓ | - |
| `3` | `unknown` | ✓ | - |
| `See` | `unknown` | ✓ | - |
| `airyai` | `Airy function of the first kind` | ✓ | - |
| `airyaiprime` | `Derivative of the Airy function of the first kind` | ✓ | - |
| `airybiprime` | `Derivative of the Airy function of the second kind` | ✓ | - |
| `References` | `unknown` | ✓ | - |
| `nargs` | `unknown` | ✓ | - |
| `unbranched` | `unknown` | ✓ | - |

**Schema: `airyaiprime`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `kind` | `unknown` | ✓ | - |
| `Explanation` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `function` | `unknown` | ✓ | - |
| `Examples` | `unknown` | ✓ | - |
| `Create` | `unknown` | ✓ | - |
| `airyaiprime` | `unknown` | ✓ | - |
| `Several` | `unknown` | ✓ | - |
| `0` | `unknown` | ✓ | - |
| `airyaiprime` | `unknown` | ✓ | - |
| `Differentiation` | `unknown` | ✓ | - |
| `z` | `unknown` | ✓ | - |
| `z` | `unknown` | ✓ | - |
| `Series` | `unknown` | ✓ | - |
| `We` | `unknown` | ✓ | - |
| `on` | `unknown` | ✓ | - |
| `0` | `unknown` | ✓ | - |
| `Rewrite` | `unknown` | ✓ | - |
| `3` | `unknown` | ✓ | - |
| `See` | `unknown` | ✓ | - |
| `airyai` | `Airy function of the first kind` | ✓ | - |
| `airybi` | `Airy function of the second kind` | ✓ | - |
| `airybiprime` | `Derivative of the Airy function of the second kind` | ✓ | - |
| `References` | `unknown` | ✓ | - |
| `nargs` | `unknown` | ✓ | - |
| `unbranched` | `unknown` | ✓ | - |

**Schema: `airybiprime`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `kind` | `unknown` | ✓ | - |
| `Explanation` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `function` | `unknown` | ✓ | - |
| `Examples` | `unknown` | ✓ | - |
| `Create` | `unknown` | ✓ | - |
| `airybiprime` | `unknown` | ✓ | - |
| `Several` | `unknown` | ✓ | - |
| `3` | `unknown` | ✓ | - |
| `oo` | `unknown` | ✓ | - |
| `0` | `unknown` | ✓ | - |
| `airybiprime` | `unknown` | ✓ | - |
| `Differentiation` | `unknown` | ✓ | - |
| `z` | `unknown` | ✓ | - |
| `z` | `unknown` | ✓ | - |
| `Series` | `unknown` | ✓ | - |
| `3` | `unknown` | ✓ | - |
| `We` | `unknown` | ✓ | - |
| `on` | `unknown` | ✓ | - |
| `0` | `unknown` | ✓ | - |
| `Rewrite` | `unknown` | ✓ | - |
| `3` | `unknown` | ✓ | - |
| `See` | `unknown` | ✓ | - |
| `airyai` | `Airy function of the first kind` | ✓ | - |
| `airybi` | `Airy function of the second kind` | ✓ | - |
| `airyaiprime` | `Derivative of the Airy function of the first kind` | ✓ | - |
| `References` | `unknown` | ✓ | - |
| `nargs` | `unknown` | ✓ | - |
| `unbranched` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in hyper.py

- **File**: `venv\Lib\site-packages\sympy\functions\special\hyper.py`
- **Captured**: 4/28/2026, 12:59:04 PM
- **Category**: bugfix
**Summary:** Modified hyper.py: 1186 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\sympy\functions\special\hyper.py` (+1186 / -0)
**Schema: `hyper`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `the` | `unknown` | ✓ | - |
| `index` | `unknown` | ✓ | - |
| `possible` | `unknown` | ✓ | - |
| `Explanation` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `the` | `unknown` | ✓ | - |
| `where` | `unknown` | ✓ | - |
| `If` | `unknown` | ✓ | - |
| `magnitude` | `unknown` | ✓ | - |
| `non` | `unknown` | ✓ | - |
| `integer` | `unknown` | ✓ | - |
| `following` | `unknown` | ✓ | - |
| `references` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `q` | `unknown` | ✓ | - |
| `analytically` | `unknown` | ✓ | - |
| `divergent` | `unknown` | ✓ | - |
| `Please` | `unknown` | ✓ | - |
| `check` | `unknown` | ✓ | - |
| `Examples` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `iterables` | `unknown` | ✓ | - |
| `hyper` | `unknown` | ✓ | - |
| `hyper` | `unknown` | ✓ | - |
| `There` | `unknown` | ✓ | - |
| `2` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `length` | `unknown` | ✓ | - |
| `hyper` | `unknown` | ✓ | - |
| `But` | `unknown` | ✓ | - |
| `should` | `unknown` | ✓ | - |
| `hyper` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `using` | `unknown` | ✓ | - |
| `exp` | `unknown` | ✓ | - |
| `You` | `unknown` | ✓ | - |
| `log` | `unknown` | ✓ | - |
| `More` | `unknown` | ✓ | - |
| `cos` | `unknown` | ✓ | - |
| `asin` | `unknown` | ✓ | - |
| `We` | `unknown` | ✓ | - |
| `See` | `unknown` | ✓ | - |
| `sympy` | `unknown` | ✓ | - |
| `gamma` | `unknown` | ✓ | - |
| `References` | `unknown` | ✓ | - |

**Schema: `meijerg`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `resembles` | `unknown` | ✓ | - |
| `functions` | `unknown` | ✓ | - |
| `Explanation` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `Confusingly` | `unknown` | ✓ | - |
| `of` | `unknown` | ✓ | - |
| `parameter` | `unknown` | ✓ | - |
| `However` | `unknown` | ✓ | - |
| `separately` | `unknown` | ✓ | - |
| `decorating` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `where` | `unknown` | ✓ | - |
| `contours` | `unknown` | ✓ | - |
| `If` | `unknown` | ✓ | - |
| `agree` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `is` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in mathieu_functions.py

- **File**: `venv\Lib\site-packages\sympy\functions\special\mathieu_functions.py`
- **Captured**: 4/28/2026, 12:59:02 PM
- **Category**: bugfix
**Summary:** Modified mathieu_functions.py: 270 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\sympy\functions\special\mathieu_functions.py` (+270 / -0)
**Schema: `mathieus`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `Explanation` | `unknown` | ✓ | - |
| `This` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `Examples` | `unknown` | ✓ | - |
| `mathieus` | `unknown` | ✓ | - |
| `sin` | `unknown` | ✓ | - |
| `mathieusprime` | `unknown` | ✓ | - |
| `See` | `unknown` | ✓ | - |
| `mathieuc` | `Mathieu cosine function` | ✓ | - |
| `mathieusprime` | `Derivative of Mathieu sine function` | ✓ | - |
| `mathieucprime` | `Derivative of Mathieu cosine function` | ✓ | - |
| `References` | `unknown` | ✓ | - |

**Schema: `mathieuc`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `Explanation` | `unknown` | ✓ | - |
| `This` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `Examples` | `unknown` | ✓ | - |
| `mathieuc` | `unknown` | ✓ | - |
| `cos` | `unknown` | ✓ | - |
| `mathieucprime` | `unknown` | ✓ | - |
| `See` | `unknown` | ✓ | - |
| `mathieus` | `Mathieu sine function` | ✓ | - |
| `mathieusprime` | `Derivative of Mathieu sine function` | ✓ | - |
| `mathieucprime` | `Derivative of Mathieu cosine function` | ✓ | - |
| `References` | `unknown` | ✓ | - |

**Schema: `mathieusprime`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `Explanation` | `unknown` | ✓ | - |
| `This` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `Examples` | `unknown` | ✓ | - |
| `mathieusprime` | `unknown` | ✓ | - |
| `sqrt` | `unknown` | ✓ | - |
| `See` | `unknown` | ✓ | - |
| `mathieus` | `Mathieu sine function` | ✓ | - |
| `mathieuc` | `Mathieu cosine function` | ✓ | - |
| `mathieucprime` | `Derivative of Mathieu cosine function` | ✓ | - |
| `References` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in _fitpack2.py

- **File**: `venv\Lib\site-packages\scipy\interpolate\_fitpack2.py`
- **Captured**: 4/28/2026, 12:58:58 PM
- **Category**: bugfix
**Summary:** Modified _fitpack2.py: 2409 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\scipy\interpolate\_fitpack2.py` (+2409 / -0)
**Schema: `BivariateSpline`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Base` | `unknown` | ✓ | - |
| `This` | `unknown` | ✓ | - |
| `the` | `unknown` | ✓ | - |
| `of` | `unknown` | ✓ | - |
| `This` | `unknown` | ✓ | - |
| `To` | `unknown` | ✓ | - |
| `See` | `unknown` | ✓ | - |
| `UnivariateSpline` | `a smooth univariate spline to fit a given set of data points` | ✓ | - |
| `SmoothBivariateSpline` | `a smoothing bivariate spline through the given points` | ✓ | - |
| `LSQBivariateSpline` | `a bivariate spline using weighted least` | ✓ | - |
| `RectSphereBivariateSpline` | `a bivariate spline over a rectangular mesh on a sphere` | ✓ | - |
| `SmoothSphereBivariateSpline` | `a smoothing bivariate spline in spherical coordinates` | ✓ | - |
| `LSQSphereBivariateSpline` | `a bivariate spline in spherical coordinates using weighted` | ✓ | - |
| `RectBivariateSpline` | `a bivariate spline over a rectangular mesh` | ✓ | - |
| `bisplrep` | `a function to find a bivariate B` | ✓ | - |
| `bisplev` | `a function to evaluate a bivariate B` | ✓ | - |

**Schema: `_DerivedBivariateSpline`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `spline` | `unknown` | ✓ | - |
| `Notes` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `interpolated` | `unknown` | ✓ | - |
| `raised` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `_invalid_why` | `unknown` | ✓ | - |

**Schema: `SphereBivariateSpline`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Bivariate` | `unknown` | ✓ | - |
| `given` | `unknown` | ✓ | - |
| `See` | `unknown` | ✓ | - |
| `bisplrep` | `a function to find a bivariate B` | ✓ | - |
| `bisplev` | `a function to evaluate a bivariate B` | ✓ | - |
| `UnivariateSpline` | `a smooth univariate spline to fit a given set of data points` | ✓ | - |
| `SmoothBivariateSpline` | `a smoothing bivariate spline through the given points` | ✓ | - |
| `LSQUnivariateSpline` | `a univariate spline using weighted least` | ✓ | - |

### [New] [bugfix] Changes in _interpolate.py

- **File**: `venv\Lib\site-packages\scipy\interpolate\_interpolate.py`
- **Captured**: 4/28/2026, 12:58:56 PM
- **Category**: bugfix
**Summary:** Modified _interpolate.py: 2313 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\scipy\interpolate\_interpolate.py` (+2313 / -0)
**Schema: `PPoly`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `The` | `unknown` | ✓ | - |
| `local` | `unknown` | ✓ | - |
| `where` | `unknown` | ✓ | - |
| `Parameters` | `unknown` | ✓ | - |
| `c` | `ndarray, shape` | ✓ | - |
| `x` | `ndarray, shape` | ✓ | - |
| `extrapolate` | `bool or` | ✓ | - |
| `axis` | `int, optional` | ✓ | - |
| `Attributes` | `unknown` | ✓ | - |
| `x` | `ndarray` | ✓ | - |
| `c` | `ndarray` | ✓ | - |
| `axis` | `int` | ✓ | - |
| `Methods` | `unknown` | ✓ | - |
| `antiderivative` | `unknown` | ✓ | - |
| `solve` | `unknown` | ✓ | - |
| `extend` | `unknown` | ✓ | - |
| `from_bernstein_basis` | `unknown` | ✓ | - |
| `See` | `unknown` | ✓ | - |
| `BPoly` | `piecewise polynomials in the Bernstein basis` | ✓ | - |
| `Notes` | `unknown` | ✓ | - |
| `High` | `unknown` | ✓ | - |
| `unstable` | `unknown` | ✓ | - |
| `larger` | `unknown` | ✓ | - |
| `cpu_only` | `unknown` | ✓ | - |
| `skip_backends` | `unknown` | ✓ | - |

**Schema: `BPoly`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `The` | `unknown` | ✓ | - |
| `Bernstein` | `unknown` | ✓ | - |
| `where` | `unknown` | ✓ | - |
| `with` | `unknown` | ✓ | - |
| `coefficient` | `unknown` | ✓ | - |
| `Parameters` | `unknown` | ✓ | - |
| `c` | `ndarray, shape` | ✓ | - |
| `x` | `ndarray, shape` | ✓ | - |
| `extrapolate` | `bool, optional` | ✓ | - |
| `axis` | `int, optional` | ✓ | - |
| `Attributes` | `unknown` | ✓ | - |
| `x` | `ndarray` | ✓ | - |
| `c` | `ndarray` | ✓ | - |
| `axis` | `int` | ✓ | - |
| `Methods` | `unknown` | ✓ | - |
| `derivative` | `unknown` | ✓ | - |
| `integrate` | `unknown` | ✓ | - |
| `from_power_basis` | `unknown` | ✓ | - |
| `See` | `unknown` | ✓ | - |
| `PPoly` | `piecewise polynomials in the power basis` | ✓ | - |
| `Notes` | `unknown` | ✓ | - |
| `Properties` | `unknown` | ✓ | - |
| `see` | `unknown` | ✓ | - |
| `References` | `unknown` | ✓ | - |
| `Examples` | `unknown` | ✓ | - |
| `This` | `unknown` | ✓ | - |
| `extend` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in _ndgriddata.py

- **File**: `venv\Lib\site-packages\scipy\interpolate\_ndgriddata.py`
- **Captured**: 4/28/2026, 12:58:53 PM
- **Category**: bugfix
**Summary:** Modified _ndgriddata.py: 331 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\scipy\interpolate\_ndgriddata.py` (+331 / -0)
**Schema: `NearestNDInterpolator`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Methods` | `unknown` | ✓ | - |
| `x` | `unknown` | ✓ | - |
| `y` | `unknown` | ✓ | - |
| `rescale` | `boolean, optional` | ✓ | - |
| `tree_options` | `dict, optional` | ✓ | - |
| `See` | `unknown` | ✓ | - |
| `griddata` | `Interpolate unstructured D` | ✓ | - |
| `LinearNDInterpolator` | `Piecewise linear interpolator in N dimensions` | ✓ | - |
| `CloughTocher2DInterpolator` | `Piecewise cubic, C1 smooth, curvature` | ✓ | - |
| `interpn` | `Interpolation on a regular grid or rectilinear grid` | ✓ | - |
| `RegularGridInterpolator` | `Interpolator on a regular or rectilinear grid` | ✓ | - |
| `Notes` | `unknown` | ✓ | - |
| `Uses` | `unknown` | ✓ | - |
| `Examples` | `unknown` | ✓ | - |
| `We` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in cxx.py

- **File**: `venv\Lib\site-packages\sympy\printing\cxx.py`
- **Captured**: 4/28/2026, 12:58:50 PM
- **Category**: bugfix
**Summary:** Modified cxx.py: 182 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\sympy\printing\cxx.py` (+182 / -0)
**Schema: `CXX98CodePrinter`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `standard` | `unknown` | ✓ | - |
| `reserved_words` | `unknown` | ✓ | - |

**Schema: `CXX11CodePrinter`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `standard` | `unknown` | ✓ | - |
| `reserved_words` | `unknown` | ✓ | - |
| `type_mappings` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in mathml.py

- **File**: `venv\Lib\site-packages\sympy\printing\mathml.py`
- **Captured**: 4/28/2026, 12:58:48 PM
- **Category**: bugfix
**Summary:** Modified mathml.py: 2158 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\sympy\printing\mathml.py` (+2158 / -0)
**Schema: `MathMLContentPrinter`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `References` | `https` | ✓ | - |
| `printmethod` | `unknown` | ✓ | - |
| `_print_MatrixSymbol` | `unknown` | ✓ | - |
| `_print_RandomSymbol` | `unknown` | ✓ | - |
| `_print_Implies` | `unknown` | ✓ | - |
| `_print_Not` | `unknown` | ✓ | - |
| `_print_Xor` | `unknown` | ✓ | - |

**Schema: `MathMLPresentationPrinter`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `References` | `https` | ✓ | - |
| `printmethod` | `unknown` | ✓ | - |
| `_print_RandomSymbol` | `unknown` | ✓ | - |
| `_print_Determinant` | `unknown` | ✓ | - |
| `_print_frozenset` | `unknown` | ✓ | - |
| `_print_BooleanTrue` | `unknown` | ✓ | - |
| `_print_BooleanFalse` | `unknown` | ✓ | - |
| `_print_Min` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modeling_phi.py

- **File**: `venv\Lib\site-packages\transformers\models\phi\modeling_phi.py`
- **Captured**: 4/28/2026, 12:58:44 PM
- **Category**: bugfix
**Summary:** Modified modeling_phi.py: 495 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\phi\modeling_phi.py` (+495 / -0)
**Schema: `PhiPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `PhiConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_skip_keys_device_placement` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `_supports_flex_attn` | `unknown` | ✓ | - |
| `_can_compile_fullgraph` | `unknown` | ✓ | - |
| `_supports_attention_backend` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |

**Schema: `PhiForCausalLM`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_tied_weights_keys` | `unknown` | ✓ | - |
| `_tp_plan` | `unknown` | ✓ | - |
| `_pp_plan` | `unknown` | ✓ | - |

**Schema: `PhiForSequenceClassification`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `pass` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modular_phi.py

- **File**: `venv\Lib\site-packages\transformers\models\phi\modular_phi.py`
- **Captured**: 4/28/2026, 12:58:42 PM
- **Category**: bugfix
**Summary:** Modified modular_phi.py: 289 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\phi\modular_phi.py` (+289 / -0)
**Schema: `PhiPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_can_record_outputs` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in test_multivariate.py

- **File**: `venv\Lib\site-packages\scipy\stats\tests\test_multivariate.py`
- **Captured**: 4/28/2026, 12:58:28 PM
- **Category**: bugfix
**Summary:** Modified test_multivariate.py: 5029 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\scipy\stats\tests\test_multivariate.py` (+5029 / -0)
**API Endpoints** (`test_multivariate.py`):

| Method | Route | Handler | Middleware |
|--------|-------|---------|------------|
| `PATCH` | `scipy.stats.multivariate_normal._logpdf` | patch | - |

### [New] [bugfix] Changes in modeling_phi3.py

- **File**: `venv\Lib\site-packages\transformers\models\phi3\modeling_phi3.py`
- **Captured**: 4/28/2026, 12:58:22 PM
- **Category**: bugfix
**Summary:** Modified modeling_phi3.py: 558 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\phi3\modeling_phi3.py` (+558 / -0)
**Schema: `Phi3PreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Phi3Config` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_skip_keys_device_placement` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `_supports_flex_attn` | `unknown` | ✓ | - |
| `_can_compile_fullgraph` | `unknown` | ✓ | - |
| `_supports_attention_backend` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |
| `_version` | `unknown` | ✓ | - |

**Schema: `Phi3ForCausalLM`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_tied_weights_keys` | `unknown` | ✓ | - |
| `_tp_plan` | `unknown` | ✓ | - |
| `_pp_plan` | `unknown` | ✓ | - |

**Schema: `Phi3ForSequenceClassification`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `pass` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modeling_phi4_multimodal.py

- **File**: `venv\Lib\site-packages\transformers\models\phi4_multimodal\modeling_phi4_multimodal.py`
- **Captured**: 4/28/2026, 12:58:10 PM
- **Category**: bugfix
**Summary:** Modified modeling_phi4_multimodal.py: 1757 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\phi4_multimodal\modeling_phi4_multimodal.py` (+1757 / -0)
**Schema: `Phi4MultimodalVisionPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Phi4MultimodalVisionConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `_supports_flex_attn` | `unknown` | ✓ | - |
| `_supports_attention_backend` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |

**Schema: `Phi4MultimodalVisionModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Phi4MultimodalVisionConfig` | ✓ | - |
| `main_input_name` | `unknown` | ✓ | - |

**Schema: `Phi4MultimodalAudioPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Phi4MultimodalAudioConfig` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `_supports_flex_attn` | `unknown` | ✓ | - |
| `For` | `unknown` | ✓ | - |
| `this` | `unknown` | ✓ | - |
| `Args` | `tensor` | ✓ | - |
| `_` | `unknown` | ✓ | - |
| `tensor` | `unknown` | ✓ | - |
| `tensor` | `unknown` | ✓ | - |
| `new_bsz` | `unknown` | ✓ | - |
| `tensor` | `unknown` | ✓ | - |
| `tensor` | `unknown` | ✓ | - |
| `tensor` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `Args` | `xs_len` | ✓ | - |
| `chunk_start_idx` | `unknown` | ✓ | - |
| `start_pad` | `unknown` | ✓ | - |
| `end_pad` | `unknown` | ✓ | - |
| `seq_range` | `unknown` | ✓ | - |
| `idx` | `unknown` | ✓ | - |
| `seq_range_expand` | `unknown` | ✓ | - |
| `idx_left` | `unknown` | ✓ | - |
| `idx_left` | `unknown` | ✓ | - |
| `boundary_left` | `unknown` | ✓ | - |
| `mask_left` | `unknown` | ✓ | - |
| `idx_right` | `unknown` | ✓ | - |
| `idx_right` | `unknown` | ✓ | - |
| `boundary_right` | `unknown` | ✓ | - |
| `mask_right` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |

**Schema: `Phi4MultimodalPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Phi4MultimodalConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_skip_keys_device_placement` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `_supports_flex_attn` | `unknown` | ✓ | - |
| `_can_compile_fullgraph` | `unknown` | ✓ | - |
| `_supports_attention_backend` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |
| `_version` | `unknown` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modular_phi4_multimodal.py

- **File**: `venv\Lib\site-packages\transformers\models\phi4_multimodal\modular_phi4_multimodal.py`
- **Captured**: 4/28/2026, 12:58:07 PM
- **Category**: bugfix
**Summary:** Modified modular_phi4_multimodal.py: 1533 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\phi4_multimodal\modular_phi4_multimodal.py` (+1533 / -0)
**Schema: `Phi4MultimodalVisionPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Phi4MultimodalVisionConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `_supports_flex_attn` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |

**Schema: `Phi4MultimodalVisionModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Phi4MultimodalVisionConfig` | ✓ | - |
| `main_input_name` | `unknown` | ✓ | - |

**Schema: `Phi4MultimodalAudioPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Phi4MultimodalAudioConfig` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `_supports_flex_attn` | `unknown` | ✓ | - |

**Schema: `Phi4MultimodalAudioModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `For` | `unknown` | ✓ | - |
| `this` | `unknown` | ✓ | - |
| `Args` | `tensor` | ✓ | - |
| `_` | `unknown` | ✓ | - |
| `tensor` | `unknown` | ✓ | - |
| `tensor` | `unknown` | ✓ | - |
| `new_bsz` | `unknown` | ✓ | - |
| `tensor` | `unknown` | ✓ | - |
| `tensor` | `unknown` | ✓ | - |
| `tensor` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `Args` | `xs_len` | ✓ | - |
| `chunk_start_idx` | `unknown` | ✓ | - |
| `start_pad` | `unknown` | ✓ | - |
| `end_pad` | `unknown` | ✓ | - |
| `seq_range` | `unknown` | ✓ | - |
| `idx` | `unknown` | ✓ | - |
| `seq_range_expand` | `unknown` | ✓ | - |
| `idx_left` | `unknown` | ✓ | - |
| `idx_left` | `unknown` | ✓ | - |
| `boundary_left` | `unknown` | ✓ | - |
| `mask_left` | `unknown` | ✓ | - |
| `idx_right` | `unknown` | ✓ | - |
| `idx_right` | `unknown` | ✓ | - |
| `boundary_right` | `unknown` | ✓ | - |
| `mask_right` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |

**Schema: `Phi4MultimodalPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `input_modalities` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in test_least_squares.py

- **File**: `venv\Lib\site-packages\scipy\optimize\tests\test_least_squares.py`
- **Captured**: 4/28/2026, 12:58:02 PM
- **Category**: bugfix
**Summary:** Modified test_least_squares.py: 1000 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\scipy\optimize\tests\test_least_squares.py` (+1000 / -0)
**Schema: `TestDogbox`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `method` | `unknown` | ✓ | - |

**Schema: `TestTRF`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `method` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in test_lsq_linear.py

- **File**: `venv\Lib\site-packages\scipy\optimize\tests\test_lsq_linear.py`
- **Captured**: 4/28/2026, 12:58:00 PM
- **Category**: bugfix
**Summary:** Modified test_lsq_linear.py: 291 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\scipy\optimize\tests\test_lsq_linear.py` (+291 / -0)
**Schema: `TestTRF`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `method` | `unknown` | ✓ | - |
| `lsq_solvers` | `unknown` | ✓ | - |

**Schema: `TestBVLS`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `method` | `unknown` | ✓ | - |
| `lsq_solvers` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in bdist_rpm.py

- **File**: `venv\Lib\site-packages\setuptools\command\bdist_rpm.py`
- **Captured**: 4/28/2026, 12:57:55 PM
- **Category**: bugfix
**Summary:** Modified bdist_rpm.py: 43 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\setuptools\command\bdist_rpm.py` (+43 / -0)

### [New] [bugfix] Changes in bdist_wheel.py

- **File**: `venv\Lib\site-packages\setuptools\command\bdist_wheel.py`
- **Captured**: 4/28/2026, 12:57:54 PM
- **Category**: bugfix
**Summary:** Modified bdist_wheel.py: 604 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\setuptools\command\bdist_wheel.py` (+604 / -0)

### [New] [bugfix] Changes in editable_wheel.py

- **File**: `venv\Lib\site-packages\setuptools\command\editable_wheel.py`
- **Captured**: 4/28/2026, 12:57:50 PM
- **Category**: bugfix
**Summary:** Modified editable_wheel.py: 915 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\setuptools\command\editable_wheel.py` (+915 / -0)

### [New] [bugfix] Changes in install.py

- **File**: `venv\Lib\site-packages\setuptools\command\install.py`
- **Captured**: 4/28/2026, 12:57:48 PM
- **Category**: bugfix
**Summary:** Modified install.py: 132 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\setuptools\command\install.py` (+132 / -0)

### [New] [bugfix] Changes in test.py

- **File**: `venv\Lib\site-packages\setuptools\command\test.py`
- **Captured**: 4/28/2026, 12:57:45 PM
- **Category**: bugfix
**Summary:** Modified test.py: 48 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\setuptools\command\test.py` (+48 / -0)

### [New] [bugfix] Changes in _stats_py.py

- **File**: `venv\Lib\site-packages\scipy\stats\_stats_py.py`
- **Captured**: 4/28/2026, 12:57:42 PM
- **Category**: bugfix
**Summary:** Modified _stats_py.py: 10841 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\scipy\stats\_stats_py.py` (+10841 / -0)
**Schema: `PearsonRResult`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Result` | `unknown` | ✓ | - |
| `Attributes` | `unknown` | ✓ | - |
| `statistic` | `float` | ✓ | - |
| `pvalue` | `float` | ✓ | - |
| `Methods` | `unknown` | ✓ | - |
| `confidence_interval` | `unknown` | ✓ | - |
| `r` | `unknown` | ✓ | - |
| `Pearson` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `between` | `unknown` | ✓ | - |
| `coefficients` | `unknown` | ✓ | - |
| `correlation` | `unknown` | ✓ | - |
| `Positive` | `unknown` | ✓ | - |
| `correlations` | `unknown` | ✓ | - |
| `This` | `unknown` | ✓ | - |
| `distributions` | `unknown` | ✓ | - |
| `distributed` | `unknown` | ✓ | - |
| `for` | `unknown` | ✓ | - |
| `distribution` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `producing` | `unknown` | ✓ | - |
| `as` | `unknown` | ✓ | - |
| `Parameters` | `unknown` | ✓ | - |
| `x` | `array_like` | ✓ | - |
| `y` | `array_like` | ✓ | - |
| `axis` | `int or None, default` | ✓ | - |
| `alternative` | `unknown` | ✓ | - |
| `method` | `ResamplingMethod, optional` | ✓ | - |
| `Returns` | `unknown` | ✓ | - |
| `result` | `unknown` | ✓ | - |
| `Raises` | `unknown` | ✓ | - |
| `ValueError` | `unknown` | ✓ | - |
| `Warns` | `unknown` | ✓ | - |
| `See` | `unknown` | ✓ | - |
| `spearmanr` | `Spearman rank` | ✓ | - |
| `kendalltau` | `Kendall` | ✓ | - |
| `Notes` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `where` | `math` | ✓ | - |
| `the` | `unknown` | ✓ | - |
| `Under` | `unknown` | ✓ | - |
| `independent` | `unknown` | ✓ | - |
| `is` | `unknown` | ✓ | - |
| `coefficient` | `unknown` | ✓ | - |
| `where` | `unknown` | ✓ | - |
| `is` | `unknown` | ✓ | - |
| `the` | `unknown` | ✓ | - |
| `the` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `with` | `unknown` | ✓ | - |
| `implementation` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `given` | `unknown` | ✓ | - |
| `the` | `unknown` | ✓ | - |
| `the` | `unknown` | ✓ | - |
| `to` | `unknown` | ✓ | - |
| `for` | `unknown` | ✓ | - |
| `When` | `unknown` | ✓ | - |
| `One` | `unknown` | ✓ | - |
| `parameters` | `unknown` | ✓ | - |
| `equal` | `unknown` | ✓ | - |
| `can` | `unknown` | ✓ | - |
| `assuming` | `unknown` | ✓ | - |
| `and` | `unknown` | ✓ | - |
| `be` | `unknown` | ✓ | - |
| `For` | `unknown` | ✓ | - |
| `like` | `unknown` | ✓ | - |
| `References` | `unknown` | ✓ | - |
| `Examples` | `unknown` | ✓ | - |
| `PearsonRResult` | `unknown` | ✓ | - |
| `To` | `unknown` | ✓ | - |
| `PearsonRResult` | `unknown` | ✓ | - |
| `To` | `unknown` | ✓ | - |
| `PearsonRResult` | `unknown` | ✓ | - |
| `To` | `unknown` | ✓ | - |
| `ConfidenceInterval` | `unknown` | ✓ | - |
| `And` | `unknown` | ✓ | - |
| `ConfidenceInterval` | `unknown` | ✓ | - |
| `If` | `unknown` | ✓ | - |
| `single` | `unknown` | ✓ | - |
| `To` | `unknown` | ✓ | - |
| `use` | `unknown` | ✓ | - |
| `correlation` | `unknown` | ✓ | - |
| `There` | `unknown` | ✓ | - |
| `a` | `unknown` | ✓ | - |
| `of` | `unknown` | ✓ | - |
| `e` | `unknown` | ✓ | - |
| `0` | `unknown` | ✓ | - |
| `This` | `unknown` | ✓ | - |
| `0` | `unknown` | ✓ | - |
| `For` | `unknown` | ✓ | - |
| `variance` | `unknown` | ✓ | - |
| `approaches` | `unknown` | ✓ | - |
| `It` | `unknown` | ✓ | - |
| `independence` | `unknown` | ✓ | - |
| `when` | `unknown` | ✓ | - |
| `standard` | `unknown` | ✓ | - |
| `between` | `unknown` | ✓ | - |
| `cov` | `unknown` | ✓ | - |
| `by` | `unknown` | ✓ | - |
| `PearsonRResult` | `unknown` | ✓ | - |
| `A` | `unknown` | ✓ | - |
| `a` | `unknown` | ✓ | - |
| `A` | `unknown` | ✓ | - |
| `implying` | `unknown` | ✓ | - |
| `PearsonRResult` | `unknown` | ✓ | - |
| `This` | `unknown` | ✓ | - |
| `than` | `unknown` | ✓ | - |
| `For` | `unknown` | ✓ | - |
| `xp` | `unknown` | ✓ | - |
| `x` | `unknown` | ✓ | - |
| `dtype` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `axis_int` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `axis` | `unknown` | ✓ | - |
| `try` | `np` | ✓ | - |
| `except` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `x` | `unknown` | ✓ | - |
| `n` | `unknown` | ✓ | - |
| `x` | `unknown` | ✓ | - |
| `y` | `unknown` | ✓ | - |
| `axis` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `x` | `unknown` | ✓ | - |
| `y` | `unknown` | ✓ | - |
| `threshold` | `unknown` | ✓ | - |
| `const_x` | `unknown` | ✓ | - |
| `const_y` | `unknown` | ✓ | - |
| `const_xy` | `unknown` | ✓ | - |
| `any_const_xy` | `unknown` | ✓ | - |
| `lazy` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `elif` | `unknown` | ✓ | - |
| `elif` | `unknown` | ✓ | - |
| `elif` | `unknown` | ✓ | - |
| `xmean` | `unknown` | ✓ | - |
| `ymean` | `unknown` | ✓ | - |
| `xm` | `unknown` | ✓ | - |
| `ym` | `unknown` | ✓ | - |
| `xmax` | `unknown` | ✓ | - |
| `ymax` | `unknown` | ✓ | - |
| `with` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `with` | `unknown` | ✓ | - |
| `r` | `unknown` | ✓ | - |
| `r` | `unknown` | ✓ | - |
| `ab` | `unknown` | ✓ | - |
| `dist` | `unknown` | ✓ | - |
| `pvalue` | `unknown` | ✓ | - |
| `mask` | `unknown` | ✓ | - |
| `mxp` | `unknown` | ✓ | - |
| `r` | `unknown` | ✓ | - |
| `pvalue` | `unknown` | ✓ | - |
| `r` | `unknown` | ✓ | - |
| `pvalue` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `For` | `unknown` | ✓ | - |
| `the` | `unknown` | ✓ | - |
| `underlying` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `resulting` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `ratio` | `unknown` | ✓ | - |
| `obtaining` | `unknown` | ✓ | - |
| `observed` | `unknown` | ✓ | - |
| `For` | `unknown` | ✓ | - |
| `is` | `unknown` | ✓ | - |
| `independent` | `unknown` | ✓ | - |
| `distribution` | `unknown` | ✓ | - |
| `probability` | `unknown` | ✓ | - |
| `p` | `unknown` | ✓ | - |
| `least` | `unknown` | ✓ | - |
| `hypothesis` | `unknown` | ✓ | - |
| `There` | `unknown` | ✓ | - |
| `p` | `unknown` | ✓ | - |
| `Notes` | `unknown` | ✓ | - |
| `Parameters` | `unknown` | ✓ | - |
| `table` | `array_like of ints` | ✓ | - |
| `alternative` | `unknown` | ✓ | - |
| `method` | `ResamplingMethod, optional` | ✓ | - |
| `Returns` | `unknown` | ✓ | - |
| `res` | `SignificanceResult` | ✓ | - |
| `Raises` | `unknown` | ✓ | - |
| `ValueError` | `unknown` | ✓ | - |
| `See` | `unknown` | ✓ | - |
| `chi2_contingency` | `Chi` | ✓ | - |
| `contingency` | `unknown` | ✓ | - |
| `barnard_exact` | `Barnard` | ✓ | - |
| `boschloo_exact` | `Boschloo` | ✓ | - |
| `Notes` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `underlying` | `unknown` | ✓ | - |
| `random` | `unknown` | ✓ | - |
| `resulting` | `unknown` | ✓ | - |
| `the` | `unknown` | ✓ | - |
| `distribution` | `unknown` | ✓ | - |
| `input` | `unknown` | ✓ | - |
| `in` | `unknown` | ✓ | - |
| `can` | `unknown` | ✓ | - |
| `tables` | `unknown` | ✓ | - |
| `For` | `unknown` | ✓ | - |
| `then` | `unknown` | ✓ | - |
| `are` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `three` | `unknown` | ✓ | - |
| `These` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `a` | `unknown` | ✓ | - |
| `probability` | `unknown` | ✓ | - |
| `the` | `unknown` | ✓ | - |
| `probability` | `unknown` | ✓ | - |
| `is` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `that` | `unknown` | ✓ | - |
| `or` | `unknown` | ✓ | - |
| `This` | `unknown` | ✓ | - |
| `distribution` | `unknown` | ✓ | - |
| `because` | `unknown` | ✓ | - |
| `For` | `unknown` | ✓ | - |
| `that` | `unknown` | ✓ | - |
| `or` | `unknown` | ✓ | - |
| `This` | `unknown` | ✓ | - |
| `of` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `R` | `unknown` | ✓ | - |
| `or` | `unknown` | ✓ | - |
| `in` | `unknown` | ✓ | - |
| `conditional` | `unknown` | ✓ | - |
| `References` | `unknown` | ✓ | - |
| `Examples` | `unknown` | ✓ | - |
| `20` | `unknown` | ✓ | - |
| `0` | `unknown` | ✓ | - |
| `For` | `unknown` | ✓ | - |
| `SignificanceResult` | `unknown` | ✓ | - |
| `For` | `unknown` | ✓ | - |
| `hypergeom` | `unknown` | ✓ | - |
| `c` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `alternative` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `else` | `oddsratio` | ✓ | - |
| `n1` | `unknown` | ✓ | - |
| `n2` | `unknown` | ✓ | - |
| `n` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `elif` | `unknown` | ✓ | - |
| `elif` | `unknown` | ✓ | - |
| `else` | `msg` | ✓ | - |
| `pvalue` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `elif` | `unknown` | ✓ | - |
| `else` | `message` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `x` | `unknown` | ✓ | - |
| `colsums` | `unknown` | ✓ | - |
| `rowsums` | `unknown` | ✓ | - |
| `X` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `method` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `rng` | `unknown` | ✓ | - |
| `shape` | `unknown` | ✓ | - |
| `colsums` | `unknown` | ✓ | - |
| `rowsums` | `unknown` | ✓ | - |
| `totsum` | `unknown` | ✓ | - |
| `X` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `r` | `unknown` | ✓ | - |
| `x` | `unknown` | ✓ | - |
| `for` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `r` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `of` | `unknown` | ✓ | - |
| `Like` | `unknown` | ✓ | - |
| `this` | `unknown` | ✓ | - |
| `Correlations` | `unknown` | ✓ | - |
| `correlations` | `unknown` | ✓ | - |
| `imply` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `producing` | `unknown` | ✓ | - |
| `as` | `unknown` | ✓ | - |
| `p` | `unknown` | ✓ | - |
| `the` | `unknown` | ✓ | - |
| `observations` | `unknown` | ✓ | - |
| `Examples` | `unknown` | ✓ | - |
| `Parameters` | `unknown` | ✓ | - |
| `a` | `unknown` | ✓ | - |
| `axis` | `int or None, optional` | ✓ | - |
| `nan_policy` | `unknown` | ✓ | - |
| `alternative` | `unknown` | ✓ | - |
| `Returns` | `unknown` | ✓ | - |
| `res` | `SignificanceResult` | ✓ | - |
| `Raises` | `unknown` | ✓ | - |
| `ValueError` | `unknown` | ✓ | - |
| `Warns` | `unknown` | ✓ | - |
| `See` | `unknown` | ✓ | - |
| `References` | `unknown` | ✓ | - |

**Schema: `TtestResult`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Result` | `unknown` | ✓ | - |
| `See` | `unknown` | ✓ | - |
| `information` | `unknown` | ✓ | - |
| `the` | `unknown` | ✓ | - |
| `Attributes` | `unknown` | ✓ | - |
| `statistic` | `float or array` | ✓ | - |
| `pvalue` | `float or array` | ✓ | - |
| `df` | `float or array` | ✓ | - |
| `Methods` | `unknown` | ✓ | - |
| `confidence_interval` | `unknown` | ✓ | - |
| `xp` | `unknown` | ✓ | - |
| `alternative` | `unknown` | ✓ | - |
| `alternative` | `unknown` | ✓ | - |
| `alternative` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `This` | `unknown` | ✓ | - |
| `population` | `unknown` | ✓ | - |
| `Parameters` | `unknown` | ✓ | - |
| `a` | `array_like` | ✓ | - |
| `popmean` | `float or array_like` | ✓ | - |
| `axis` | `int or None, optional` | ✓ | - |
| `nan_policy` | `unknown` | ✓ | - |
| `alternative` | `unknown` | ✓ | - |
| `Returns` | `unknown` | ✓ | - |
| `result` | `unknown` | ✓ | - |
| `Notes` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `when` | `unknown` | ✓ | - |
| `the` | `unknown` | ✓ | - |
| `Examples` | `unknown` | ✓ | - |
| `Suppose` | `unknown` | ✓ | - |
| `is` | `unknown` | ✓ | - |
| `reject` | `unknown` | ✓ | - |
| `less` | `unknown` | ✓ | - |
| `When` | `unknown` | ✓ | - |
| `has` | `unknown` | ✓ | - |
| `hypothesis` | `unknown` | ✓ | - |
| `TtestResult` | `unknown` | ✓ | - |
| `As` | `unknown` | ✓ | - |
| `we` | `unknown` | ✓ | - |
| `When` | `unknown` | ✓ | - |
| `of` | `unknown` | ✓ | - |
| `TtestResult` | `unknown` | ✓ | - |
| `Indeed` | `unknown` | ✓ | - |
| `null` | `unknown` | ✓ | - |
| `of` | `unknown` | ✓ | - |
| `However` | `unknown` | ✓ | - |
| `one` | `unknown` | ✓ | - |
| `0` | `unknown` | ✓ | - |
| `expect` | `unknown` | ✓ | - |
| `TtestResult` | `unknown` | ✓ | - |
| `Unsurprisingly` | `unknown` | ✓ | - |
| `reject` | `unknown` | ✓ | - |
| `Note` | `unknown` | ✓ | - |
| `hypothesis` | `unknown` | ✓ | - |
| `1` | `unknown` | ✓ | - |
| `uniform` | `unknown` | ✓ | - |
| `mistakenly` | `unknown` | ✓ | - |
| `mean` | `unknown` | ✓ | - |
| `ConfidenceInterval` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `minimum` | `unknown` | ✓ | - |
| `p` | `unknown` | ✓ | - |
| `Under` | `unknown` | ✓ | - |
| `is` | `unknown` | ✓ | - |
| `to` | `unknown` | ✓ | - |
| `953` | `unknown` | ✓ | - |
| `xp` | `unknown` | ✓ | - |
| `a` | `unknown` | ✓ | - |
| `a` | `unknown` | ✓ | - |
| `n` | `unknown` | ✓ | - |
| `df` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `mean` | `unknown` | ✓ | - |
| `try` | `popmean` | ✓ | - |
| `except` | `unknown` | ✓ | - |
| `d` | `unknown` | ✓ | - |
| `v` | `unknown` | ✓ | - |
| `denom` | `unknown` | ✓ | - |
| `with` | `unknown` | ✓ | - |
| `dist` | `unknown` | ✓ | - |
| `prob` | `unknown` | ✓ | - |
| `prob` | `unknown` | ✓ | - |
| `df` | `unknown` | ✓ | - |
| `df` | `unknown` | ✓ | - |
| `alternative_num` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `dtype` | `unknown` | ✓ | - |
| `xp` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `confidence_level` | `unknown` | ✓ | - |
| `inf` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `elif` | `unknown` | ✓ | - |
| `elif` | `unknown` | ✓ | - |
| `else` | `unknown` | ✓ | - |
| `low` | `unknown` | ✓ | - |
| `low` | `unknown` | ✓ | - |
| `high` | `unknown` | ✓ | - |
| `high` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `xp` | `unknown` | ✓ | - |
| `d` | `unknown` | ✓ | - |
| `with` | `unknown` | ✓ | - |
| `dist` | `unknown` | ✓ | - |
| `prob` | `unknown` | ✓ | - |
| `prob` | `unknown` | ✓ | - |
| `t` | `unknown` | ✓ | - |
| `prob` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `xp` | `unknown` | ✓ | - |
| `vn1` | `unknown` | ✓ | - |
| `vn2` | `unknown` | ✓ | - |
| `with` | `unknown` | ✓ | - |
| `df` | `unknown` | ✓ | - |
| `denom` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `xp` | `unknown` | ✓ | - |
| `v1` | `unknown` | ✓ | - |
| `v2` | `unknown` | ✓ | - |
| `df` | `unknown` | ✓ | - |
| `svar` | `unknown` | ✓ | - |
| `denom` | `unknown` | ✓ | - |
| `df` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `Ttest_indResult` | `unknown` | ✓ | - |
| `r` | `unknown` | ✓ | - |
| `T` | `unknown` | ✓ | - |
| `This` | `unknown` | ✓ | - |
| `samples` | `unknown` | ✓ | - |
| `Parameters` | `unknown` | ✓ | - |
| `mean1` | `array_like` | ✓ | - |
| `std1` | `array_like` | ✓ | - |
| `nobs1` | `array_like` | ✓ | - |
| `mean2` | `array_like` | ✓ | - |
| `std2` | `array_like` | ✓ | - |
| `nobs2` | `array_like` | ✓ | - |
| `equal_var` | `bool, optional` | ✓ | - |
| `alternative` | `unknown` | ✓ | - |
| `Returns` | `unknown` | ✓ | - |
| `statistic` | `float or array` | ✓ | - |
| `pvalue` | `float or array` | ✓ | - |
| `See` | `unknown` | ✓ | - |
| `scipy` | `unknown` | ✓ | - |
| `Notes` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `standard` | `unknown` | ✓ | - |
| `greater` | `unknown` | ✓ | - |
| `This` | `unknown` | ✓ | - |
| `are` | `unknown` | ✓ | - |
| `negative` | `unknown` | ✓ | - |
| `as` | `unknown` | ✓ | - |
| `respectively` | `unknown` | ✓ | - |
| `References` | `unknown` | ✓ | - |
| `Examples` | `unknown` | ✓ | - |
| `Suppose` | `unknown` | ✓ | - |
| `Sample` | `unknown` | ✓ | - |
| `Apply` | `unknown` | ✓ | - |
| `variances` | `unknown` | ✓ | - |
| `Ttest_indResult` | `unknown` | ✓ | - |
| `For` | `unknown` | ✓ | - |
| `were` | `unknown` | ✓ | - |
| `TtestResult` | `unknown` | ✓ | - |
| `Suppose` | `unknown` | ✓ | - |
| `compare` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `and` | `unknown` | ✓ | - |
| `Ttest_indResult` | `unknown` | ✓ | - |
| `For` | `unknown` | ✓ | - |
| `arrays` | `unknown` | ✓ | - |
| `TtestResult` | `unknown` | ✓ | - |
| `xp` | `unknown` | ✓ | - |
| `mean1` | `unknown` | ✓ | - |
| `std1` | `unknown` | ✓ | - |
| `mean2` | `unknown` | ✓ | - |
| `std2` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `else` | `df, denom` | ✓ | - |
| `res` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `Calculate` | `unknown` | ✓ | - |
| `This` | `unknown` | ✓ | - |
| `have` | `unknown` | ✓ | - |
| `populations` | `unknown` | ✓ | - |
| `Parameters` | `unknown` | ✓ | - |
| `a` | `unknown` | ✓ | - |
| `axis` | `int or None, optional` | ✓ | - |
| `equal_var` | `bool, optional` | ✓ | - |
| `nan_policy` | `unknown` | ✓ | - |
| `alternative` | `unknown` | ✓ | - |
| `trim` | `float, optional` | ✓ | - |
| `method` | `ResamplingMethod, optional` | ✓ | - |
| `Returns` | `unknown` | ✓ | - |
| `result` | `unknown` | ✓ | - |
| `Notes` | `unknown` | ✓ | - |
| `Suppose` | `unknown` | ✓ | - |
| `we` | `unknown` | ✓ | - |
| `population` | `unknown` | ✓ | - |
| `petal` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `of` | `unknown` | ✓ | - |
| `as` | `unknown` | ✓ | - |
| `samples` | `unknown` | ✓ | - |
| `A` | `unknown` | ✓ | - |
| `our` | `unknown` | ✓ | - |
| `we` | `unknown` | ✓ | - |
| `If` | `unknown` | ✓ | - |
| `against` | `unknown` | ✓ | - |
| `By` | `unknown` | ✓ | - |
| `observed` | `unknown` | ✓ | - |
| `It` | `unknown` | ✓ | - |
| `passing` | `unknown` | ✓ | - |
| `where` | `unknown` | ✓ | - |
| `forming` | `unknown` | ✓ | - |
| `the` | `unknown` | ✓ | - |
| `or` | `unknown` | ✓ | - |
| `repeatedly` | `unknown` | ✓ | - |
| `t` | `unknown` | ✓ | - |
| `data` | `unknown` | ✓ | - |
| `Specifically` | `unknown` | ✓ | - |
| `estimating` | `unknown` | ✓ | - |
| `options` | `unknown` | ✓ | - |
| `When` | `unknown` | ✓ | - |
| `are` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `more` | `unknown` | ✓ | - |
| `assumptions` | `unknown` | ✓ | - |
| `Use` | `unknown` | ✓ | - |
| `called` | `unknown` | ✓ | - |
| `difference` | `unknown` | ✓ | - |
| `and` | `unknown` | ✓ | - |
| `recommended` | `unknown` | ✓ | - |
| `with` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `when` | `unknown` | ✓ | - |
| `negative` | `unknown` | ✓ | - |
| `References` | `unknown` | ✓ | - |
| `Examples` | `unknown` | ✓ | - |
| `Test` | `unknown` | ✓ | - |
| `TtestResult` | `unknown` | ✓ | - |
| `TtestResult` | `unknown` | ✓ | - |
| `TtestResult` | `unknown` | ✓ | - |
| `TtestResult` | `unknown` | ✓ | - |
| `When` | `unknown` | ✓ | - |
| `unequal` | `unknown` | ✓ | - |
| `TtestResult` | `unknown` | ✓ | - |
| `TtestResult` | `unknown` | ✓ | - |
| `T` | `unknown` | ✓ | - |
| `TtestResult` | `unknown` | ✓ | - |
| `TtestResult` | `unknown` | ✓ | - |
| `Take` | `unknown` | ✓ | - |
| `Use` | `unknown` | ✓ | - |
| `using` | `unknown` | ✓ | - |
| `have` | `unknown` | ✓ | - |
| `TtestResult` | `unknown` | ✓ | - |
| `xp` | `unknown` | ✓ | - |
| `a` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `result_shape` | `unknown` | ✓ | - |
| `NaN` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `alternative_nums` | `unknown` | ✓ | - |
| `n1` | `unknown` | ✓ | - |
| `n2` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `else` | `message` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `else` | `df, denom` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `else` | `unknown` | ✓ | - |
| `df` | `unknown` | ✓ | - |
| `df` | `unknown` | ✓ | - |
| `estimate` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `test` | `unknown` | ✓ | - |
| `method` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `res` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `a` | `unknown` | ✓ | - |
| `n` | `unknown` | ✓ | - |
| `g` | `unknown` | ✓ | - |
| `v` | `unknown` | ✓ | - |
| `n` | `unknown` | ✓ | - |
| `m` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `a_win` | `unknown` | ✓ | - |
| `nans_indices` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modeling_phimoe.py

- **File**: `venv\Lib\site-packages\transformers\models\phimoe\modeling_phimoe.py`
- **Captured**: 4/28/2026, 12:57:40 PM
- **Category**: bugfix
**Summary:** Modified modeling_phimoe.py: 917 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\phimoe\modeling_phimoe.py` (+917 / -0)
**Schema: `PhimoePreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `PhimoeConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_skip_keys_device_placement` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `_supports_flex_attn` | `unknown` | ✓ | - |
| `_can_compile_fullgraph` | `unknown` | ✓ | - |
| `_supports_attention_backend` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |

**Schema: `PhimoeModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `gate_logits` | `torch` | ✓ | - |
| `num_experts` | `int` | ✓ | - |
| `top_k` | `unknown` | ✓ | - |
| `attention_mask` | `torch` | ✓ | - |
| `r` | `unknown` | ✓ | - |
| `Computes` | `unknown` | ✓ | - |
| `See` | `unknown` | ✓ | - |
| `function` | `unknown` | ✓ | - |
| `experts` | `unknown` | ✓ | - |
| `Args` | `gate_logits` | ✓ | - |
| `Returns` | `The auxiliary loss` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `routing_weights` | `unknown` | ✓ | - |
| `_` | `unknown` | ✓ | - |
| `expert_mask` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `else` | `batch_size, sequence_length` | ✓ | - |
| `overall_loss` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |

**Schema: `PhimoeForCausalLM`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_tied_weights_keys` | `unknown` | ✓ | - |
| `_tp_plan` | `unknown` | ✓ | - |
| `_pp_plan` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modular_phimoe.py

- **File**: `venv\Lib\site-packages\transformers\models\phimoe\modular_phimoe.py`
- **Captured**: 4/28/2026, 12:57:38 PM
- **Category**: bugfix
**Summary:** Modified modular_phimoe.py: 411 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\phimoe\modular_phimoe.py` (+411 / -0)
**Schema: `PhimoePreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_can_record_outputs` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in _projection.py

- **File**: `venv\Lib\site-packages\plotly\graph_objs\layout\geo\_projection.py`
- **Captured**: 4/28/2026, 12:57:36 PM
- **Category**: bugfix
**Summary:** Modified _projection.py: 252 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\plotly\graph_objs\layout\geo\_projection.py` (+252 / -0)
**Schema: `Projection`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_parent_path_str` | `unknown` | ✓ | - |
| `_path_str` | `unknown` | ✓ | - |
| `_valid_props` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in _core_metadata.py

- **File**: `venv\Lib\site-packages\setuptools\_core_metadata.py`
- **Captured**: 4/28/2026, 12:57:34 PM
- **Category**: bugfix
**Summary:** Modified _core_metadata.py: 338 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\setuptools\_core_metadata.py` (+338 / -0)

### [New] [bugfix] Changes in build_meta.py

- **File**: `venv\Lib\site-packages\setuptools\build_meta.py`
- **Captured**: 4/28/2026, 12:57:30 PM
- **Category**: bugfix
**Summary:** Modified build_meta.py: 557 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\setuptools\build_meta.py` (+557 / -0)

### [New] [bugfix] Changes in setupcfg.py

- **File**: `venv\Lib\site-packages\setuptools\config\setupcfg.py`
- **Captured**: 4/28/2026, 12:57:27 PM
- **Category**: bugfix
**Summary:** Modified setupcfg.py: 783 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\setuptools\config\setupcfg.py` (+783 / -0)

### [New] [bugfix] Changes in error_reporting.py

- **File**: `venv\Lib\site-packages\setuptools\config\_validate_pyproject\error_reporting.py`
- **Captured**: 4/28/2026, 12:57:25 PM
- **Category**: bugfix
**Summary:** Modified error_reporting.py: 337 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\setuptools\config\_validate_pyproject\error_reporting.py` (+337 / -0)
**Schema: `ValidationError`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `This` | `unknown` | ✓ | - |
| `by` | `unknown` | ✓ | - |
| `Depending` | `unknown` | ✓ | - |
| `the` | `unknown` | ✓ | - |
| `summary` | `unknown` | ✓ | - |
| `details` | `unknown` | ✓ | - |
| `_original_message` | `unknown` | ✓ | - |
| `try` | `yield` | ✓ | - |
| `except` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in fastjsonschema_exceptions.py

- **File**: `venv\Lib\site-packages\setuptools\config\_validate_pyproject\fastjsonschema_exceptions.py`
- **Captured**: 4/28/2026, 12:57:21 PM
- **Category**: bugfix
**Summary:** Modified fastjsonschema_exceptions.py: 52 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\setuptools\config\_validate_pyproject\fastjsonschema_exceptions.py` (+52 / -0)
**Schema: `JsonSchemaValueException`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Exception` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in _vertex.py

- **File**: `venv\Lib\site-packages\scipy\optimize\_shgo_lib\_vertex.py`
- **Captured**: 4/28/2026, 12:57:14 PM
- **Category**: bugfix
**Summary:** Modified _vertex.py: 461 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\scipy\optimize\_shgo_lib\_vertex.py` (+461 / -0)
**Schema: `VertexScalarField`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Add` | `unknown` | ✓ | - |
| `the` | `unknown` | ✓ | - |

**Schema: `VertexVectorField`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Add` | `unknown` | ✓ | - |
| `the` | `unknown` | ✓ | - |

**Schema: `VertexCube`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `differential` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modeling_pi0.py

- **File**: `venv\Lib\site-packages\transformers\models\pi0\modeling_pi0.py`
- **Captured**: 4/28/2026, 12:57:13 PM
- **Category**: bugfix
**Summary:** Modified modeling_pi0.py: 393 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\pi0\modeling_pi0.py` (+393 / -0)
**Schema: `PI0PreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `PI0Config` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `main_input_name` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_skip_keys_device_placement` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `_supports_flex_attn` | `unknown` | ✓ | - |
| `_can_compile_fullgraph` | `unknown` | ✓ | - |
| `_supports_attention_backend` | `unknown` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modular_pi0.py

- **File**: `venv\Lib\site-packages\transformers\models\pi0\modular_pi0.py`
- **Captured**: 4/28/2026, 12:57:11 PM
- **Category**: bugfix
**Summary:** Modified modular_pi0.py: 650 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\pi0\modular_pi0.py` (+650 / -0)
**Schema: `PI0PreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `PI0Config` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `main_input_name` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_skip_keys_device_placement` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `_supports_flex_attn` | `unknown` | ✓ | - |
| `_can_compile_fullgraph` | `unknown` | ✓ | - |
| `_supports_attention_backend` | `unknown` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modeling_pix2struct.py

- **File**: `venv\Lib\site-packages\transformers\models\pix2struct\modeling_pix2struct.py`
- **Captured**: 4/28/2026, 12:57:05 PM
- **Category**: bugfix
**Summary:** Modified modeling_pix2struct.py: 1351 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\pix2struct\modeling_pix2struct.py` (+1351 / -0)
**Schema: `Pix2StructPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Pix2StructConfig` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `_can_compile_fullgraph` | `unknown` | ✓ | - |

**Schema: `Pix2StructVisionModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Pix2StructVisionConfig` | ✓ | - |
| `main_input_name` | `unknown` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |

**Schema: `Pix2StructTextModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Pix2StructTextConfig` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_tied_weights_keys` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `A` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in dist.py

- **File**: `venv\Lib\site-packages\setuptools\dist.py`
- **Captured**: 4/28/2026, 12:57:02 PM
- **Category**: bugfix
**Summary:** Modified dist.py: 1125 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\setuptools\dist.py` (+1125 / -0)

### [New] [bugfix] Changes in errors.py

- **File**: `venv\Lib\site-packages\setuptools\errors.py`
- **Captured**: 4/28/2026, 12:57:00 PM
- **Category**: bugfix
**Summary:** Modified errors.py: 68 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\setuptools\errors.py` (+68 / -0)
**Schema: `RemovedCommandError`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Since` | `unknown` | ✓ | - |
| `from` | `unknown` | ✓ | - |
| `error` | `unknown` | ✓ | - |
| `removed` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modeling_pixio.py

- **File**: `venv\Lib\site-packages\transformers\models\pixio\modeling_pixio.py`
- **Captured**: 4/28/2026, 12:56:51 PM
- **Category**: bugfix
**Summary:** Modified modeling_pixio.py: 508 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\pixio\modeling_pixio.py` (+508 / -0)
**Schema: `PixioPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `PixioConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `main_input_name` | `unknown` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_supports_flex_attn` | `unknown` | ✓ | - |
| `_supports_attention_backend` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |

**Schema: `PixioModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `custom_intro` | `unknown` | ✓ | - |
| `Pixio` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modular_pixio.py

- **File**: `venv\Lib\site-packages\transformers\models\pixio\modular_pixio.py`
- **Captured**: 4/28/2026, 12:56:49 PM
- **Category**: bugfix
**Summary:** Modified modular_pixio.py: 319 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\pixio\modular_pixio.py` (+319 / -0)
**Schema: `PixioPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_can_record_outputs` | `unknown` | ✓ | - |

**Schema: `PixioModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `custom_intro` | `unknown` | ✓ | - |
| `Pixio` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in formal.py

- **File**: `venv\Lib\site-packages\sympy\series\formal.py`
- **Captured**: 4/28/2026, 12:56:47 PM
- **Category**: bugfix
**Summary:** Modified formal.py: 1864 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\sympy\series\formal.py` (+1864 / -0)
**Schema: `FormalPowerSeries`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Represents` | `unknown` | ✓ | - |
| `Explanation` | `unknown` | ✓ | - |
| `No` | `unknown` | ✓ | - |
| `a` | `unknown` | ✓ | - |
| `For` | `unknown` | ✓ | - |
| `See` | `unknown` | ✓ | - |
| `sympy` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in fourier.py

- **File**: `venv\Lib\site-packages\sympy\series\fourier.py`
- **Captured**: 4/28/2026, 12:56:44 PM
- **Category**: bugfix
**Summary:** Modified fourier.py: 812 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\sympy\series\fourier.py` (+812 / -0)
**Schema: `FourierSeries`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `Explanation` | `unknown` | ✓ | - |
| `This` | `unknown` | ✓ | - |
| `No` | `unknown` | ✓ | - |
| `For` | `unknown` | ✓ | - |
| `docstring` | `unknown` | ✓ | - |
| `See` | `unknown` | ✓ | - |
| `sympy` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in sequences.py

- **File**: `venv\Lib\site-packages\sympy\series\sequences.py`
- **Captured**: 4/28/2026, 12:56:43 PM
- **Category**: bugfix
**Summary:** Modified sequences.py: 1240 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\sympy\series\sequences.py` (+1240 / -0)
**Schema: `EmptySequence`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `The` | `unknown` | ✓ | - |
| `Examples` | `unknown` | ✓ | - |
| `EmptySequence` | `unknown` | ✓ | - |
| `SeqPer` | `unknown` | ✓ | - |
| `EmptySequence` | `unknown` | ✓ | - |
| `EmptySequence` | `unknown` | ✓ | - |

**Schema: `SeqExpr`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Various` | `unknown` | ✓ | - |
| `Examples` | `unknown` | ✓ | - |
| `Interval` | `unknown` | ✓ | - |
| `11` | `unknown` | ✓ | - |
| `sympy` | `unknown` | ✓ | - |
| `sympy` | `unknown` | ✓ | - |

**Schema: `RecursiveSeq`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `A` | `unknown` | ✓ | - |
| `Explanation` | `unknown` | ✓ | - |
| `That` | `unknown` | ✓ | - |
| `previous` | `unknown` | ✓ | - |
| `for` | `unknown` | ✓ | - |
| `SymPy` | `unknown` | ✓ | - |
| `Parameters` | `unknown` | ✓ | - |
| `recurrence` | `SymPy expression defining recurrence` | ✓ | - |
| `yn` | `applied undefined function` | ✓ | - |
| `n` | `symbolic argument` | ✓ | - |
| `initial` | `iterable with length equal to the degree of the recurrence` | ✓ | - |
| `start` | `start value of sequence` | ✓ | - |
| `Examples` | `unknown` | ✓ | - |
| `2` | `unknown` | ✓ | - |
| `Eq` | `unknown` | ✓ | - |
| `2` | `unknown` | ✓ | - |
| `See` | `unknown` | ✓ | - |
| `sympy` | `unknown` | ✓ | - |
| `Returns` | `unknown` | ✓ | - |
| `Explanation` | `unknown` | ✓ | - |
| `If` | `unknown` | ✓ | - |
| `otherwise` | `unknown` | ✓ | - |
| `Examples` | `unknown` | ✓ | - |
| `SeqFormula` | `unknown` | ✓ | - |
| `SeqPer` | `unknown` | ✓ | - |
| `See` | `unknown` | ✓ | - |
| `sympy` | `unknown` | ✓ | - |
| `sympy` | `unknown` | ✓ | - |
| `seq` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `else` | `return SeqFormula` | ✓ | - |

**Schema: `SeqExprOp`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Base` | `unknown` | ✓ | - |
| `Examples` | `unknown` | ✓ | - |
| `Interval` | `unknown` | ✓ | - |
| `6` | `unknown` | ✓ | - |
| `sympy` | `unknown` | ✓ | - |
| `sympy` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modeling_pixtral.py

- **File**: `venv\Lib\site-packages\transformers\models\pixtral\modeling_pixtral.py`
- **Captured**: 4/28/2026, 12:56:36 PM
- **Category**: bugfix
**Summary:** Modified modeling_pixtral.py: 486 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\pixtral\modeling_pixtral.py` (+486 / -0)
**Schema: `PixtralPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `PixtralVisionConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `main_input_name` | `unknown` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_supports_attention_backend` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `_supports_flex_attn` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |
| `dtype` | `unknown` | ✓ | - |
| `device` | `unknown` | ✓ | - |
| `seq_len` | `unknown` | ✓ | - |
| `d_min` | `unknown` | ✓ | - |
| `causal_mask` | `unknown` | ✓ | - |
| `block_end_idx` | `unknown` | ✓ | - |
| `block_start_idx` | `unknown` | ✓ | - |
| `for` | `unknown` | ✓ | - |
| `causal_mask` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in _trustregion_exact.py

- **File**: `venv\Lib\site-packages\scipy\optimize\_trustregion_exact.py`
- **Captured**: 4/28/2026, 12:56:32 PM
- **Category**: bugfix
**Summary:** Modified _trustregion_exact.py: 459 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\scipy\optimize\_trustregion_exact.py` (+459 / -0)
**Schema: `IterativeSubproblem`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Notes` | `unknown` | ✓ | - |
| `This` | `unknown` | ✓ | - |
| `which` | `unknown` | ✓ | - |
| `that` | `unknown` | ✓ | - |
| `References` | `unknown` | ✓ | - |
| `UPDATE_COEFF` | `unknown` | ✓ | - |
| `MAXITER_DEFAULT` | `unknown` | ✓ | - |
| `EPS` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in _zaxis.py

- **File**: `venv\Lib\site-packages\plotly\graph_objs\layout\scene\_zaxis.py`
- **Captured**: 4/28/2026, 12:56:29 PM
- **Category**: bugfix
**Summary:** Modified _zaxis.py: 2129 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\plotly\graph_objs\layout\scene\_zaxis.py` (+2129 / -0)
**Schema: `ZAxis`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_parent_path_str` | `unknown` | ✓ | - |
| `_path_str` | `unknown` | ✓ | - |
| `_valid_props` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modeling_plbart.py

- **File**: `venv\Lib\site-packages\transformers\models\plbart\modeling_plbart.py`
- **Captured**: 4/28/2026, 12:56:26 PM
- **Category**: bugfix
**Summary:** Modified modeling_plbart.py: 1150 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\plbart\modeling_plbart.py` (+1150 / -0)
**Schema: `PLBartPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `PLBartConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `_supports_flex_attn` | `unknown` | ✓ | - |

**Schema: `PLBartEncoder`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Transformer` | `unknown` | ✓ | - |
| `Args` | `config` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |

**Schema: `PLBartDecoder`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Transformer` | `unknown` | ✓ | - |
| `Args` | `config` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |
| `Shift` | `unknown` | ✓ | - |
| `have` | `unknown` | ✓ | - |
| `prev_output_tokens` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `prev_output_tokens` | `unknown` | ✓ | - |
| `index_of_eos` | `unknown` | ✓ | - |
| `decoder_start_tokens` | `unknown` | ✓ | - |
| `prev_output_tokens` | `unknown` | ✓ | - |
| `prev_output_tokens` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |

**Schema: `PLBartModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_tied_weights_keys` | `unknown` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |

**Schema: `PLBartForConditionalGeneration`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `base_model_prefix` | `unknown` | ✓ | - |
| `_keys_to_ignore_on_load_missing` | `unknown` | ✓ | - |
| `_tied_weights_keys` | `unknown` | ✓ | - |

**Schema: `PLBartDecoderWrapper`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `This` | `unknown` | ✓ | - |
| `used` | `unknown` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `PLBART` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modular_plbart.py

- **File**: `venv\Lib\site-packages\transformers\models\plbart\modular_plbart.py`
- **Captured**: 4/28/2026, 12:56:25 PM
- **Category**: bugfix
**Summary:** Modified modular_plbart.py: 392 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\plbart\modular_plbart.py` (+392 / -0)
**Schema: `PLBartPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `PLBartConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `_supports_flex_attn` | `unknown` | ✓ | - |

**Schema: `PLBartModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_tied_weights_keys` | `unknown` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |

**Schema: `PLBartForConditionalGeneration`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `base_model_prefix` | `unknown` | ✓ | - |
| `_keys_to_ignore_on_load_missing` | `unknown` | ✓ | - |
| `_tied_weights_keys` | `unknown` | ✓ | - |

### [New] [enhancement] Changes in index.html

- **File**: `venv\Lib\site-packages\setuptools\tests\indexes\test_links_priority\simple\foobar\index.html`
- **Captured**: 4/28/2026, 12:56:21 PM
- **Category**: enhancement
**Summary:** Modified index.html: 5 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\setuptools\tests\indexes\test_links_priority\simple\foobar\index.html` (+5 / -0)

### [New] [bugfix] Changes in modeling_poolformer.py

- **File**: `venv\Lib\site-packages\transformers\models\poolformer\modeling_poolformer.py`
- **Captured**: 4/28/2026, 12:56:15 PM
- **Category**: bugfix
**Summary:** Modified modeling_poolformer.py: 383 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\poolformer\modeling_poolformer.py` (+383 / -0)
**Schema: `PoolFormerPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `PoolFormerConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `main_input_name` | `unknown` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |

### [bugfix] Changes in preload.js

- **File**: `desktop\preload.js`
- **Captured**: 4/28/2026, 12:56:13 PM
- **Category**: bugfix
**Summary:** Modified preload.js: 49 lines added, 0 lines removed.
**Files Modified:**
  - `desktop\preload.js` (+49 / -0)

### [New] [bugfix] Changes in _scripts.py

- **File**: `venv\Lib\site-packages\setuptools\_scripts.py`
- **Captured**: 4/28/2026, 12:56:10 PM
- **Category**: bugfix
**Summary:** Modified _scripts.py: 362 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\setuptools\_scripts.py` (+362 / -0)

### [New] [bugfix] Changes in _static.py

- **File**: `venv\Lib\site-packages\setuptools\_static.py`
- **Captured**: 4/28/2026, 12:56:08 PM
- **Category**: bugfix
**Summary:** Modified _static.py: 189 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\setuptools\_static.py` (+189 / -0)

### [New] [bugfix] Changes in modeling_pop2piano.py

- **File**: `venv\Lib\site-packages\transformers\models\pop2piano\modeling_pop2piano.py`
- **Captured**: 4/28/2026, 12:56:04 PM
- **Category**: bugfix
**Summary:** Modified modeling_pop2piano.py: 1084 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\pop2piano\modeling_pop2piano.py` (+1084 / -0)
**Schema: `Pop2PianoPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Pop2PianoConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `output_modalities` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_can_compile_fullgraph` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_keep_in_fp32_modules` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in test_config_discovery.py

- **File**: `venv\Lib\site-packages\setuptools\tests\test_config_discovery.py`
- **Captured**: 4/28/2026, 12:56:00 PM
- **Category**: bugfix
**Summary:** Modified test_config_discovery.py: 648 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\setuptools\tests\test_config_discovery.py` (+648 / -0)
**API Endpoints** (`test_config_discovery.py`):

| Method | Route | Handler | Middleware |
|--------|-------|---------|------------|
| `PATH("PKG", DIST` | `pkg` | find_package_path | - |

### [bugfix] Changes in main.js

- **File**: `desktop\main.js`
- **Captured**: 4/28/2026, 12:55:59 PM
- **Category**: bugfix
**Summary:** Modified main.js: 223 lines added, 0 lines removed.
**Files Modified:**
  - `desktop\main.js` (+223 / -0)
**Environment Variables:**

| Variable | Required | Default |
|----------|----------|---------|
| `NEXUS_DEV_URL` | **Yes** | - |
| `NEXUS_BACKEND_URL` | No | `http://localhost:8000` |

### [New] [bugfix] Changes in test_epathtools.py

- **File**: `venv\Lib\site-packages\sympy\simplify\tests\test_epathtools.py`
- **Captured**: 4/28/2026, 12:55:54 PM
- **Category**: bugfix
**Summary:** Modified test_epathtools.py: 91 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\sympy\simplify\tests\test_epathtools.py` (+91 / -0)
**API Endpoints** (`test_epathtools.py`):

| Method | Route | Handler | Middleware |
|--------|-------|---------|------------|
| `PATH("/*", EXPR` | `/*` | - | - |
| `PATH("/*/*", EXPR` | `/*/*` | - | - |
| `PATH("/*/*/*", EXPR` | `/*/*/*` | - | - |
| `PATH("/*/*/*/*", EXPR` | `/*/*/*/*` | - | - |
| `PATH("/[:]", EXPR` | `/[:]` | - | - |
| `PATH("/[:]/[:]", EXPR` | `/[:]/[:]` | - | - |
| `PATH("/[:]/[:]/[:]", EXPR` | `/[:]/[:]/[:]` | - | - |
| `PATH("/[:]/[:]/[:]/[:]", EXPR` | `/[:]/[:]/[:]/[:]` | - | - |
| `PATH("/*/[:]", EXPR` | `/*/[:]` | - | - |
| `PATH("/*/[0]", EXPR` | `/*/[0]` | - | - |
| `PATH("/*/[1]", EXPR` | `/*/[1]` | - | - |
| `PATH("/*/[2]", EXPR` | `/*/[2]` | - | - |
| `PATH("/*/INT", EXPR` | `/*/int` | - | - |
| `PATH("/*/SYMBOL", EXPR` | `/*/Symbol` | - | - |
| `PATH("/*/TUPLE", EXPR` | `/*/tuple` | - | - |
| `PATH("/*/__ITER__?", EXPR` | `/*/__iter__?` | - | - |
| `PATH("/*/INT|TUPLE", EXPR` | `/*/int|tuple` | - | - |
| `PATH("/*/SYMBOL|TUPLE", EXPR` | `/*/Symbol|tuple` | - | - |
| `PATH("/*/INT|SYMBOL|TUPLE", EXPR` | `/*/int|Symbol|tuple` | - | - |
| `PATH("/*/INT|__ITER__?", EXPR` | `/*/int|__iter__?` | - | - |
| `PATH("/*/SYMBOL|__ITER__?", EXPR` | `/*/Symbol|__iter__?` | - | - |
| `PATH(
        "/*/INT|SYMBOL|__ITER__?", EXPR` | `/*/int|Symbol|__iter__?` | - | - |
| `PATH("/*/[0]/INT", EXPR` | `/*/[0]/int` | - | - |
| `PATH("/*/[0]/SYMBOL", EXPR` | `/*/[0]/Symbol` | - | - |
| `PATH("/*/[0]/INT[1:]", EXPR` | `/*/[0]/int[1:]` | - | - |
| `PATH("/*/[0]/SYMBOL[1:]", EXPR` | `/*/[0]/Symbol[1:]` | - | - |
| `PATH("/SYMBOL", X` | `/Symbol` | - | - |
| `PATH("/*/*/SYMBOL", T` | `/*/*/Symbol` | - | - |
| `PATH(
        "/*/[0]/INT[1:]", EXPR` | `/*/[0]/int[1:]` | - | - |

### [New] [bugfix] Changes in test_config.py

- **File**: `venv\Lib\site-packages\scipy\_lib\tests\test_config.py`
- **Captured**: 4/28/2026, 12:55:51 PM
- **Category**: bugfix
**Summary:** Modified test_config.py: 45 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\scipy\_lib\tests\test_config.py` (+45 / -0)
**API Endpoints** (`test_config.py`):

| Method | Route | Handler | Middleware |
|--------|-------|---------|------------|
| `PATCH` | `scipy.__config__._check_pyyaml` | patch | - |

### [New] [bugfix] Changes in _pep440.py

- **File**: `venv\Lib\site-packages\scipy\_lib\_pep440.py`
- **Captured**: 4/28/2026, 12:55:46 PM
- **Category**: bugfix
**Summary:** Modified _pep440.py: 488 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\scipy\_lib\_pep440.py` (+488 / -0)
**Schema: `LegacyVersion`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_legacy_version_component_re` | `unknown` | ✓ | - |
| `r` | `unknown` | ✓ | - |
| `for` | `unknown` | ✓ | - |
| `yield` | `unknown` | ✓ | - |
| `epoch` | `unknown` | ✓ | - |
| `parts` | `unknown` | ✓ | - |
| `for` | `unknown` | ✓ | - |
| `parts` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `v` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modeling_pp_doclayout_v2.py

- **File**: `venv\Lib\site-packages\transformers\models\pp_doclayout_v2\modeling_pp_doclayout_v2.py`
- **Captured**: 4/28/2026, 12:55:41 PM
- **Category**: bugfix
**Summary:** Modified modeling_pp_doclayout_v2.py: 2481 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\pp_doclayout_v2\modeling_pp_doclayout_v2.py` (+2481 / -0)
**Schema: `PPDocLayoutV2PreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `PPDocLayoutV2Config` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `main_input_name` | `unknown` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_supports_attention_backend` | `unknown` | ✓ | - |
| `_supports_flex_attn` | `unknown` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `PP` | `unknown` | ✓ | - |
| `It` | `unknown` | ✓ | - |
| `between` | `unknown` | ✓ | - |

**Schema: `PPDocLayoutV2ReadingOrder`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_supports_sdpa` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_supports_attention_backend` | `unknown` | ✓ | - |
| `_supports_flex_attn` | `unknown` | ✓ | - |

**Schema: `PPDocLayoutV2ForObjectDetectionOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `logits` | `unknown` | ✓ | - |
| `pred_boxes` | `unknown` | ✓ | - |
| `order_logits` | `unknown` | ✓ | - |
| `last_hidden_state` | `unknown` | ✓ | - |
| `intermediate_hidden_states` | `unknown` | ✓ | - |
| `intermediate_logits` | `unknown` | ✓ | - |
| `intermediate_reference_points` | `unknown` | ✓ | - |
| `intermediate_predicted_corners` | `unknown` | ✓ | - |
| `initial_reference_points` | `unknown` | ✓ | - |
| `init_reference_points` | `unknown` | ✓ | - |
| `enc_topk_logits` | `unknown` | ✓ | - |
| `enc_topk_bboxes` | `unknown` | ✓ | - |
| `enc_outputs_coord_logits` | `unknown` | ✓ | - |
| `denoising_meta_values` | `unknown` | ✓ | - |
| `logits` | `torch` | ✓ | - |
| `pred_boxes` | `torch` | ✓ | - |
| `order_logits` | `tuple[torch` | ✓ | - |
| `last_hidden_state` | `torch` | ✓ | - |
| `intermediate_hidden_states` | `torch` | ✓ | - |
| `intermediate_logits` | `torch` | ✓ | - |
| `intermediate_reference_points` | `torch` | ✓ | - |
| `intermediate_predicted_corners` | `torch` | ✓ | - |
| `initial_reference_points` | `torch` | ✓ | - |
| `decoder_hidden_states` | `tuple[torch` | ✓ | - |
| `decoder_attentions` | `tuple[torch` | ✓ | - |
| `cross_attentions` | `tuple[torch` | ✓ | - |
| `encoder_last_hidden_state` | `torch` | ✓ | - |
| `encoder_hidden_states` | `tuple[torch` | ✓ | - |
| `encoder_attentions` | `tuple[torch` | ✓ | - |
| `init_reference_points` | `tuple[torch` | ✓ | - |
| `enc_topk_logits` | `torch` | ✓ | - |
| `enc_topk_bboxes` | `torch` | ✓ | - |
| `enc_outputs_coord_logits` | `torch` | ✓ | - |
| `denoising_meta_values` | `dict` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `Base` | `unknown` | ✓ | - |

**Schema: `PPDocLayoutV2ModelOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `last_hidden_state` | `unknown` | ✓ | - |
| `intermediate_hidden_states` | `unknown` | ✓ | - |
| `intermediate_logits` | `unknown` | ✓ | - |
| `intermediate_reference_points` | `unknown` | ✓ | - |
| `intermediate_predicted_corners` | `unknown` | ✓ | - |
| `initial_reference_points` | `unknown` | ✓ | - |
| `init_reference_points` | `unknown` | ✓ | - |
| `enc_topk_logits` | `unknown` | ✓ | - |
| `enc_topk_bboxes` | `unknown` | ✓ | - |
| `enc_outputs_coord_logits` | `unknown` | ✓ | - |
| `denoising_meta_values` | `unknown` | ✓ | - |
| `last_hidden_state` | `torch` | ✓ | - |
| `intermediate_hidden_states` | `torch` | ✓ | - |
| `intermediate_logits` | `torch` | ✓ | - |
| `intermediate_reference_points` | `torch` | ✓ | - |
| `intermediate_predicted_corners` | `torch` | ✓ | - |
| `initial_reference_points` | `torch` | ✓ | - |
| `decoder_hidden_states` | `tuple[torch` | ✓ | - |
| `decoder_attentions` | `tuple[torch` | ✓ | - |
| `cross_attentions` | `tuple[torch` | ✓ | - |
| `encoder_last_hidden_state` | `torch` | ✓ | - |
| `encoder_hidden_states` | `tuple[torch` | ✓ | - |
| `encoder_attentions` | `tuple[torch` | ✓ | - |
| `init_reference_points` | `torch` | ✓ | - |
| `enc_topk_logits` | `torch` | ✓ | - |
| `enc_topk_bboxes` | `torch` | ✓ | - |
| `enc_outputs_coord_logits` | `torch` | ✓ | - |
| `denoising_meta_values` | `dict` | ✓ | - |

**Schema: `PPDocLayoutV2DecoderOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `intermediate_hidden_states` | `unknown` | ✓ | - |
| `intermediate_logits` | `unknown` | ✓ | - |
| `intermediate_reference_points` | `unknown` | ✓ | - |
| `intermediate_predicted_corners` | `unknown` | ✓ | - |
| `initial_reference_points` | `unknown` | ✓ | - |
| `cross_attentions` | `unknown` | ✓ | - |
| `last_hidden_state` | `torch` | ✓ | - |
| `intermediate_hidden_states` | `torch` | ✓ | - |
| `intermediate_logits` | `torch` | ✓ | - |
| `intermediate_reference_points` | `torch` | ✓ | - |
| `intermediate_predicted_corners` | `torch` | ✓ | - |
| `initial_reference_points` | `torch` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[torch` | ✓ | - |
| `cross_attentions` | `tuple[torch` | ✓ | - |

**Schema: `PPDocLayoutV2HybridEncoder`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Hybrid` | `unknown` | ✓ | - |
| `a` | `unknown` | ✓ | - |
| `More` | `unknown` | ✓ | - |
| `Args` | `config` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |
| `x` | `unknown` | ✓ | - |
| `x1` | `unknown` | ✓ | - |
| `x2` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |

**Schema: `PPDocLayoutV2Decoder`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_can_record_outputs` | `unknown` | ✓ | - |
| `targets` | `unknown` | ✓ | - |
| `num_queries` | `unknown` | ✓ | - |
| `num_denoising_queries` | `unknown` | ✓ | - |
| `label_noise_ratio` | `unknown` | ✓ | - |
| `box_noise_scale` | `unknown` | ✓ | - |
| `Creates` | `unknown` | ✓ | - |
| `Args` | `targets` | ✓ | - |
| `Returns` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `num_ground_truths` | `unknown` | ✓ | - |
| `device` | `unknown` | ✓ | - |
| `max_gt_num` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `num_groups_denoising_queries` | `unknown` | ✓ | - |
| `num_groups_denoising_queries` | `unknown` | ✓ | - |
| `batch_size` | `unknown` | ✓ | - |
| `input_query_bbox` | `unknown` | ✓ | - |
| `pad_gt_mask` | `unknown` | ✓ | - |
| `for` | `unknown` | ✓ | - |
| `input_query_bbox` | `unknown` | ✓ | - |
| `pad_gt_mask` | `unknown` | ✓ | - |
| `negative_gt_mask` | `unknown` | ✓ | - |
| `negative_gt_mask` | `unknown` | ✓ | - |
| `negative_gt_mask` | `unknown` | ✓ | - |
| `positive_gt_mask` | `unknown` | ✓ | - |
| `positive_gt_mask` | `unknown` | ✓ | - |
| `denoise_positive_idx` | `unknown` | ✓ | - |
| `denoise_positive_idx` | `unknown` | ✓ | - |
| `num_denoising_queries` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `target_size` | `unknown` | ✓ | - |
| `attn_mask` | `unknown` | ✓ | - |
| `attn_mask` | `unknown` | ✓ | - |
| `for` | `unknown` | ✓ | - |
| `denoising_meta_values` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `PP` | `unknown` | ✓ | - |

**Schema: `PPDocLayoutV2Model`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `custom_intro` | `unknown` | ✓ | - |
| `PP` | `unknown` | ✓ | - |
| `decoded` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modular_pp_doclayout_v2.py

- **File**: `venv\Lib\site-packages\transformers\models\pp_doclayout_v2\modular_pp_doclayout_v2.py`
- **Captured**: 4/28/2026, 12:55:39 PM
- **Category**: bugfix
**Summary:** Modified modular_pp_doclayout_v2.py: 1002 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\pp_doclayout_v2\modular_pp_doclayout_v2.py` (+1002 / -0)
**Schema: `PPDocLayoutV2PreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `custom_intro` | `unknown` | ✓ | - |
| `PP` | `unknown` | ✓ | - |
| `It` | `unknown` | ✓ | - |
| `between` | `unknown` | ✓ | - |

**Schema: `PPDocLayoutV2ReadingOrder`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_supports_sdpa` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_supports_attention_backend` | `unknown` | ✓ | - |
| `_supports_flex_attn` | `unknown` | ✓ | - |

**Schema: `PPDocLayoutV2ForObjectDetectionOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `logits` | `unknown` | ✓ | - |
| `pred_boxes` | `unknown` | ✓ | - |
| `order_logits` | `unknown` | ✓ | - |
| `last_hidden_state` | `unknown` | ✓ | - |
| `intermediate_hidden_states` | `unknown` | ✓ | - |
| `intermediate_logits` | `unknown` | ✓ | - |
| `intermediate_reference_points` | `unknown` | ✓ | - |
| `intermediate_predicted_corners` | `unknown` | ✓ | - |
| `initial_reference_points` | `unknown` | ✓ | - |
| `init_reference_points` | `unknown` | ✓ | - |
| `enc_topk_logits` | `unknown` | ✓ | - |
| `enc_topk_bboxes` | `unknown` | ✓ | - |
| `enc_outputs_coord_logits` | `unknown` | ✓ | - |
| `denoising_meta_values` | `unknown` | ✓ | - |
| `logits` | `torch` | ✓ | - |
| `pred_boxes` | `torch` | ✓ | - |
| `order_logits` | `tuple[torch` | ✓ | - |
| `last_hidden_state` | `torch` | ✓ | - |
| `intermediate_hidden_states` | `torch` | ✓ | - |
| `intermediate_logits` | `torch` | ✓ | - |
| `intermediate_reference_points` | `torch` | ✓ | - |
| `intermediate_predicted_corners` | `torch` | ✓ | - |
| `initial_reference_points` | `torch` | ✓ | - |
| `decoder_hidden_states` | `tuple[torch` | ✓ | - |
| `decoder_attentions` | `tuple[torch` | ✓ | - |
| `cross_attentions` | `tuple[torch` | ✓ | - |
| `encoder_last_hidden_state` | `torch` | ✓ | - |
| `encoder_hidden_states` | `tuple[torch` | ✓ | - |
| `encoder_attentions` | `tuple[torch` | ✓ | - |
| `init_reference_points` | `tuple[torch` | ✓ | - |
| `enc_topk_logits` | `torch` | ✓ | - |
| `enc_topk_bboxes` | `torch` | ✓ | - |
| `enc_outputs_coord_logits` | `torch` | ✓ | - |
| `denoising_meta_values` | `dict` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `Base` | `unknown` | ✓ | - |

**Schema: `PPDocLayoutV2ModelOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `pass` | `unknown` | ✓ | - |

**Schema: `PPDocLayoutV2Model`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `custom_intro` | `unknown` | ✓ | - |
| `PP` | `unknown` | ✓ | - |
| `decoded` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modeling_pp_doclayout_v3.py

- **File**: `venv\Lib\site-packages\transformers\models\pp_doclayout_v3\modeling_pp_doclayout_v3.py`
- **Captured**: 4/28/2026, 12:55:35 PM
- **Category**: bugfix
**Summary:** Modified modeling_pp_doclayout_v3.py: 2074 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\pp_doclayout_v3\modeling_pp_doclayout_v3.py` (+2074 / -0)
**Schema: `PPDocLayoutV3PreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `PPDocLayoutV3Config` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `main_input_name` | `unknown` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_supports_attention_backend` | `unknown` | ✓ | - |
| `_supports_flex_attn` | `unknown` | ✓ | - |

**Schema: `PPDocLayoutV3DecoderOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `intermediate_hidden_states` | `unknown` | ✓ | - |
| `intermediate_logits` | `unknown` | ✓ | - |
| `intermediate_reference_points` | `unknown` | ✓ | - |
| `intermediate_predicted_corners` | `unknown` | ✓ | - |
| `initial_reference_points` | `unknown` | ✓ | - |
| `cross_attentions` | `unknown` | ✓ | - |
| `decoder_out_order_logits` | `unknown` | ✓ | - |
| `decoder_out_masks` | `unknown` | ✓ | - |
| `last_hidden_state` | `torch` | ✓ | - |
| `intermediate_hidden_states` | `torch` | ✓ | - |
| `intermediate_logits` | `torch` | ✓ | - |
| `intermediate_reference_points` | `torch` | ✓ | - |
| `intermediate_predicted_corners` | `torch` | ✓ | - |
| `initial_reference_points` | `torch` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[torch` | ✓ | - |
| `cross_attentions` | `tuple[torch` | ✓ | - |
| `decoder_out_order_logits` | `torch` | ✓ | - |
| `decoder_out_masks` | `torch` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `Base` | `unknown` | ✓ | - |

**Schema: `PPDocLayoutV3ModelOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `last_hidden_state` | `unknown` | ✓ | - |
| `intermediate_hidden_states` | `unknown` | ✓ | - |
| `intermediate_logits` | `unknown` | ✓ | - |
| `intermediate_reference_points` | `unknown` | ✓ | - |
| `intermediate_predicted_corners` | `unknown` | ✓ | - |
| `initial_reference_points` | `unknown` | ✓ | - |
| `init_reference_points` | `unknown` | ✓ | - |
| `enc_topk_logits` | `unknown` | ✓ | - |
| `enc_topk_bboxes` | `unknown` | ✓ | - |
| `enc_outputs_coord_logits` | `unknown` | ✓ | - |
| `denoising_meta_values` | `unknown` | ✓ | - |
| `out_order_logits` | `unknown` | ✓ | - |
| `out_masks` | `unknown` | ✓ | - |
| `last_hidden_state` | `torch` | ✓ | - |
| `intermediate_hidden_states` | `torch` | ✓ | - |
| `intermediate_logits` | `torch` | ✓ | - |
| `intermediate_reference_points` | `torch` | ✓ | - |
| `intermediate_predicted_corners` | `torch` | ✓ | - |
| `initial_reference_points` | `torch` | ✓ | - |
| `decoder_hidden_states` | `tuple[torch` | ✓ | - |
| `decoder_attentions` | `tuple[torch` | ✓ | - |
| `cross_attentions` | `tuple[torch` | ✓ | - |
| `encoder_last_hidden_state` | `torch` | ✓ | - |
| `encoder_hidden_states` | `tuple[torch` | ✓ | - |
| `encoder_attentions` | `tuple[torch` | ✓ | - |
| `init_reference_points` | `torch` | ✓ | - |
| `enc_topk_logits` | `torch` | ✓ | - |
| `enc_topk_bboxes` | `torch` | ✓ | - |
| `enc_outputs_coord_logits` | `torch` | ✓ | - |
| `denoising_meta_values` | `dict` | ✓ | - |
| `out_order_logits` | `torch` | ✓ | - |
| `out_masks` | `torch` | ✓ | - |

**Schema: `PPDocLayoutV3HybridEncoder`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Main` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |

**Schema: `PPDocLayoutV3Decoder`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Main` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |

**Schema: `PPDocLayoutV3Model`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_tied_weights_keys` | `unknown` | ✓ | - |

**Schema: `PPDocLayoutV3HybridEncoderOutput`** (pydantic)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `mask_feat` | `unknown` | ✓ | - |
| `mask_feat` | `torch` | ✓ | - |

**Schema: `PPDocLayoutV3ForObjectDetectionOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `logits` | `unknown` | ✓ | - |
| `pred_boxes` | `unknown` | ✓ | - |
| `order_logits` | `unknown` | ✓ | - |
| `out_masks` | `unknown` | ✓ | - |
| `last_hidden_state` | `unknown` | ✓ | - |
| `intermediate_hidden_states` | `unknown` | ✓ | - |
| `intermediate_logits` | `unknown` | ✓ | - |
| `intermediate_reference_points` | `unknown` | ✓ | - |
| `intermediate_predicted_corners` | `unknown` | ✓ | - |
| `initial_reference_points` | `unknown` | ✓ | - |
| `init_reference_points` | `unknown` | ✓ | - |
| `enc_topk_logits` | `unknown` | ✓ | - |
| `enc_topk_bboxes` | `unknown` | ✓ | - |
| `enc_outputs_coord_logits` | `unknown` | ✓ | - |
| `denoising_meta_values` | `unknown` | ✓ | - |
| `logits` | `torch` | ✓ | - |
| `pred_boxes` | `torch` | ✓ | - |
| `order_logits` | `torch` | ✓ | - |
| `out_masks` | `torch` | ✓ | - |
| `last_hidden_state` | `torch` | ✓ | - |
| `intermediate_hidden_states` | `torch` | ✓ | - |
| `intermediate_logits` | `torch` | ✓ | - |
| `intermediate_reference_points` | `torch` | ✓ | - |
| `intermediate_predicted_corners` | `torch` | ✓ | - |
| `initial_reference_points` | `torch` | ✓ | - |
| `decoder_hidden_states` | `tuple[torch` | ✓ | - |
| `decoder_attentions` | `tuple[torch` | ✓ | - |
| `cross_attentions` | `tuple[torch` | ✓ | - |
| `encoder_last_hidden_state` | `torch` | ✓ | - |
| `encoder_hidden_states` | `tuple[torch` | ✓ | - |
| `encoder_attentions` | `tuple[torch` | ✓ | - |
| `init_reference_points` | `tuple[torch` | ✓ | - |
| `enc_topk_logits` | `torch` | ✓ | - |
| `enc_topk_bboxes` | `torch` | ✓ | - |
| `enc_outputs_coord_logits` | `torch` | ✓ | - |
| `denoising_meta_values` | `dict` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `PP` | `unknown` | ✓ | - |
| `which` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modular_pp_doclayout_v3.py

- **File**: `venv\Lib\site-packages\transformers\models\pp_doclayout_v3\modular_pp_doclayout_v3.py`
- **Captured**: 4/28/2026, 12:55:33 PM
- **Category**: bugfix
**Summary:** Modified modular_pp_doclayout_v3.py: 1443 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\pp_doclayout_v3\modular_pp_doclayout_v3.py` (+1443 / -0)
**Schema: `PPDocLayoutV3PreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `mask` | `unknown` | ✓ | - |
| `height` | `unknown` | ✓ | - |
| `y_coords` | `unknown` | ✓ | - |
| `x_coords` | `unknown` | ✓ | - |
| `y_coords` | `unknown` | ✓ | - |
| `x_coords_masked` | `unknown` | ✓ | - |
| `x_max` | `unknown` | ✓ | - |
| `x_min` | `unknown` | ✓ | - |
| `y_coords_masked` | `unknown` | ✓ | - |
| `y_max` | `unknown` | ✓ | - |
| `y_min` | `unknown` | ✓ | - |
| `unnormalized_bbox` | `unknown` | ✓ | - |
| `is_mask_non_empty` | `unknown` | ✓ | - |
| `unnormalized_bbox` | `unknown` | ✓ | - |
| `norm_tensor` | `unknown` | ✓ | - |
| `normalized_bbox_xyxy` | `unknown` | ✓ | - |
| `x_min_norm` | `unknown` | ✓ | - |
| `center_x` | `unknown` | ✓ | - |
| `center_y` | `unknown` | ✓ | - |
| `box_width` | `unknown` | ✓ | - |
| `box_height` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |

**Schema: `PPDocLayoutV3ModelOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `last_hidden_state` | `unknown` | ✓ | - |
| `intermediate_hidden_states` | `unknown` | ✓ | - |
| `intermediate_logits` | `unknown` | ✓ | - |
| `intermediate_reference_points` | `unknown` | ✓ | - |
| `intermediate_predicted_corners` | `unknown` | ✓ | - |
| `initial_reference_points` | `unknown` | ✓ | - |
| `init_reference_points` | `unknown` | ✓ | - |
| `enc_topk_logits` | `unknown` | ✓ | - |
| `enc_topk_bboxes` | `unknown` | ✓ | - |
| `enc_outputs_coord_logits` | `unknown` | ✓ | - |
| `denoising_meta_values` | `unknown` | ✓ | - |
| `out_order_logits` | `unknown` | ✓ | - |
| `out_masks` | `unknown` | ✓ | - |
| `out_order_logits` | `torch` | ✓ | - |
| `out_masks` | `torch` | ✓ | - |

**Schema: `PPDocLayoutV3Model`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_tied_weights_keys` | `unknown` | ✓ | - |

**Schema: `PPDocLayoutV3HybridEncoderOutput`** (pydantic)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `mask_feat` | `unknown` | ✓ | - |
| `mask_feat` | `torch` | ✓ | - |

**Schema: `PPDocLayoutV3ForObjectDetectionOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `logits` | `unknown` | ✓ | - |
| `pred_boxes` | `unknown` | ✓ | - |
| `order_logits` | `unknown` | ✓ | - |
| `out_masks` | `unknown` | ✓ | - |
| `last_hidden_state` | `unknown` | ✓ | - |
| `intermediate_hidden_states` | `unknown` | ✓ | - |
| `intermediate_logits` | `unknown` | ✓ | - |
| `intermediate_reference_points` | `unknown` | ✓ | - |
| `intermediate_predicted_corners` | `unknown` | ✓ | - |
| `initial_reference_points` | `unknown` | ✓ | - |
| `init_reference_points` | `unknown` | ✓ | - |
| `enc_topk_logits` | `unknown` | ✓ | - |
| `enc_topk_bboxes` | `unknown` | ✓ | - |
| `enc_outputs_coord_logits` | `unknown` | ✓ | - |
| `denoising_meta_values` | `unknown` | ✓ | - |
| `logits` | `torch` | ✓ | - |
| `pred_boxes` | `torch` | ✓ | - |
| `order_logits` | `torch` | ✓ | - |
| `out_masks` | `torch` | ✓ | - |
| `last_hidden_state` | `torch` | ✓ | - |
| `intermediate_hidden_states` | `torch` | ✓ | - |
| `intermediate_logits` | `torch` | ✓ | - |
| `intermediate_reference_points` | `torch` | ✓ | - |
| `intermediate_predicted_corners` | `torch` | ✓ | - |
| `initial_reference_points` | `torch` | ✓ | - |
| `decoder_hidden_states` | `tuple[torch` | ✓ | - |
| `decoder_attentions` | `tuple[torch` | ✓ | - |
| `cross_attentions` | `tuple[torch` | ✓ | - |
| `encoder_last_hidden_state` | `torch` | ✓ | - |
| `encoder_hidden_states` | `tuple[torch` | ✓ | - |
| `encoder_attentions` | `tuple[torch` | ✓ | - |
| `init_reference_points` | `tuple[torch` | ✓ | - |
| `enc_topk_logits` | `torch` | ✓ | - |
| `enc_topk_bboxes` | `torch` | ✓ | - |
| `enc_outputs_coord_logits` | `torch` | ✓ | - |
| `denoising_meta_values` | `dict` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `PP` | `unknown` | ✓ | - |
| `which` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modeling_pp_lcnet.py

- **File**: `venv\Lib\site-packages\transformers\models\pp_lcnet\modeling_pp_lcnet.py`
- **Captured**: 4/28/2026, 12:55:28 PM
- **Category**: bugfix
**Summary:** Modified modeling_pp_lcnet.py: 369 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\pp_lcnet\modeling_pp_lcnet.py` (+369 / -0)
**Schema: `PPLCNetPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `An` | `unknown` | ✓ | - |
| `Provides` | `unknown` | ✓ | - |
| `config` | `PPLCNetConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `main_input_name` | `unknown` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `_can_compile_fullgraph` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |

**Schema: `PPLCNetEncoder`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `custom_intro` | `unknown` | ✓ | - |
| `PPLCNet` | `unknown` | ✓ | - |

**Schema: `PPLCNetBackbone`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `has_attentions` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modular_pp_lcnet.py

- **File**: `venv\Lib\site-packages\transformers\models\pp_lcnet\modular_pp_lcnet.py`
- **Captured**: 4/28/2026, 12:55:22 PM
- **Category**: bugfix
**Summary:** Modified modular_pp_lcnet.py: 541 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\pp_lcnet\modular_pp_lcnet.py` (+541 / -0)
**Schema: `PPLCNetPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `An` | `unknown` | ✓ | - |
| `Provides` | `unknown` | ✓ | - |
| `config` | `PPLCNetConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `main_input_name` | `unknown` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `_can_compile_fullgraph` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |

**Schema: `PPLCNetEncoder`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `custom_intro` | `unknown` | ✓ | - |
| `PPLCNet` | `unknown` | ✓ | - |

**Schema: `PPLCNetBackbone`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `has_attentions` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modeling_pp_lcnet_v3.py

- **File**: `venv\Lib\site-packages\transformers\models\pp_lcnet_v3\modeling_pp_lcnet_v3.py`
- **Captured**: 4/28/2026, 12:55:18 PM
- **Category**: bugfix
**Summary:** Modified modeling_pp_lcnet_v3.py: 408 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\pp_lcnet_v3\modeling_pp_lcnet_v3.py` (+408 / -0)
**Schema: `PPLCNetV3PreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `An` | `unknown` | ✓ | - |
| `Provides` | `unknown` | ✓ | - |
| `config` | `PPLCNetV3Config` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `main_input_name` | `unknown` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `_can_compile_fullgraph` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `PPLCNetV3` | `unknown` | ✓ | - |

**Schema: `PPLCNetV3Backbone`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `has_attentions` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modeling_pp_ocrv5_mobile_det.py

- **File**: `venv\Lib\site-packages\transformers\models\pp_ocrv5_mobile_det\modeling_pp_ocrv5_mobile_det.py`
- **Captured**: 4/28/2026, 12:55:11 PM
- **Category**: bugfix
**Summary:** Modified modeling_pp_ocrv5_mobile_det.py: 321 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\pp_ocrv5_mobile_det\modeling_pp_ocrv5_mobile_det.py` (+321 / -0)
**Schema: `PPOCRV5MobileDetPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Base` | `unknown` | ✓ | - |
| `configuration` | `unknown` | ✓ | - |
| `config` | `PPOCRV5MobileDetConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `main_input_name` | `unknown` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `_can_compile_fullgraph` | `unknown` | ✓ | - |

**Schema: `PPOCRV5MobileDetModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `custom_intro` | `unknown` | ✓ | - |
| `PPOCRV5` | `unknown` | ✓ | - |
| `and` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modeling_pp_ocrv5_mobile_rec.py

- **File**: `venv\Lib\site-packages\transformers\models\pp_ocrv5_mobile_rec\modeling_pp_ocrv5_mobile_rec.py`
- **Captured**: 4/28/2026, 12:55:04 PM
- **Category**: bugfix
**Summary:** Modified modeling_pp_ocrv5_mobile_rec.py: 408 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\pp_ocrv5_mobile_rec\modeling_pp_ocrv5_mobile_rec.py` (+408 / -0)
**Schema: `PPOCRV5MobileRecPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `PPOCRV5MobileRecConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_skip_keys_device_placement` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `_supports_flex_attn` | `unknown` | ✓ | - |
| `_can_compile_fullgraph` | `unknown` | ✓ | - |
| `_supports_attention_backend` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |
| `main_input_name` | `unknown` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `Ensure` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `new_value` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |

**Schema: `PPOCRV5MobileRecEncoderWithSVTR`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `SVTR` | `Scene Text Recognition with a Single Visual Model` | ✓ | - |
| `https` | `unknown` | ✓ | - |

**Schema: `PPOCRV5MobileRecForTextRecognitionOutput`** (pydantic)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `head_hidden_states` | `unknown` | ✓ | - |
| `head_hidden_states` | `torch` | ✓ | - |

### [New] [bugfix] Changes in modeling_pp_ocrv5_server_det.py

- **File**: `venv\Lib\site-packages\transformers\models\pp_ocrv5_server_det\modeling_pp_ocrv5_server_det.py`
- **Captured**: 4/28/2026, 12:54:56 PM
- **Category**: bugfix
**Summary:** Modified modeling_pp_ocrv5_server_det.py: 449 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\pp_ocrv5_server_det\modeling_pp_ocrv5_server_det.py` (+449 / -0)
**Schema: `PPOCRV5ServerDetPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Base` | `unknown` | ✓ | - |
| `configuration` | `unknown` | ✓ | - |
| `config` | `PPOCRV5ServerDetConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `main_input_name` | `unknown` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `_can_compile_fullgraph` | `unknown` | ✓ | - |

**Schema: `PPOCRV5ServerDetModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `custom_intro` | `unknown` | ✓ | - |
| `PPOCRV5` | `unknown` | ✓ | - |
| `and` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modular_pp_ocrv5_server_det.py

- **File**: `venv\Lib\site-packages\transformers\models\pp_ocrv5_server_det\modular_pp_ocrv5_server_det.py`
- **Captured**: 4/28/2026, 12:54:54 PM
- **Category**: bugfix
**Summary:** Modified modular_pp_ocrv5_server_det.py: 918 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\pp_ocrv5_server_det\modular_pp_ocrv5_server_det.py` (+918 / -0)
**Schema: `PPOCRV5ServerDetPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Base` | `unknown` | ✓ | - |
| `configuration` | `unknown` | ✓ | - |
| `config` | `PPOCRV5ServerDetConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `main_input_name` | `unknown` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `_can_compile_fullgraph` | `unknown` | ✓ | - |

**Schema: `PPOCRV5ServerDetModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `custom_intro` | `unknown` | ✓ | - |
| `PPOCRV5` | `unknown` | ✓ | - |
| `and` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in _z.py

- **File**: `venv\Lib\site-packages\plotly\graph_objs\isosurface\caps\_z.py`
- **Captured**: 4/28/2026, 12:54:52 PM
- **Category**: bugfix
**Summary:** Modified _z.py: 123 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\plotly\graph_objs\isosurface\caps\_z.py` (+123 / -0)
**Schema: `Z`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_parent_path_str` | `unknown` | ✓ | - |
| `_path_str` | `unknown` | ✓ | - |
| `_valid_props` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modeling_pp_ocrv5_server_rec.py

- **File**: `venv\Lib\site-packages\transformers\models\pp_ocrv5_server_rec\modeling_pp_ocrv5_server_rec.py`
- **Captured**: 4/28/2026, 12:54:46 PM
- **Category**: bugfix
**Summary:** Modified modeling_pp_ocrv5_server_rec.py: 391 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\pp_ocrv5_server_rec\modeling_pp_ocrv5_server_rec.py` (+391 / -0)
**Schema: `PPOCRV5ServerRecPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `PPOCRV5ServerRecConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_skip_keys_device_placement` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `_supports_flex_attn` | `unknown` | ✓ | - |
| `_can_compile_fullgraph` | `unknown` | ✓ | - |
| `_supports_attention_backend` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |
| `main_input_name` | `unknown` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |

**Schema: `PPOCRV5ServerRecEncoderWithSVTR`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `SVTR` | `Scene Text Recognition with a Single Visual Model` | ✓ | - |
| `https` | `unknown` | ✓ | - |

**Schema: `PPOCRV5ServerRecForTextRecognitionOutput`** (pydantic)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `head_hidden_states` | `unknown` | ✓ | - |
| `head_hidden_states` | `torch` | ✓ | - |

### [New] [bugfix] Changes in modular_pp_ocrv5_server_rec.py

- **File**: `venv\Lib\site-packages\transformers\models\pp_ocrv5_server_rec\modular_pp_ocrv5_server_rec.py`
- **Captured**: 4/28/2026, 12:54:44 PM
- **Category**: bugfix
**Summary:** Modified modular_pp_ocrv5_server_rec.py: 470 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\pp_ocrv5_server_rec\modular_pp_ocrv5_server_rec.py` (+470 / -0)
**Schema: `PPOCRV5ServerRecPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_no_split_modules` | `unknown` | ✓ | - |
| `main_input_name` | `unknown` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |

**Schema: `PPOCRV5ServerRecEncoderWithSVTR`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `SVTR` | `Scene Text Recognition with a Single Visual Model` | ✓ | - |
| `https` | `unknown` | ✓ | - |

**Schema: `PPOCRV5ServerRecForTextRecognitionOutput`** (pydantic)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `head_hidden_states` | `unknown` | ✓ | - |
| `head_hidden_states` | `torch` | ✓ | - |

### [New] [bugfix] Changes in random_matrix_models.py

- **File**: `venv\Lib\site-packages\sympy\stats\random_matrix_models.py`
- **Captured**: 4/28/2026, 12:54:41 PM
- **Category**: bugfix
**Summary:** Modified random_matrix_models.py: 458 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\sympy\stats\random_matrix_models.py` (+458 / -0)
**Schema: `GaussianEnsembleModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Abstract` | `unknown` | ✓ | - |
| `Contains` | `unknown` | ✓ | - |
| `gaussian` | `unknown` | ✓ | - |
| `References` | `unknown` | ✓ | - |

**Schema: `CircularEnsembleModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Abstract` | `unknown` | ✓ | - |
| `Contains` | `unknown` | ✓ | - |
| `common` | `unknown` | ✓ | - |
| `References` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in lambda_loss.py

- **File**: `venv\Lib\site-packages\sentence_transformers\cross_encoder\losses\lambda_loss.py`
- **Captured**: 4/28/2026, 12:54:38 PM
- **Category**: bugfix
**Summary:** Modified lambda_loss.py: 362 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\sentence_transformers\cross_encoder\losses\lambda_loss.py` (+362 / -0)
**Schema: `NDCGLoss1Scheme`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `It` | `unknown` | ✓ | - |
| `NDCGLoss2Scheme` | `unknown` | ✓ | - |
| `LambdaLoss` | `unknown` | ✓ | - |

**Schema: `NDCGLoss2Scheme`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `This` | `unknown` | ✓ | - |
| `superior` | `unknown` | ✓ | - |
| `for` | `unknown` | ✓ | - |

**Schema: `LambdaRankScheme`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `This` | `unknown` | ✓ | - |

**Schema: `NDCGLoss2PPScheme`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `It` | `unknown` | ✓ | - |
| `was` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in _map.py

- **File**: `venv\Lib\site-packages\plotly\graph_objs\layout\_map.py`
- **Captured**: 4/28/2026, 12:54:34 PM
- **Category**: bugfix
**Summary:** Modified _map.py: 393 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\plotly\graph_objs\layout\_map.py` (+393 / -0)
**Schema: `Map`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_parent_path_str` | `unknown` | ✓ | - |
| `_path_str` | `unknown` | ✓ | - |
| `_valid_props` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in _mapbox.py

- **File**: `venv\Lib\site-packages\plotly\graph_objs\layout\_mapbox.py`
- **Captured**: 4/28/2026, 12:54:33 PM
- **Category**: bugfix
**Summary:** Modified _mapbox.py: 453 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\plotly\graph_objs\layout\_mapbox.py` (+453 / -0)
**Schema: `Mapbox`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_parent_path_str` | `unknown` | ✓ | - |
| `_path_str` | `unknown` | ✓ | - |
| `_valid_props` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in _scene.py

- **File**: `venv\Lib\site-packages\plotly\graph_objs\layout\_scene.py`
- **Captured**: 4/28/2026, 12:54:29 PM
- **Category**: bugfix
**Summary:** Modified _scene.py: 455 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\plotly\graph_objs\layout\_scene.py` (+455 / -0)
**Schema: `Scene`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_parent_path_str` | `unknown` | ✓ | - |
| `_path_str` | `unknown` | ✓ | - |
| `_valid_props` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in _selection.py

- **File**: `venv\Lib\site-packages\plotly\graph_objs\layout\_selection.py`
- **Captured**: 4/28/2026, 12:54:27 PM
- **Category**: bugfix
**Summary:** Modified _selection.py: 494 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\plotly\graph_objs\layout\_selection.py` (+494 / -0)
**Schema: `Selection`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_parent_path_str` | `unknown` | ✓ | - |
| `_path_str` | `unknown` | ✓ | - |
| `_valid_props` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in _shape.py

- **File**: `venv\Lib\site-packages\plotly\graph_objs\layout\_shape.py`
- **Captured**: 4/28/2026, 12:54:25 PM
- **Category**: bugfix
**Summary:** Modified _shape.py: 1382 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\plotly\graph_objs\layout\_shape.py` (+1382 / -0)
**Schema: `Shape`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_parent_path_str` | `unknown` | ✓ | - |
| `_path_str` | `unknown` | ✓ | - |
| `_valid_props` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modeling_prompt_depth_anything.py

- **File**: `venv\Lib\site-packages\transformers\models\prompt_depth_anything\modeling_prompt_depth_anything.py`
- **Captured**: 4/28/2026, 12:54:22 PM
- **Category**: bugfix
**Summary:** Modified modeling_prompt_depth_anything.py: 481 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\prompt_depth_anything\modeling_prompt_depth_anything.py` (+481 / -0)
**Schema: `PromptDepthAnythingPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `PromptDepthAnythingConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `main_input_name` | `unknown` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modular_prompt_depth_anything.py

- **File**: `venv\Lib\site-packages\transformers\models\prompt_depth_anything\modular_prompt_depth_anything.py`
- **Captured**: 4/28/2026, 12:54:20 PM
- **Category**: bugfix
**Summary:** Modified modular_prompt_depth_anything.py: 329 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\prompt_depth_anything\modular_prompt_depth_anything.py` (+329 / -0)
**Schema: `PromptDepthAnythingPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `PromptDepthAnythingConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `main_input_name` | `unknown` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in model_card.py

- **File**: `venv\Lib\site-packages\sentence_transformers\cross_encoder\model_card.py`
- **Captured**: 4/28/2026, 12:54:17 PM
- **Category**: bugfix
**Summary:** Modified model_card.py: 277 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\sentence_transformers\cross_encoder\model_card.py` (+277 / -0)
**Schema: `CrossEncoderModelCardCallback`** (pydantic)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `pass` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modeling_prophetnet.py

- **File**: `venv\Lib\site-packages\transformers\models\prophetnet\modeling_prophetnet.py`
- **Captured**: 4/28/2026, 12:54:14 PM
- **Category**: bugfix
**Summary:** Modified modeling_prophetnet.py: 1847 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\prophetnet\modeling_prophetnet.py` (+1847 / -0)
**Schema: `ProphetNetSeq2SeqLMOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `loss` | `unknown` | ✓ | - |
| `logits` | `unknown` | ✓ | - |
| `logits_ngram` | `unknown` | ✓ | - |
| `past_key_values` | `unknown` | ✓ | - |
| `decoder_ngram_hidden_states` | `unknown` | ✓ | - |
| `decoder_ngram_attentions` | `unknown` | ✓ | - |
| `encoder_last_hidden_state` | `unknown` | ✓ | - |
| `loss` | `torch` | ✓ | - |
| `logits` | `torch` | ✓ | - |
| `logits_ngram` | `torch` | ✓ | - |
| `past_key_values` | `Cache` | ✓ | - |
| `decoder_hidden_states` | `tuple[torch` | ✓ | - |
| `decoder_ngram_hidden_states` | `tuple[torch` | ✓ | - |
| `decoder_attentions` | `tuple[torch` | ✓ | - |
| `decoder_ngram_attentions` | `tuple[torch` | ✓ | - |
| `cross_attentions` | `tuple[torch` | ✓ | - |
| `encoder_last_hidden_state` | `torch` | ✓ | - |
| `encoder_hidden_states` | `tuple[torch` | ✓ | - |
| `encoder_attentions` | `tuple[torch` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `Base` | `unknown` | ✓ | - |
| `decoding` | `unknown` | ✓ | - |

**Schema: `ProphetNetSeq2SeqModelOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `last_hidden_state` | `unknown` | ✓ | - |
| `last_hidden_state_ngram` | `unknown` | ✓ | - |
| `past_key_values` | `unknown` | ✓ | - |
| `decoder_ngram_hidden_states` | `unknown` | ✓ | - |
| `decoder_ngram_attentions` | `unknown` | ✓ | - |
| `encoder_last_hidden_state` | `unknown` | ✓ | - |
| `last_hidden_state` | `torch` | ✓ | - |
| `last_hidden_state_ngram` | `torch` | ✓ | - |
| `past_key_values` | `Cache` | ✓ | - |
| `decoder_hidden_states` | `tuple[torch` | ✓ | - |
| `decoder_ngram_hidden_states` | `tuple[torch` | ✓ | - |
| `decoder_attentions` | `tuple[torch` | ✓ | - |
| `decoder_ngram_attentions` | `tuple[torch` | ✓ | - |
| `cross_attentions` | `tuple[torch` | ✓ | - |
| `encoder_last_hidden_state` | `torch` | ✓ | - |
| `encoder_hidden_states` | `tuple[torch` | ✓ | - |
| `encoder_attentions` | `tuple[torch` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `Base` | `unknown` | ✓ | - |

**Schema: `ProphetNetDecoderModelOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `last_hidden_state` | `unknown` | ✓ | - |
| `last_hidden_state_ngram` | `unknown` | ✓ | - |
| `past_key_values` | `unknown` | ✓ | - |
| `hidden_states_ngram` | `unknown` | ✓ | - |
| `ngram_attentions` | `unknown` | ✓ | - |
| `last_hidden_state` | `torch` | ✓ | - |
| `last_hidden_state_ngram` | `torch` | ✓ | - |
| `past_key_values` | `Cache` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `hidden_states_ngram` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[torch` | ✓ | - |
| `ngram_attentions` | `tuple[torch` | ✓ | - |
| `cross_attentions` | `tuple[torch` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `Base` | `unknown` | ✓ | - |

**Schema: `ProphetNetDecoderLMOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `ngram_hidden_states` | `unknown` | ✓ | - |
| `loss` | `unknown` | ✓ | - |
| `logits` | `unknown` | ✓ | - |
| `logits_ngram` | `unknown` | ✓ | - |
| `past_key_values` | `unknown` | ✓ | - |
| `hidden_states_ngram` | `unknown` | ✓ | - |
| `ngram_attentions` | `unknown` | ✓ | - |
| `loss` | `torch` | ✓ | - |
| `logits` | `torch` | ✓ | - |
| `logits_ngram` | `torch` | ✓ | - |
| `past_key_values` | `Cache` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `hidden_states_ngram` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[torch` | ✓ | - |
| `ngram_attentions` | `tuple[torch` | ✓ | - |
| `cross_attentions` | `tuple[torch` | ✓ | - |

**Schema: `ProphetNetPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `ProphetNetConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |

**Schema: `ProphetNetEncoder`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `custom_intro` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |

**Schema: `ProphetNetModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_tied_weights_keys` | `unknown` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |

**Schema: `ProphetNetForConditionalGeneration`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_tied_weights_keys` | `unknown` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |

**Schema: `ProphetNetForCausalLM`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_tied_weights_keys` | `unknown` | ✓ | - |

### [bugfix] Changes in setup.js

- **File**: `desktop\setup.js`
- **Captured**: 4/28/2026, 12:54:08 PM
- **Category**: bugfix
**Summary:** Modified setup.js: 181 lines added, 0 lines removed.
**Files Modified:**
  - `desktop\setup.js` (+181 / -0)
**Environment Variables:**

| Variable | Required | Default |
|----------|----------|---------|
| `NEXUS_REQUIRED_MODEL` | No | `llama3.1:8b-instruct-q4_K_M` |
| `NEXUS_REQUIRED_EMBED` | No | `nomic-embed-text:latest` |
| `NEXUS_BACKEND_URL` | No | `http://localhost:8000` |

### [New] [bugfix] Changes in modeling_pvt.py

- **File**: `venv\Lib\site-packages\transformers\models\pvt\modeling_pvt.py`
- **Captured**: 4/28/2026, 12:54:03 PM
- **Category**: bugfix
**Summary:** Modified modeling_pvt.py: 552 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\pvt\modeling_pvt.py` (+552 / -0)
**Schema: `PvtPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `PvtConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `main_input_name` | `unknown` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |

**Schema: `PvtModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `custom_intro` | `unknown` | ✓ | - |
| `Pvt` | `unknown` | ✓ | - |
| `the` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in _caps.py

- **File**: `venv\Lib\site-packages\plotly\graph_objs\isosurface\_caps.py`
- **Captured**: 4/28/2026, 12:54:00 PM
- **Category**: bugfix
**Summary:** Modified _caps.py: 133 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\plotly\graph_objs\isosurface\_caps.py` (+133 / -0)
**Schema: `Caps`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_parent_path_str` | `unknown` | ✓ | - |
| `_path_str` | `unknown` | ✓ | - |
| `_valid_props` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in _lightposition.py

- **File**: `venv\Lib\site-packages\plotly\graph_objs\isosurface\_lightposition.py`
- **Captured**: 4/28/2026, 12:53:57 PM
- **Category**: bugfix
**Summary:** Modified _lightposition.py: 130 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\plotly\graph_objs\isosurface\_lightposition.py` (+130 / -0)
**Schema: `Lightposition`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_parent_path_str` | `unknown` | ✓ | - |
| `_path_str` | `unknown` | ✓ | - |
| `_valid_props` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in _slices.py

- **File**: `venv\Lib\site-packages\plotly\graph_objs\isosurface\_slices.py`
- **Captured**: 4/28/2026, 12:53:54 PM
- **Category**: bugfix
**Summary:** Modified _slices.py: 133 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\plotly\graph_objs\isosurface\_slices.py` (+133 / -0)
**Schema: `Slices`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_parent_path_str` | `unknown` | ✓ | - |
| `_path_str` | `unknown` | ✓ | - |
| `_valid_props` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in _lightposition.py

- **File**: `venv\Lib\site-packages\plotly\graph_objs\mesh3d\_lightposition.py`
- **Captured**: 4/28/2026, 12:53:50 PM
- **Category**: bugfix
**Summary:** Modified _lightposition.py: 130 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\plotly\graph_objs\mesh3d\_lightposition.py` (+130 / -0)
**Schema: `Lightposition`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_parent_path_str` | `unknown` | ✓ | - |
| `_path_str` | `unknown` | ✓ | - |
| `_valid_props` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in more.py

- **File**: `venv\Lib\site-packages\setuptools\_vendor\more_itertools\more.py`
- **Captured**: 4/28/2026, 12:53:43 PM
- **Category**: bugfix
**Summary:** Modified more.py: 5304 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\setuptools\_vendor\more_itertools\more.py` (+5304 / -0)
**Schema: `AbortThread`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `pass` | `unknown` | ✓ | - |

### [bugfix] Changes in ollama.js

- **File**: `desktop\ollama.js`
- **Captured**: 4/28/2026, 12:53:41 PM
- **Category**: bugfix
**Summary:** Modified ollama.js: 208 lines added, 0 lines removed.
**Files Modified:**
  - `desktop\ollama.js` (+208 / -0)
**API Endpoints** (`ollama.js`):

| Method | Route | Handler | Middleware |
|--------|-------|---------|------------|
| `URL('/API/PULL', OLLAMA_HOST` | `/api/pull` | - | - |
**Environment Variables:**

| Variable | Required | Default |
|----------|----------|---------|
| `OLLAMA_HOST` | No | `http://127.0.0.1:11434` |

### [New] [bugfix] Changes in _lightposition.py

- **File**: `venv\Lib\site-packages\plotly\graph_objs\streamtube\_lightposition.py`
- **Captured**: 4/28/2026, 12:53:39 PM
- **Category**: bugfix
**Summary:** Modified _lightposition.py: 130 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\plotly\graph_objs\streamtube\_lightposition.py` (+130 / -0)
**Schema: `Lightposition`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_parent_path_str` | `unknown` | ✓ | - |
| `_path_str` | `unknown` | ✓ | - |
| `_valid_props` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modeling_pvt_v2.py

- **File**: `venv\Lib\site-packages\transformers\models\pvt_v2\modeling_pvt_v2.py`
- **Captured**: 4/28/2026, 12:53:36 PM
- **Category**: bugfix
**Summary:** Modified modeling_pvt_v2.py: 589 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\pvt_v2\modeling_pvt_v2.py` (+589 / -0)
**Schema: `PvtV2PreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `PvtV2Config` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `main_input_name` | `unknown` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |

**Schema: `PvtV2Model`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `custom_intro` | `unknown` | ✓ | - |
| `Pvt` | `unknown` | ✓ | - |
| `of` | `unknown` | ✓ | - |

**Schema: `PvtV2ForImageClassification`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `custom_intro` | `unknown` | ✓ | - |
| `PVTv2` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modeling_qwen2.py

- **File**: `venv\Lib\site-packages\transformers\models\qwen2\modeling_qwen2.py`
- **Captured**: 4/28/2026, 12:53:33 PM
- **Category**: bugfix
**Summary:** Modified modeling_qwen2.py: 511 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\qwen2\modeling_qwen2.py` (+511 / -0)
**Schema: `Qwen2PreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Qwen2Config` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_skip_keys_device_placement` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `_supports_flex_attn` | `unknown` | ✓ | - |
| `_can_compile_fullgraph` | `unknown` | ✓ | - |
| `_supports_attention_backend` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |

**Schema: `Qwen2ForCausalLM`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_tied_weights_keys` | `unknown` | ✓ | - |
| `_tp_plan` | `unknown` | ✓ | - |
| `_pp_plan` | `unknown` | ✓ | - |

**Schema: `Qwen2ForSequenceClassification`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `pass` | `unknown` | ✓ | - |

**Schema: `Qwen2ForTokenClassification`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `pass` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modular_qwen2.py

- **File**: `venv\Lib\site-packages\transformers\models\qwen2\modular_qwen2.py`
- **Captured**: 4/28/2026, 12:53:30 PM
- **Category**: bugfix
**Summary:** Modified modular_qwen2.py: 205 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\qwen2\modular_qwen2.py` (+205 / -0)
**Schema: `Qwen2PreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `pass` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in nano_beir.py

- **File**: `venv\Lib\site-packages\sentence_transformers\sentence_transformer\evaluation\nano_beir.py`
- **Captured**: 4/28/2026, 12:53:27 PM
- **Category**: bugfix
**Summary:** Modified nano_beir.py: 537 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\sentence_transformers\sentence_transformer\evaluation\nano_beir.py` (+537 / -0)
**Schema: `NanoBEIREvaluator`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `This` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `suitable` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `which` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modeling_qwen2_5_omni.py

- **File**: `venv\Lib\site-packages\transformers\models\qwen2_5_omni\modeling_qwen2_5_omni.py`
- **Captured**: 4/28/2026, 12:53:23 PM
- **Category**: bugfix
**Summary:** Modified modeling_qwen2_5_omni.py: 3989 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\qwen2_5_omni\modeling_qwen2_5_omni.py` (+3989 / -0)
**Schema: `Qwen2_5OmniPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Qwen2_5OmniConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_skip_keys_device_placement` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `_can_compile_fullgraph` | `unknown` | ✓ | - |
| `_supports_attention_backend` | `unknown` | ✓ | - |

**Schema: `Qwen2_5OmniPreTrainedModelForConditionalGeneration`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `input_modalities` | `unknown` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `Base` | `unknown` | ✓ | - |

**Schema: `Qwen2_5OmniThinkerCausalLMOutputWithPast`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `loss` | `unknown` | ✓ | - |
| `logits` | `unknown` | ✓ | - |
| `past_key_values` | `unknown` | ✓ | - |
| `rope_deltas` | `unknown` | ✓ | - |
| `loss` | `torch` | ✓ | - |
| `logits` | `torch` | ✓ | - |
| `past_key_values` | `Cache` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[torch` | ✓ | - |
| `rope_deltas` | `torch` | ✓ | - |
| `This` | `unknown` | ✓ | - |
| `num_key_value_heads` | `unknown` | ✓ | - |
| `batch` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `hidden_states` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `module` | `nn` | ✓ | - |
| `query` | `torch` | ✓ | - |
| `key` | `torch` | ✓ | - |
| `value` | `torch` | ✓ | - |
| `attention_mask` | `torch` | ✓ | - |
| `scaling` | `float,` | ✓ | - |
| `dropout` | `float` | ✓ | - |
| `key_states` | `unknown` | ✓ | - |
| `value_states` | `unknown` | ✓ | - |
| `attn_weights` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `attn_weights` | `unknown` | ✓ | - |
| `attn_weights` | `unknown` | ✓ | - |
| `attn_output` | `unknown` | ✓ | - |
| `attn_output` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |

**Schema: `Qwen2_5OmniAudioEncoder`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Qwen2_5OmniAudioEncoderConfig` | ✓ | - |
| `main_input_name` | `unknown` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |
| `x1` | `unknown` | ✓ | - |
| `x2` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `orig_dtype` | `unknown` | ✓ | - |
| `tensor` | `unknown` | ✓ | - |
| `cos` | `unknown` | ✓ | - |
| `sin` | `unknown` | ✓ | - |
| `cos` | `unknown` | ✓ | - |
| `sin` | `unknown` | ✓ | - |
| `output` | `unknown` | ✓ | - |
| `output` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |

**Schema: `Qwen2_5OmniVisionEncoder`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Qwen2_5OmniVisionEncoderConfig` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_input_embed_layer` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |

**Schema: `Qwen2_5OmniThinkerTextModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Qwen2_5OmniTextConfig` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |

**Schema: `Qwen2_5OmniThinkerForConditionalGeneration`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Qwen2_5OmniThinkerConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `_tied_weights_keys` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `Base` | `unknown` | ✓ | - |

**Schema: `Qwen2_5OmniTalkerCausalLMOutputWithPast`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `loss` | `unknown` | ✓ | - |
| `logits` | `unknown` | ✓ | - |
| `past_key_values` | `unknown` | ✓ | - |
| `rope_deltas` | `unknown` | ✓ | - |
| `thinker_reply_part` | `unknown` | ✓ | - |
| `loss` | `torch` | ✓ | - |
| `logits` | `torch` | ✓ | - |
| `past_key_values` | `Cache` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[torch` | ✓ | - |
| `rope_deltas` | `torch` | ✓ | - |
| `thinker_reply_part` | `torch` | ✓ | - |

**Schema: `Qwen2_5OmniTalkerModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Qwen2_5OmniTalkerConfig` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |

**Schema: `Qwen2_5OmniTalkerForConditionalGeneration`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Qwen2_5OmniTalkerConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `output_modalities` | `unknown` | ✓ | - |

**Schema: `Qwen2_5OmniToken2WavBigVGANModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Qwen2_5OmniBigVGANConfig` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |

**Schema: `Qwen2_5OmniToken2WavDiTModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Qwen2_5OmniDiTConfig` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |

**Schema: `Qwen2_5OmniToken2WavModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Qwen2_5OmniToken2WavConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `a` | `unknown` | ✓ | - |
| `a` | `unknown` | ✓ | - |
| `a` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modular_qwen2_5_omni.py

- **File**: `venv\Lib\site-packages\transformers\models\qwen2_5_omni\modular_qwen2_5_omni.py`
- **Captured**: 4/28/2026, 12:53:20 PM
- **Category**: bugfix
**Summary:** Modified modular_qwen2_5_omni.py: 3828 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\qwen2_5_omni\modular_qwen2_5_omni.py` (+3828 / -0)
**Schema: `Qwen2_5OmniPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Qwen2_5OmniConfig` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `_can_compile_fullgraph` | `unknown` | ✓ | - |

**Schema: `Qwen2_5OmniPreTrainedModelForConditionalGeneration`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `input_modalities` | `unknown` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `Base` | `unknown` | ✓ | - |

**Schema: `Qwen2_5OmniThinkerCausalLMOutputWithPast`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `loss` | `unknown` | ✓ | - |
| `logits` | `unknown` | ✓ | - |
| `past_key_values` | `unknown` | ✓ | - |
| `rope_deltas` | `unknown` | ✓ | - |
| `loss` | `torch` | ✓ | - |
| `logits` | `torch` | ✓ | - |
| `past_key_values` | `Cache` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[torch` | ✓ | - |
| `rope_deltas` | `torch` | ✓ | - |

**Schema: `Qwen2_5OmniAudioEncoder`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Qwen2_5OmniAudioEncoderConfig` | ✓ | - |
| `main_input_name` | `unknown` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |
| `orig_dtype` | `unknown` | ✓ | - |
| `tensor` | `unknown` | ✓ | - |
| `cos` | `unknown` | ✓ | - |
| `sin` | `unknown` | ✓ | - |
| `cos` | `unknown` | ✓ | - |
| `sin` | `unknown` | ✓ | - |
| `output` | `unknown` | ✓ | - |
| `output` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |

**Schema: `Qwen2_5OmniVisionEncoder`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Qwen2_5OmniVisionEncoderConfig` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_input_embed_layer` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |

**Schema: `Qwen2_5OmniThinkerTextModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Qwen2_5OmniTextConfig` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |

**Schema: `Qwen2_5OmniThinkerForConditionalGeneration`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Qwen2_5OmniThinkerConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `_tied_weights_keys` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `Base` | `unknown` | ✓ | - |

**Schema: `Qwen2_5OmniTalkerCausalLMOutputWithPast`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `loss` | `unknown` | ✓ | - |
| `logits` | `unknown` | ✓ | - |
| `past_key_values` | `unknown` | ✓ | - |
| `rope_deltas` | `unknown` | ✓ | - |
| `thinker_reply_part` | `unknown` | ✓ | - |
| `loss` | `torch` | ✓ | - |
| `logits` | `torch` | ✓ | - |
| `past_key_values` | `Cache` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[torch` | ✓ | - |
| `rope_deltas` | `torch` | ✓ | - |
| `thinker_reply_part` | `torch` | ✓ | - |

**Schema: `Qwen2_5OmniTalkerModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Qwen2_5OmniTalkerConfig` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |

**Schema: `Qwen2_5OmniTalkerForConditionalGeneration`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Qwen2_5OmniTalkerConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `output_modalities` | `unknown` | ✓ | - |

**Schema: `Qwen2_5OmniToken2WavBigVGANModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Qwen2_5OmniBigVGANConfig` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |

**Schema: `Qwen2_5OmniToken2WavDiTModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Qwen2_5OmniDiTConfig` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |

**Schema: `Qwen2_5OmniToken2WavModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Qwen2_5OmniToken2WavConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `a` | `unknown` | ✓ | - |
| `a` | `unknown` | ✓ | - |
| `a` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in specifiers.py

- **File**: `venv\Lib\site-packages\setuptools\_vendor\packaging\specifiers.py`
- **Captured**: 4/28/2026, 12:53:17 PM
- **Category**: bugfix
**Summary:** Modified specifiers.py: 1069 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\setuptools\_vendor\packaging\specifiers.py` (+1069 / -0)
**Schema: `Specifier`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_operator_regex_str` | `unknown` | ✓ | - |
| `_version_regex_str` | `unknown` | ✓ | - |
| `_regex` | `unknown` | ✓ | - |
| `_operators` | `Final` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `not` | `unknown` | ✓ | - |
| `components` | `unknown` | ✓ | - |
| `version` | `unknown` | ✓ | - |
| `result` | `list[str]` | ✓ | - |
| `epoch` | `unknown` | ✓ | - |
| `result` | `unknown` | ✓ | - |
| `for` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `This` | `unknown` | ✓ | - |
| `first` | `unknown` | ✓ | - |
| `components` | `unknown` | ✓ | - |
| `epoch` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `left_split` | `unknown` | ✓ | - |
| `left_split` | `unknown` | ✓ | - |
| `right_split` | `unknown` | ✓ | - |
| `left_split` | `unknown` | ✓ | - |
| `right_split` | `unknown` | ✓ | - |
| `left_split` | `unknown` | ✓ | - |
| `right_split` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in version.py

- **File**: `venv\Lib\site-packages\setuptools\_vendor\packaging\version.py`
- **Captured**: 4/28/2026, 12:53:16 PM
- **Category**: bugfix
**Summary:** Modified version.py: 793 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\setuptools\_vendor\packaging\version.py` (+793 / -0)
**Schema: `Version`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `A` | `class` | ✓ | - |
| `sorted` | `unknown` | ✓ | - |
| `True` | `unknown` | ✓ | - |
| `False` | `unknown` | ✓ | - |
| `False` | `unknown` | ✓ | - |
| `False` | `unknown` | ✓ | - |
| `True` | `unknown` | ✓ | - |
| `_regex` | `unknown` | ✓ | - |
| `_epoch` | `int` | ✓ | - |
| `_release` | `tuple[int,` | ✓ | - |
| `_dev` | `tuple[str, int]` | ✓ | - |
| `_pre` | `tuple[str, int]` | ✓ | - |
| `_post` | `tuple[str, int]` | ✓ | - |
| `_local` | `LocalType` | ✓ | - |
| `_key_cache` | `CmpKey` | ✓ | - |

### [New] [bugfix] Changes in modeling_qwen2_5_vl.py

- **File**: `venv\Lib\site-packages\transformers\models\qwen2_5_vl\modeling_qwen2_5_vl.py`
- **Captured**: 4/28/2026, 12:53:13 PM
- **Category**: bugfix
**Summary:** Modified modeling_qwen2_5_vl.py: 1760 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\qwen2_5_vl\modeling_qwen2_5_vl.py` (+1760 / -0)
**Schema: `Qwen2_5_VLPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Qwen2_5_VLConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_skip_keys_device_placement` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `_can_compile_fullgraph` | `unknown` | ✓ | - |
| `_supports_attention_backend` | `unknown` | ✓ | - |

**Schema: `Qwen2_5_VisionTransformerPretrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Qwen2_5_VLVisionConfig` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_input_embed_layer` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `Base` | `unknown` | ✓ | - |

**Schema: `Qwen2_5_VLModelOutputWithPast`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `past_key_values` | `unknown` | ✓ | - |
| `rope_deltas` | `unknown` | ✓ | - |
| `last_hidden_state` | `torch` | ✓ | - |
| `past_key_values` | `Cache` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[torch` | ✓ | - |
| `rope_deltas` | `torch` | ✓ | - |

**Schema: `Qwen2_5_VLTextModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Qwen2_5_VLTextConfig` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |

**Schema: `Qwen2_5_VLModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `base_model_prefix` | `unknown` | ✓ | - |
| `accepts_loss_kwargs` | `unknown` | ✓ | - |
| `config` | `Qwen2_5_VLConfig` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `Base` | `unknown` | ✓ | - |

**Schema: `Qwen2_5_VLCausalLMOutputWithPast`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `loss` | `unknown` | ✓ | - |
| `logits` | `unknown` | ✓ | - |
| `past_key_values` | `unknown` | ✓ | - |
| `rope_deltas` | `unknown` | ✓ | - |
| `loss` | `torch` | ✓ | - |
| `logits` | `torch` | ✓ | - |
| `past_key_values` | `Cache` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[torch` | ✓ | - |
| `rope_deltas` | `torch` | ✓ | - |

### [New] [bugfix] Changes in modular_qwen2_5_vl.py

- **File**: `venv\Lib\site-packages\transformers\models\qwen2_5_vl\modular_qwen2_5_vl.py`
- **Captured**: 4/28/2026, 12:53:11 PM
- **Category**: bugfix
**Summary:** Modified modular_qwen2_5_vl.py: 933 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\qwen2_5_vl\modular_qwen2_5_vl.py` (+933 / -0)
**Schema: `Qwen2_5_VisionTransformerPretrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Qwen2_5_VLVisionConfig` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_input_embed_layer` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |

**Schema: `Qwen2_5_VLModelOutputWithPast`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `pass` | `unknown` | ✓ | - |

**Schema: `Qwen2_5_VLModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Qwen2_5_VLConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `accepts_loss_kwargs` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modeling_qwen2_audio.py

- **File**: `venv\Lib\site-packages\transformers\models\qwen2_audio\modeling_qwen2_audio.py`
- **Captured**: 4/28/2026, 12:53:07 PM
- **Category**: bugfix
**Summary:** Modified modeling_qwen2_audio.py: 813 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\qwen2_audio\modeling_qwen2_audio.py` (+813 / -0)
**Schema: `Qwen2AudioCausalLMOutputWithPast`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `loss` | `unknown` | ✓ | - |
| `logits` | `unknown` | ✓ | - |
| `past_key_values` | `unknown` | ✓ | - |
| `attention_mask` | `unknown` | ✓ | - |
| `loss` | `torch` | ✓ | - |
| `logits` | `torch` | ✓ | - |
| `past_key_values` | `Cache` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[torch` | ✓ | - |
| `attention_mask` | `torch` | ✓ | - |
| `module` | `nn` | ✓ | - |
| `query` | `torch` | ✓ | - |
| `key` | `torch` | ✓ | - |
| `value` | `torch` | ✓ | - |
| `attention_mask` | `torch` | ✓ | - |
| `scaling` | `float` | ✓ | - |
| `dropout` | `float` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `attn_weights` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `attn_weights` | `unknown` | ✓ | - |
| `attn_weights` | `unknown` | ✓ | - |
| `attn_output` | `unknown` | ✓ | - |
| `attn_output` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |

**Schema: `Qwen2AudioPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Qwen2AudioConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_skip_keys_device_placement` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |

**Schema: `Qwen2AudioEncoder`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Transformer` | `unknown` | ✓ | - |
| `Args` | `config` | ✓ | - |
| `config` | `Qwen2AudioEncoderConfig` | ✓ | - |
| `main_input_name` | `unknown` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modeling_qwen2_moe.py

- **File**: `venv\Lib\site-packages\transformers\models\qwen2_moe\modeling_qwen2_moe.py`
- **Captured**: 4/28/2026, 12:53:05 PM
- **Category**: bugfix
**Summary:** Modified modeling_qwen2_moe.py: 737 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\qwen2_moe\modeling_qwen2_moe.py` (+737 / -0)
**Schema: `Qwen2MoePreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Qwen2MoeConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_skip_keys_device_placement` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `_supports_flex_attn` | `unknown` | ✓ | - |
| `_can_compile_fullgraph` | `unknown` | ✓ | - |
| `_supports_attention_backend` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |

**Schema: `Qwen2MoeModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `gate_logits` | `torch` | ✓ | - |
| `num_experts` | `int` | ✓ | - |
| `top_k` | `unknown` | ✓ | - |
| `attention_mask` | `torch` | ✓ | - |
| `r` | `unknown` | ✓ | - |
| `Computes` | `unknown` | ✓ | - |
| `See` | `unknown` | ✓ | - |
| `function` | `unknown` | ✓ | - |
| `experts` | `unknown` | ✓ | - |
| `Args` | `gate_logits` | ✓ | - |
| `Returns` | `The auxiliary loss` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `routing_weights` | `unknown` | ✓ | - |
| `_` | `unknown` | ✓ | - |
| `expert_mask` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `else` | `batch_size, sequence_length` | ✓ | - |
| `overall_loss` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |

**Schema: `Qwen2MoeForCausalLM`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_tied_weights_keys` | `unknown` | ✓ | - |
| `_tp_plan` | `unknown` | ✓ | - |
| `_pp_plan` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modular_qwen2_moe.py

- **File**: `venv\Lib\site-packages\transformers\models\qwen2_moe\modular_qwen2_moe.py`
- **Captured**: 4/28/2026, 12:53:03 PM
- **Category**: bugfix
**Summary:** Modified modular_qwen2_moe.py: 259 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\qwen2_moe\modular_qwen2_moe.py` (+259 / -0)
**Schema: `Qwen2MoePreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_can_record_outputs` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modeling_qwen2_vl.py

- **File**: `venv\Lib\site-packages\transformers\models\qwen2_vl\modeling_qwen2_vl.py`
- **Captured**: 4/28/2026, 12:52:59 PM
- **Category**: bugfix
**Summary:** Modified modeling_qwen2_vl.py: 1672 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\qwen2_vl\modeling_qwen2_vl.py` (+1672 / -0)
**Schema: `Qwen2VLModelOutputWithPast`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `past_key_values` | `unknown` | ✓ | - |
| `rope_deltas` | `unknown` | ✓ | - |
| `last_hidden_state` | `torch` | ✓ | - |
| `past_key_values` | `Cache` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[torch` | ✓ | - |
| `rope_deltas` | `torch` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `Base` | `unknown` | ✓ | - |

**Schema: `Qwen2VLCausalLMOutputWithPast`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `loss` | `unknown` | ✓ | - |
| `logits` | `unknown` | ✓ | - |
| `past_key_values` | `unknown` | ✓ | - |
| `rope_deltas` | `unknown` | ✓ | - |
| `loss` | `torch` | ✓ | - |
| `logits` | `torch` | ✓ | - |
| `past_key_values` | `Cache` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[torch` | ✓ | - |
| `rope_deltas` | `torch` | ✓ | - |

**Schema: `Qwen2VLPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Qwen2VLConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_skip_keys_device_placement` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `_can_compile_fullgraph` | `unknown` | ✓ | - |
| `_supports_attention_backend` | `unknown` | ✓ | - |

**Schema: `Qwen2VisionTransformerPretrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Qwen2VLVisionConfig` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_input_embed_layer` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |

**Schema: `Qwen2VLTextModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Qwen2VLTextConfig` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |

**Schema: `Qwen2VLModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `base_model_prefix` | `unknown` | ✓ | - |
| `accepts_loss_kwargs` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modeling_qwen3.py

- **File**: `venv\Lib\site-packages\transformers\models\qwen3\modeling_qwen3.py`
- **Captured**: 4/28/2026, 12:52:56 PM
- **Category**: bugfix
**Summary:** Modified modeling_qwen3.py: 540 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\qwen3\modeling_qwen3.py` (+540 / -0)
**Schema: `Qwen3PreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Qwen3Config` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_skip_keys_device_placement` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `_supports_flex_attn` | `unknown` | ✓ | - |
| `_can_compile_fullgraph` | `unknown` | ✓ | - |
| `_supports_attention_backend` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |

**Schema: `Qwen3ForCausalLM`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_tied_weights_keys` | `unknown` | ✓ | - |
| `_tp_plan` | `unknown` | ✓ | - |
| `_pp_plan` | `unknown` | ✓ | - |

**Schema: `Qwen3ForSequenceClassification`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `pass` | `unknown` | ✓ | - |

**Schema: `Qwen3ForTokenClassification`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `pass` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modeling_qwen3_5.py

- **File**: `venv\Lib\site-packages\transformers\models\qwen3_5\modeling_qwen3_5.py`
- **Captured**: 4/28/2026, 12:52:52 PM
- **Category**: bugfix
**Summary:** Modified modeling_qwen3_5.py: 2182 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\qwen3_5\modeling_qwen3_5.py` (+2182 / -0)
**Schema: `Qwen3_5PreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Qwen3_5Config` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_skip_keys_device_placement` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `_keys_to_ignore_on_load_unexpected` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |
| `_is_stateful` | `unknown` | ✓ | - |

**Schema: `Qwen3_5VisionModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Qwen3_5VisionConfig` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `Base` | `unknown` | ✓ | - |

**Schema: `Qwen3_5ModelOutputWithPast`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `past_key_values` | `unknown` | ✓ | - |
| `rope_deltas` | `unknown` | ✓ | - |
| `last_hidden_state` | `torch` | ✓ | - |
| `past_key_values` | `Cache` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[torch` | ✓ | - |
| `rope_deltas` | `torch` | ✓ | - |

**Schema: `Qwen3_5TextModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Qwen3_5TextConfig` | ✓ | - |

**Schema: `Qwen3_5Model`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `base_model_prefix` | `unknown` | ✓ | - |
| `accepts_loss_kwargs` | `unknown` | ✓ | - |
| `config` | `Qwen3_5Config` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |

**Schema: `Qwen3_5ForCausalLM`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_tied_weights_keys` | `unknown` | ✓ | - |
| `_tp_plan` | `unknown` | ✓ | - |
| `_pp_plan` | `unknown` | ✓ | - |
| `config` | `Qwen3_5TextConfig` | ✓ | - |
| `_keys_to_ignore_on_load_unexpected` | `unknown` | ✓ | - |

**Schema: `Qwen3_5ForSequenceClassification`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Qwen3_5TextConfig` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `Base` | `unknown` | ✓ | - |

**Schema: `Qwen3_5CausalLMOutputWithPast`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `loss` | `unknown` | ✓ | - |
| `logits` | `unknown` | ✓ | - |
| `past_key_values` | `unknown` | ✓ | - |
| `rope_deltas` | `unknown` | ✓ | - |
| `loss` | `torch` | ✓ | - |
| `logits` | `torch` | ✓ | - |
| `past_key_values` | `Cache` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[torch` | ✓ | - |
| `rope_deltas` | `torch` | ✓ | - |

### [New] [bugfix] Changes in modular_qwen3_5.py

- **File**: `venv\Lib\site-packages\transformers\models\qwen3_5\modular_qwen3_5.py`
- **Captured**: 4/28/2026, 12:52:51 PM
- **Category**: bugfix
**Summary:** Modified modular_qwen3_5.py: 691 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\qwen3_5\modular_qwen3_5.py` (+691 / -0)
**Schema: `Qwen3_5PreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Qwen3_5Config` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |

**Schema: `Qwen3_5VisionModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Qwen3_5VisionConfig` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |

**Schema: `Qwen3_5ModelOutputWithPast`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `pass` | `unknown` | ✓ | - |

**Schema: `Qwen3_5TextModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Qwen3_5TextConfig` | ✓ | - |

**Schema: `Qwen3_5Model`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_no_split_modules` | `unknown` | ✓ | - |

**Schema: `Qwen3_5ForSequenceClassification`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Qwen3_5TextConfig` | ✓ | - |

### [New] [bugfix] Changes in list.py

- **File**: `venv\Lib\site-packages\pip\_internal\commands\list.py`
- **Captured**: 4/28/2026, 12:52:49 PM
- **Category**: bugfix
**Summary:** Modified list.py: 401 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\pip\_internal\commands\list.py` (+401 / -0)
**Schema: `_DistWithLatestInfo`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_ProcessedDists` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modeling_qwen3_5_moe.py

- **File**: `venv\Lib\site-packages\transformers\models\qwen3_5_moe\modeling_qwen3_5_moe.py`
- **Captured**: 4/28/2026, 12:52:46 PM
- **Category**: bugfix
**Summary:** Modified modeling_qwen3_5_moe.py: 2399 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\qwen3_5_moe\modeling_qwen3_5_moe.py` (+2399 / -0)
**Schema: `Qwen3_5MoePreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Qwen3_5MoeConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_skip_keys_device_placement` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `_keys_to_ignore_on_load_unexpected` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |
| `_is_stateful` | `unknown` | ✓ | - |

**Schema: `Qwen3_5MoeVisionModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Qwen3_5MoeVisionConfig` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `Base` | `unknown` | ✓ | - |

**Schema: `Qwen3_5MoeModelOutputWithPast`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `past_key_values` | `unknown` | ✓ | - |
| `rope_deltas` | `unknown` | ✓ | - |
| `last_hidden_state` | `torch` | ✓ | - |
| `past_key_values` | `Cache` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[torch` | ✓ | - |
| `rope_deltas` | `torch` | ✓ | - |
| `router_logits` | `tuple[torch` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `Base` | `unknown` | ✓ | - |

**Schema: `Qwen3_5MoeCausalLMOutputWithPast`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `loss` | `unknown` | ✓ | - |
| `logits` | `unknown` | ✓ | - |
| `past_key_values` | `unknown` | ✓ | - |
| `rope_deltas` | `unknown` | ✓ | - |
| `loss` | `torch` | ✓ | - |
| `logits` | `torch` | ✓ | - |
| `past_key_values` | `Cache` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[torch` | ✓ | - |
| `rope_deltas` | `torch` | ✓ | - |
| `router_logits` | `tuple[torch` | ✓ | - |
| `aux_loss` | `torch` | ✓ | - |

**Schema: `Qwen3_5MoeTextModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Qwen3_5MoeTextConfig` | ✓ | - |

**Schema: `Qwen3_5MoeModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `base_model_prefix` | `unknown` | ✓ | - |
| `accepts_loss_kwargs` | `unknown` | ✓ | - |
| `config` | `Qwen3_5MoeConfig` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `gate_logits` | `torch` | ✓ | - |
| `num_experts` | `int` | ✓ | - |
| `top_k` | `unknown` | ✓ | - |
| `attention_mask` | `torch` | ✓ | - |
| `r` | `unknown` | ✓ | - |
| `Computes` | `unknown` | ✓ | - |
| `See` | `unknown` | ✓ | - |
| `function` | `unknown` | ✓ | - |
| `experts` | `unknown` | ✓ | - |
| `Args` | `gate_logits` | ✓ | - |
| `Returns` | `The auxiliary loss` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `routing_weights` | `unknown` | ✓ | - |
| `_` | `unknown` | ✓ | - |
| `expert_mask` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `else` | `batch_size, sequence_length` | ✓ | - |
| `overall_loss` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |

**Schema: `Qwen3_5MoeForCausalLM`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_tied_weights_keys` | `unknown` | ✓ | - |
| `_tp_plan` | `unknown` | ✓ | - |
| `_pp_plan` | `unknown` | ✓ | - |
| `config` | `Qwen3_5MoeTextConfig` | ✓ | - |
| `_keys_to_ignore_on_load_unexpected` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modular_qwen3_5_moe.py

- **File**: `venv\Lib\site-packages\transformers\models\qwen3_5_moe\modular_qwen3_5_moe.py`
- **Captured**: 4/28/2026, 12:52:44 PM
- **Category**: bugfix
**Summary:** Modified modular_qwen3_5_moe.py: 329 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\qwen3_5_moe\modular_qwen3_5_moe.py` (+329 / -0)
**Schema: `Qwen3_5MoePreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_no_split_modules` | `unknown` | ✓ | - |

**Schema: `Qwen3_5MoeVisionModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `pass` | `unknown` | ✓ | - |

**Schema: `Qwen3_5MoeModelOutputWithPast`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `router_logits` | `tuple[torch` | ✓ | - |

**Schema: `Qwen3_5MoeTextModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `pass` | `unknown` | ✓ | - |

**Schema: `Qwen3_5MoeModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `pass` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modeling_qwen3_moe.py

- **File**: `venv\Lib\site-packages\transformers\models\qwen3_moe\modeling_qwen3_moe.py`
- **Captured**: 4/28/2026, 12:52:42 PM
- **Category**: bugfix
**Summary:** Modified modeling_qwen3_moe.py: 732 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\qwen3_moe\modeling_qwen3_moe.py` (+732 / -0)
**Schema: `Qwen3MoePreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Qwen3MoeConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_skip_keys_device_placement` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `_supports_flex_attn` | `unknown` | ✓ | - |
| `_can_compile_fullgraph` | `unknown` | ✓ | - |
| `_supports_attention_backend` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |

**Schema: `Qwen3MoeModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `gate_logits` | `torch` | ✓ | - |
| `num_experts` | `int` | ✓ | - |
| `top_k` | `unknown` | ✓ | - |
| `attention_mask` | `torch` | ✓ | - |
| `r` | `unknown` | ✓ | - |
| `Computes` | `unknown` | ✓ | - |
| `See` | `unknown` | ✓ | - |
| `function` | `unknown` | ✓ | - |
| `experts` | `unknown` | ✓ | - |
| `Args` | `gate_logits` | ✓ | - |
| `Returns` | `The auxiliary loss` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `routing_weights` | `unknown` | ✓ | - |
| `_` | `unknown` | ✓ | - |
| `expert_mask` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `else` | `batch_size, sequence_length` | ✓ | - |
| `overall_loss` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |

**Schema: `Qwen3MoeForCausalLM`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_tied_weights_keys` | `unknown` | ✓ | - |
| `_tp_plan` | `unknown` | ✓ | - |
| `_pp_plan` | `unknown` | ✓ | - |

**Schema: `Qwen3MoeForSequenceClassification`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `pass` | `unknown` | ✓ | - |

**Schema: `Qwen3MoeForTokenClassification`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `pass` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in _z.py

- **File**: `venv\Lib\site-packages\plotly\graph_objs\surface\contours\_z.py`
- **Captured**: 4/28/2026, 12:52:39 PM
- **Category**: bugfix
**Summary:** Modified _z.py: 363 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\plotly\graph_objs\surface\contours\_z.py` (+363 / -0)
**Schema: `Z`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_parent_path_str` | `unknown` | ✓ | - |
| `_path_str` | `unknown` | ✓ | - |
| `_valid_props` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modeling_qwen3_next.py

- **File**: `venv\Lib\site-packages\transformers\models\qwen3_next\modeling_qwen3_next.py`
- **Captured**: 4/28/2026, 12:52:37 PM
- **Category**: bugfix
**Summary:** Modified modeling_qwen3_next.py: 1195 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\qwen3_next\modeling_qwen3_next.py` (+1195 / -0)
**Schema: `Qwen3NextPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Qwen3NextConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_skip_keys_device_placement` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `_keys_to_ignore_on_load_unexpected` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |
| `_is_stateful` | `unknown` | ✓ | - |

**Schema: `Qwen3NextModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `gate_logits` | `torch` | ✓ | - |
| `num_experts` | `int` | ✓ | - |
| `top_k` | `unknown` | ✓ | - |
| `attention_mask` | `torch` | ✓ | - |
| `r` | `unknown` | ✓ | - |
| `Computes` | `unknown` | ✓ | - |
| `See` | `unknown` | ✓ | - |
| `function` | `unknown` | ✓ | - |
| `experts` | `unknown` | ✓ | - |
| `Args` | `gate_logits` | ✓ | - |
| `Returns` | `The auxiliary loss` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `routing_weights` | `unknown` | ✓ | - |
| `_` | `unknown` | ✓ | - |
| `expert_mask` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `else` | `batch_size, sequence_length` | ✓ | - |
| `overall_loss` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |

**Schema: `Qwen3NextForCausalLM`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_tied_weights_keys` | `unknown` | ✓ | - |
| `_tp_plan` | `unknown` | ✓ | - |
| `_pp_plan` | `unknown` | ✓ | - |

**Schema: `Qwen3NextForSequenceClassification`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `pass` | `unknown` | ✓ | - |

**Schema: `Qwen3NextForTokenClassification`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `pass` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modular_qwen3_next.py

- **File**: `venv\Lib\site-packages\transformers\models\qwen3_next\modular_qwen3_next.py`
- **Captured**: 4/28/2026, 12:52:36 PM
- **Category**: bugfix
**Summary:** Modified modular_qwen3_next.py: 820 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\qwen3_next\modular_qwen3_next.py` (+820 / -0)
**Schema: `Qwen3NextPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Qwen3NextConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_skip_keys_device_placement` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `_keys_to_ignore_on_load_unexpected` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |
| `_is_stateful` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in ops.py

- **File**: `venv\Lib\site-packages\pandas\tests\extension\base\ops.py`
- **Captured**: 4/28/2026, 12:52:33 PM
- **Category**: bugfix
**Summary:** Modified ops.py: 288 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\pandas\tests\extension\base\ops.py` (+288 / -0)
**Schema: `BaseArithmeticOpsTests`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Various` | `unknown` | ✓ | - |
| `to` | `unknown` | ✓ | - |
| `series_scalar_exc` | `type[Exception]` | ✓ | - |
| `frame_scalar_exc` | `type[Exception]` | ✓ | - |
| `series_array_exc` | `type[Exception]` | ✓ | - |
| `divmod_exc` | `type[Exception]` | ✓ | - |

### [New] [bugfix] Changes in __init__.py

- **File**: `venv\Lib\site-packages\pandas\tests\extension\base\__init__.py`
- **Captured**: 4/28/2026, 12:52:32 PM
- **Category**: bugfix
**Summary:** Modified __init__.py: 90 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\pandas\tests\extension\base\__init__.py` (+90 / -0)
**Schema: `TestMyDtype`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Dim2CompatTests` | `unknown` | ✓ | - |
| `NDArrayBacked2DTests` | `unknown` | ✓ | - |
| `BaseArithmeticOpsTests` | `unknown` | ✓ | - |
| `BaseComparisonOpsTests` | `unknown` | ✓ | - |
| `BaseOpsUtil` | `unknown` | ✓ | - |
| `BaseUnaryOpsTests` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in _z.py

- **File**: `venv\Lib\site-packages\plotly\graph_objs\scatter3d\projection\_z.py`
- **Captured**: 4/28/2026, 12:52:31 PM
- **Category**: bugfix
**Summary:** Modified _z.py: 129 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\plotly\graph_objs\scatter3d\projection\_z.py` (+129 / -0)
**Schema: `Z`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_parent_path_str` | `unknown` | ✓ | - |
| `_path_str` | `unknown` | ✓ | - |
| `_valid_props` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modeling_qwen3_omni_moe.py

- **File**: `venv\Lib\site-packages\transformers\models\qwen3_omni_moe\modeling_qwen3_omni_moe.py`
- **Captured**: 4/28/2026, 12:52:28 PM
- **Category**: bugfix
**Summary:** Modified modeling_qwen3_omni_moe.py: 4096 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\qwen3_omni_moe\modeling_qwen3_omni_moe.py` (+4096 / -0)
**Schema: `BaseModelOutputWithDeepstackFeatures`** (pydantic)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `deepstack_features` | `unknown` | ✓ | - |
| `deepstack_features` | `list[torch` | ✓ | - |

**Schema: `Qwen3OmniMoePreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Qwen3OmniMoeConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_skip_keys_device_placement` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `_can_compile_fullgraph` | `unknown` | ✓ | - |
| `_supports_attention_backend` | `unknown` | ✓ | - |
| `Computes` | `unknown` | ✓ | - |
| `input_lengths_leave` | `unknown` | ✓ | - |
| `feat_lengths` | `unknown` | ✓ | - |
| `output_lengths` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |

**Schema: `Qwen3OmniMoePreTrainedModelForConditionalGeneration`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `input_modalities` | `unknown` | ✓ | - |
| `This` | `unknown` | ✓ | - |
| `num_key_value_heads` | `unknown` | ✓ | - |
| `batch` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `hidden_states` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `module` | `nn` | ✓ | - |
| `query` | `torch` | ✓ | - |
| `key` | `torch` | ✓ | - |
| `value` | `torch` | ✓ | - |
| `attention_mask` | `torch` | ✓ | - |
| `scaling` | `float,` | ✓ | - |
| `dropout` | `float` | ✓ | - |
| `key_states` | `unknown` | ✓ | - |
| `value_states` | `unknown` | ✓ | - |
| `attn_weights` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `attn_weights` | `unknown` | ✓ | - |
| `attn_weights` | `unknown` | ✓ | - |
| `attn_output` | `unknown` | ✓ | - |
| `attn_output` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |

**Schema: `Qwen3OmniMoeAudioEncoder`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Qwen3OmniMoeAudioEncoderConfig` | ✓ | - |
| `main_input_name` | `unknown` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |
| `x1` | `unknown` | ✓ | - |
| `x2` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `q` | `torch` | ✓ | - |
| `orig_q_dtype` | `unknown` | ✓ | - |
| `orig_k_dtype` | `unknown` | ✓ | - |
| `q` | `unknown` | ✓ | - |
| `cos` | `unknown` | ✓ | - |
| `q_embed` | `unknown` | ✓ | - |
| `k_embed` | `unknown` | ✓ | - |
| `q_embed` | `unknown` | ✓ | - |
| `k_embed` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |

**Schema: `Qwen3OmniMoeVisionEncoder`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Qwen3OmniMoeVisionEncoderConfig` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |

**Schema: `Qwen3OmniMoeThinkerTextPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `unknown` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_skip_keys_device_placement` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `_supports_flex_attn` | `unknown` | ✓ | - |
| `_can_compile_fullgraph` | `unknown` | ✓ | - |
| `_supports_attention_backend` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |

**Schema: `Qwen3OmniMoeThinkerTextModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Qwen3OmniMoeTextConfig` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |

**Schema: `Qwen3OmniMoeThinkerForConditionalGeneration`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Qwen3OmniMoeThinkerConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `_tied_weights_keys` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |

**Schema: `Qwen3OmniMoeTalkerCodePredictorModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `base_model_prefix` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |

**Schema: `Qwen3OmniMoeTalkerCodePredictorModelForConditionalGeneration`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_tied_weights_keys` | `unknown` | ✓ | - |
| `_tp_plan` | `unknown` | ✓ | - |
| `_pp_plan` | `unknown` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |

**Schema: `Qwen3OmniMoeTalkerModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Qwen3OmniMoeTextConfig` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |

**Schema: `Qwen3OmniMoeTalkerForConditionalGeneration`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_tied_weights_keys` | `unknown` | ✓ | - |
| `_tp_plan` | `unknown` | ✓ | - |
| `_pp_plan` | `unknown` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |

**Schema: `Qwen3OmniMoeCode2WavTransformerModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_can_record_outputs` | `unknown` | ✓ | - |

**Schema: `Qwen3OmniMoeCode2Wav`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `input_modalities` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modular_qwen3_omni_moe.py

- **File**: `venv\Lib\site-packages\transformers\models\qwen3_omni_moe\modular_qwen3_omni_moe.py`
- **Captured**: 4/28/2026, 12:52:27 PM
- **Category**: bugfix
**Summary:** Modified modular_qwen3_omni_moe.py: 2638 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\qwen3_omni_moe\modular_qwen3_omni_moe.py` (+2638 / -0)
**Schema: `BaseModelOutputWithDeepstackFeatures`** (pydantic)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `deepstack_features` | `unknown` | ✓ | - |
| `deepstack_features` | `list[torch` | ✓ | - |
| `Computes` | `unknown` | ✓ | - |
| `input_lengths_leave` | `unknown` | ✓ | - |
| `feat_lengths` | `unknown` | ✓ | - |
| `output_lengths` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |

**Schema: `Qwen3OmniMoeVisionEncoder`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Qwen3OmniMoeVisionEncoderConfig` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |

**Schema: `Qwen3OmniMoeThinkerTextPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `unknown` | ✓ | - |

**Schema: `Qwen3OmniMoeThinkerTextModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_can_record_outputs` | `unknown` | ✓ | - |

**Schema: `Qwen3OmniMoeTalkerCodePredictorModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `base_model_prefix` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |

**Schema: `Qwen3OmniMoeTalkerModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `base_model_prefix` | `unknown` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |

**Schema: `Qwen3OmniMoeCode2WavTransformerModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_can_record_outputs` | `unknown` | ✓ | - |

**Schema: `Qwen3OmniMoeCode2Wav`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `input_modalities` | `unknown` | ✓ | - |

**Schema: `Qwen3OmniMoeForConditionalGeneration`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `output_modalities` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in _error_z.py

- **File**: `venv\Lib\site-packages\plotly\graph_objs\scatter3d\_error_z.py`
- **Captured**: 4/28/2026, 12:52:25 PM
- **Category**: bugfix
**Summary:** Modified _error_z.py: 481 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\plotly\graph_objs\scatter3d\_error_z.py` (+481 / -0)
**Schema: `ErrorZ`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_parent_path_str` | `unknown` | ✓ | - |
| `_path_str` | `unknown` | ✓ | - |
| `_valid_props` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in _projection.py

- **File**: `venv\Lib\site-packages\plotly\graph_objs\scatter3d\_projection.py`
- **Captured**: 4/28/2026, 12:52:23 PM
- **Category**: bugfix
**Summary:** Modified _projection.py: 133 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\plotly\graph_objs\scatter3d\_projection.py` (+133 / -0)
**Schema: `Projection`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_parent_path_str` | `unknown` | ✓ | - |
| `_path_str` | `unknown` | ✓ | - |
| `_valid_props` | `unknown` | ✓ | - |

### [bugfix] Changes in Pricing.jsx

- **File**: `frontend\src\pages\Pricing.jsx`
- **Captured**: 4/28/2026, 12:52:21 PM
- **Category**: bugfix
**Summary:** Modified Pricing.jsx: 452 lines added, 0 lines removed.
**Files Modified:**
  - `frontend\src\pages\Pricing.jsx` (+452 / -0)

### [New] [bugfix] Changes in auth.py

- **File**: `venv\Lib\site-packages\pip\_internal\network\auth.py`
- **Captured**: 4/28/2026, 12:52:18 PM
- **Category**: bugfix
**Summary:** Modified auth.py: 565 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\pip\_internal\network\auth.py` (+565 / -0)
**Schema: `KeyRingNullProvider`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `has_keyring` | `unknown` | ✓ | - |

**Schema: `KeyRingPythonProvider`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `has_keyring` | `unknown` | ✓ | - |

**Schema: `KeyRingCliProvider`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Instead` | `unknown` | ✓ | - |
| `we` | `unknown` | ✓ | - |
| `use` | `unknown` | ✓ | - |
| `PATH` | `unknown` | ✓ | - |
| `has_keyring` | `unknown` | ✓ | - |
| `logger` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `logger` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in session.py

- **File**: `venv\Lib\site-packages\pip\_internal\network\session.py`
- **Captured**: 4/28/2026, 12:52:16 PM
- **Category**: bugfix
**Summary:** Modified session.py: 529 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\pip\_internal\network\session.py` (+529 / -0)
**Schema: `HTTPAdapter`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `pass` | `unknown` | ✓ | - |

**Schema: `CacheControlAdapter`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `pass` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modeling_qwen3_vl.py

- **File**: `venv\Lib\site-packages\transformers\models\qwen3_vl\modeling_qwen3_vl.py`
- **Captured**: 4/28/2026, 12:52:13 PM
- **Category**: bugfix
**Summary:** Modified modeling_qwen3_vl.py: 1771 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\qwen3_vl\modeling_qwen3_vl.py` (+1771 / -0)
**Schema: `BaseModelOutputWithDeepstackFeatures`** (pydantic)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `deepstack_features` | `unknown` | ✓ | - |
| `deepstack_features` | `list[torch` | ✓ | - |

**Schema: `Qwen3VLModelOutputWithPast`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `past_key_values` | `unknown` | ✓ | - |
| `rope_deltas` | `unknown` | ✓ | - |
| `last_hidden_state` | `torch` | ✓ | - |
| `past_key_values` | `Cache` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[torch` | ✓ | - |
| `rope_deltas` | `torch` | ✓ | - |

**Schema: `Qwen3VLPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Qwen3VLConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_skip_keys_device_placement` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `_can_compile_fullgraph` | `unknown` | ✓ | - |
| `_supports_attention_backend` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |

**Schema: `Qwen3VLVisionModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Qwen3VLVisionConfig` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |

**Schema: `Qwen3VLTextModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Qwen3VLTextConfig` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |

**Schema: `Qwen3VLModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `base_model_prefix` | `unknown` | ✓ | - |
| `accepts_loss_kwargs` | `unknown` | ✓ | - |
| `config` | `Qwen3VLConfig` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `Base` | `unknown` | ✓ | - |

**Schema: `Qwen3VLCausalLMOutputWithPast`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `loss` | `unknown` | ✓ | - |
| `logits` | `unknown` | ✓ | - |
| `past_key_values` | `unknown` | ✓ | - |
| `rope_deltas` | `unknown` | ✓ | - |
| `loss` | `torch` | ✓ | - |
| `logits` | `torch` | ✓ | - |
| `past_key_values` | `Cache` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[torch` | ✓ | - |
| `rope_deltas` | `torch` | ✓ | - |

### [New] [bugfix] Changes in modular_qwen3_vl.py

- **File**: `venv\Lib\site-packages\transformers\models\qwen3_vl\modular_qwen3_vl.py`
- **Captured**: 4/28/2026, 12:52:11 PM
- **Category**: bugfix
**Summary:** Modified modular_qwen3_vl.py: 1332 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\qwen3_vl\modular_qwen3_vl.py` (+1332 / -0)
**Schema: `BaseModelOutputWithDeepstackFeatures`** (pydantic)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `deepstack_features` | `unknown` | ✓ | - |
| `deepstack_features` | `list[torch` | ✓ | - |

**Schema: `Qwen3VLModelOutputWithPast`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `pass` | `unknown` | ✓ | - |

**Schema: `Qwen3VLPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Qwen3VLConfig` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |

**Schema: `Qwen3VLVisionModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Qwen3VLVisionConfig` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |

**Schema: `Qwen3VLTextModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Qwen3VLTextConfig` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |

**Schema: `Qwen3VLModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Qwen3VLConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in codegen.py

- **File**: `venv\Lib\site-packages\sympy\utilities\codegen.py`
- **Captured**: 4/28/2026, 12:52:09 PM
- **Category**: bugfix
**Summary:** Modified codegen.py: 2238 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\sympy\utilities\codegen.py` (+2238 / -0)
**Schema: `Result`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `The` | `unknown` | ✓ | - |
| `These` | `unknown` | ✓ | - |
| `might` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in _contours.py

- **File**: `venv\Lib\site-packages\plotly\graph_objs\surface\_contours.py`
- **Captured**: 4/28/2026, 12:52:06 PM
- **Category**: bugfix
**Summary:** Modified _contours.py: 133 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\plotly\graph_objs\surface\_contours.py` (+133 / -0)
**Schema: `Contours`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_parent_path_str` | `unknown` | ✓ | - |
| `_path_str` | `unknown` | ✓ | - |
| `_valid_props` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in _lightposition.py

- **File**: `venv\Lib\site-packages\plotly\graph_objs\surface\_lightposition.py`
- **Captured**: 4/28/2026, 12:52:03 PM
- **Category**: bugfix
**Summary:** Modified _lightposition.py: 130 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\plotly\graph_objs\surface\_lightposition.py` (+130 / -0)
**Schema: `Lightposition`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_parent_path_str` | `unknown` | ✓ | - |
| `_path_str` | `unknown` | ✓ | - |
| `_valid_props` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modeling_qwen3_vl_moe.py

- **File**: `venv\Lib\site-packages\transformers\models\qwen3_vl_moe\modeling_qwen3_vl_moe.py`
- **Captured**: 4/28/2026, 12:52:00 PM
- **Category**: bugfix
**Summary:** Modified modeling_qwen3_vl_moe.py: 1973 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\qwen3_vl_moe\modeling_qwen3_vl_moe.py` (+1973 / -0)
**Schema: `Qwen3VLMoePreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Qwen3VLMoeConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_skip_keys_device_placement` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `_supports_flex_attn` | `unknown` | ✓ | - |
| `_can_compile_fullgraph` | `unknown` | ✓ | - |
| `_supports_attention_backend` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |

**Schema: `BaseModelOutputWithDeepstackFeatures`** (pydantic)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `deepstack_features` | `unknown` | ✓ | - |
| `deepstack_features` | `list[torch` | ✓ | - |

**Schema: `Qwen3VLMoeVisionModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Qwen3VLMoeVisionConfig` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |

**Schema: `Qwen3VLMoeTextModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Qwen3VLMoeTextConfig` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `Base` | `unknown` | ✓ | - |

**Schema: `Qwen3VLMoeModelOutputWithPast`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `past_key_values` | `unknown` | ✓ | - |
| `rope_deltas` | `unknown` | ✓ | - |
| `last_hidden_state` | `torch` | ✓ | - |
| `past_key_values` | `Cache` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[torch` | ✓ | - |
| `rope_deltas` | `torch` | ✓ | - |
| `router_logits` | `tuple[torch` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `Base` | `unknown` | ✓ | - |

**Schema: `Qwen3VLMoeCausalLMOutputWithPast`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `loss` | `unknown` | ✓ | - |
| `logits` | `unknown` | ✓ | - |
| `past_key_values` | `unknown` | ✓ | - |
| `rope_deltas` | `unknown` | ✓ | - |
| `loss` | `torch` | ✓ | - |
| `logits` | `torch` | ✓ | - |
| `past_key_values` | `Cache` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[torch` | ✓ | - |
| `rope_deltas` | `torch` | ✓ | - |
| `router_logits` | `tuple[torch` | ✓ | - |
| `aux_loss` | `torch` | ✓ | - |

**Schema: `Qwen3VLMoeModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `base_model_prefix` | `unknown` | ✓ | - |
| `accepts_loss_kwargs` | `unknown` | ✓ | - |
| `config` | `Qwen3VLMoeConfig` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `gate_logits` | `torch` | ✓ | - |
| `num_experts` | `int` | ✓ | - |
| `top_k` | `unknown` | ✓ | - |
| `attention_mask` | `torch` | ✓ | - |
| `r` | `unknown` | ✓ | - |
| `Computes` | `unknown` | ✓ | - |
| `See` | `unknown` | ✓ | - |
| `function` | `unknown` | ✓ | - |
| `experts` | `unknown` | ✓ | - |
| `Args` | `gate_logits` | ✓ | - |
| `Returns` | `The auxiliary loss` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `routing_weights` | `unknown` | ✓ | - |
| `_` | `unknown` | ✓ | - |
| `expert_mask` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `else` | `batch_size, sequence_length` | ✓ | - |
| `overall_loss` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modular_qwen3_vl_moe.py

- **File**: `venv\Lib\site-packages\transformers\models\qwen3_vl_moe\modular_qwen3_vl_moe.py`
- **Captured**: 4/28/2026, 12:51:58 PM
- **Category**: bugfix
**Summary:** Modified modular_qwen3_vl_moe.py: 460 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\qwen3_vl_moe\modular_qwen3_vl_moe.py` (+460 / -0)
**Schema: `Qwen3VLMoePreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `Qwen3VLMoeConfig` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |

**Schema: `Qwen3VLMoeVisionModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_can_record_outputs` | `unknown` | ✓ | - |

**Schema: `Qwen3VLMoeModelOutputWithPast`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `router_logits` | `tuple[torch` | ✓ | - |

### [New] [bugfix] Changes in modeling_rag.py

- **File**: `venv\Lib\site-packages\transformers\models\rag\modeling_rag.py`
- **Captured**: 4/28/2026, 12:51:52 PM
- **Category**: bugfix
**Summary:** Modified modeling_rag.py: 1666 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\rag\modeling_rag.py` (+1666 / -0)
**Schema: `RetrievAugLMMarginOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `loss` | `unknown` | ✓ | - |
| `logits` | `unknown` | ✓ | - |
| `doc_scores` | `unknown` | ✓ | - |
| `past_key_values` | `unknown` | ✓ | - |
| `retrieved_doc_embeds` | `unknown` | ✓ | - |
| `retrieved_doc_ids` | `unknown` | ✓ | - |
| `context_input_ids` | `unknown` | ✓ | - |
| `context_attention_mask` | `unknown` | ✓ | - |
| `question_encoder_last_hidden_state` | `unknown` | ✓ | - |
| `question_enc_hidden_states` | `unknown` | ✓ | - |
| `question_enc_attentions` | `unknown` | ✓ | - |
| `generator_enc_last_hidden_state` | `unknown` | ✓ | - |
| `generator_enc_hidden_states` | `unknown` | ✓ | - |
| `generator_enc_attentions` | `unknown` | ✓ | - |
| `generator_dec_hidden_states` | `unknown` | ✓ | - |
| `generator_dec_attentions` | `unknown` | ✓ | - |
| `generator_cross_attentions` | `unknown` | ✓ | - |
| `loss` | `torch` | ✓ | - |
| `logits` | `torch` | ✓ | - |
| `doc_scores` | `torch` | ✓ | - |
| `past_key_values` | `Cache` | ✓ | - |
| `retrieved_doc_embeds` | `torch` | ✓ | - |
| `retrieved_doc_ids` | `torch` | ✓ | - |
| `context_input_ids` | `torch` | ✓ | - |
| `context_attention_mask` | `torch` | ✓ | - |
| `question_encoder_last_hidden_state` | `torch` | ✓ | - |
| `question_enc_hidden_states` | `tuple[torch` | ✓ | - |
| `question_enc_attentions` | `tuple[torch` | ✓ | - |
| `generator_enc_last_hidden_state` | `torch` | ✓ | - |
| `generator_enc_hidden_states` | `tuple[torch` | ✓ | - |
| `generator_enc_attentions` | `tuple[torch` | ✓ | - |
| `generator_dec_hidden_states` | `tuple[torch` | ✓ | - |
| `generator_dec_attentions` | `tuple[torch` | ✓ | - |
| `generator_cross_attentions` | `tuple[torch` | ✓ | - |

**Schema: `RetrievAugLMOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `logits` | `unknown` | ✓ | - |
| `doc_scores` | `unknown` | ✓ | - |
| `past_key_values` | `unknown` | ✓ | - |
| `retrieved_doc_embeds` | `unknown` | ✓ | - |
| `retrieved_doc_ids` | `unknown` | ✓ | - |
| `context_input_ids` | `unknown` | ✓ | - |
| `context_attention_mask` | `unknown` | ✓ | - |
| `question_encoder_last_hidden_state` | `unknown` | ✓ | - |
| `question_enc_hidden_states` | `unknown` | ✓ | - |
| `question_enc_attentions` | `unknown` | ✓ | - |
| `generator_enc_last_hidden_state` | `unknown` | ✓ | - |
| `generator_enc_hidden_states` | `unknown` | ✓ | - |
| `generator_enc_attentions` | `unknown` | ✓ | - |
| `generator_dec_hidden_states` | `unknown` | ✓ | - |
| `generator_dec_attentions` | `unknown` | ✓ | - |
| `generator_cross_attentions` | `unknown` | ✓ | - |
| `logits` | `torch` | ✓ | - |
| `doc_scores` | `torch` | ✓ | - |
| `past_key_values` | `Cache` | ✓ | - |
| `retrieved_doc_embeds` | `torch` | ✓ | - |
| `retrieved_doc_ids` | `torch` | ✓ | - |
| `context_input_ids` | `torch` | ✓ | - |
| `context_attention_mask` | `torch` | ✓ | - |
| `question_encoder_last_hidden_state` | `torch` | ✓ | - |
| `question_enc_hidden_states` | `tuple[torch` | ✓ | - |
| `question_enc_attentions` | `tuple[torch` | ✓ | - |
| `generator_enc_last_hidden_state` | `torch` | ✓ | - |
| `generator_enc_hidden_states` | `tuple[torch` | ✓ | - |
| `generator_enc_attentions` | `tuple[torch` | ✓ | - |
| `generator_dec_hidden_states` | `tuple[torch` | ✓ | - |
| `generator_dec_attentions` | `tuple[torch` | ✓ | - |
| `generator_cross_attentions` | `tuple[torch` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `RAG` | `unknown` | ✓ | - |
| `Tasks` | `unknown` | ✓ | - |
| `RAG` | `unknown` | ✓ | - |
| `generator` | `unknown` | ✓ | - |

**Schema: `RagPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `RagConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |

**Schema: `RagModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `custom_intro` | `unknown` | ✓ | - |
| `A` | `unknown` | ✓ | - |

**Schema: `RagSequenceForGeneration`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `custom_intro` | `unknown` | ✓ | - |
| `A` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in retrieval_rag.py

- **File**: `venv\Lib\site-packages\transformers\models\rag\retrieval_rag.py`
- **Captured**: 4/28/2026, 12:51:50 PM
- **Category**: bugfix
**Summary:** Modified retrieval_rag.py: 677 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\rag\retrieval_rag.py` (+677 / -0)
**API Endpoints** (`retrieval_rag.py`):

| Method | Route | Handler | Middleware |
|--------|-------|---------|------------|
| `PATH (`STR`, OPTIONAL` | `str` | index_path | - |
**Schema: `CanonicalHFIndex`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `A` | `unknown` | ✓ | - |
| `index` | `unknown` | ✓ | - |
| `on` | `unknown` | ✓ | - |
| `Args` | `vector_size` | ✓ | - |

**Schema: `CustomHFIndex`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `A` | `unknown` | ✓ | - |
| `indicated` | `unknown` | ✓ | - |
| `Args` | `vector_size` | ✓ | - |

### [New] [bugfix] Changes in model.py

- **File**: `venv\Lib\site-packages\sentence_transformers\sparse_encoder\model.py`
- **Captured**: 4/28/2026, 12:51:48 PM
- **Category**: bugfix
**Summary:** Modified model.py: 1300 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\sentence_transformers\sparse_encoder\model.py` (+1300 / -0)
**Schema: `SparseEncoder`** (pydantic)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Loads` | `unknown` | ✓ | - |
| `Args` | `model_name_or_path` | ✓ | - |
| `Example` | `unknown` | ✓ | - |
| `_model_card_model_id_placeholder` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modeling_recurrent_gemma.py

- **File**: `venv\Lib\site-packages\transformers\models\recurrent_gemma\modeling_recurrent_gemma.py`
- **Captured**: 4/28/2026, 12:51:39 PM
- **Category**: bugfix
**Summary:** Modified modeling_recurrent_gemma.py: 791 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\recurrent_gemma\modeling_recurrent_gemma.py` (+791 / -0)
**Schema: `RecurrentGemmaPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `RecurrentGemmaConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_skip_keys_device_placement` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modeling_reformer.py

- **File**: `venv\Lib\site-packages\transformers\models\reformer\modeling_reformer.py`
- **Captured**: 4/28/2026, 12:51:35 PM
- **Category**: bugfix
**Summary:** Modified modeling_reformer.py: 2671 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\reformer\modeling_reformer.py` (+2671 / -0)
**Schema: `ReformerPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `ReformerConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `Output` | `unknown` | ✓ | - |

**Schema: `ReformerModelOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `last_hidden_state` | `unknown` | ✓ | - |
| `past_buckets_states` | `unknown` | ✓ | - |
| `last_hidden_state` | `torch` | ✓ | - |
| `past_buckets_states` | `list[tuple[torch` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[torch` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `Output` | `unknown` | ✓ | - |

**Schema: `ReformerModelWithLMHeadOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `loss` | `unknown` | ✓ | - |
| `logits` | `unknown` | ✓ | - |
| `past_buckets_states` | `unknown` | ✓ | - |
| `loss` | `torch` | ✓ | - |
| `logits` | `torch` | ✓ | - |
| `past_buckets_states` | `list[tuple[torch` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[torch` | ✓ | - |

**Schema: `ReformerModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `custom_intro` | `unknown` | ✓ | - |
| `Reformer` | `unknown` | ✓ | - |

**Schema: `ReformerForMaskedLM`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `custom_intro` | `unknown` | ✓ | - |
| `Reformer` | `unknown` | ✓ | - |
| `pooled` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modeling_regnet.py

- **File**: `venv\Lib\site-packages\transformers\models\regnet\modeling_regnet.py`
- **Captured**: 4/28/2026, 12:51:28 PM
- **Category**: bugfix
**Summary:** Modified modeling_regnet.py: 385 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\regnet\modeling_regnet.py` (+385 / -0)
**Schema: `RegNetPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `RegNetConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `main_input_name` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |

**Schema: `RegNetModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `custom_intro` | `unknown` | ✓ | - |
| `RegNet` | `unknown` | ✓ | - |
| `ImageNet` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modeling_rembert.py

- **File**: `venv\Lib\site-packages\transformers\models\rembert\modeling_rembert.py`
- **Captured**: 4/28/2026, 12:51:25 PM
- **Category**: bugfix
**Summary:** Modified modeling_rembert.py: 1143 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\rembert\modeling_rembert.py` (+1143 / -0)
**Schema: `RemBertPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `RemBertConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `cross` | `unknown` | ✓ | - |
| `all` | `unknown` | ✓ | - |
| `Llion` | `unknown` | ✓ | - |
| `To` | `unknown` | ✓ | - |
| `to` | `unknown` | ✓ | - |

**Schema: `RemBertForMaskedLM`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `custom_intro` | `unknown` | ✓ | - |
| `RemBERT` | `unknown` | ✓ | - |

**Schema: `RemBertForCausalLM`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `custom_intro` | `unknown` | ✓ | - |
| `RemBERT` | `unknown` | ✓ | - |
| `pooled` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modeling_resnet.py

- **File**: `venv\Lib\site-packages\transformers\models\resnet\modeling_resnet.py`
- **Captured**: 4/28/2026, 12:51:20 PM
- **Category**: bugfix
**Summary:** Modified modeling_resnet.py: 455 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\resnet\modeling_resnet.py` (+455 / -0)
**Schema: `ResNetPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `ResNetConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `main_input_name` | `unknown` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |

**Schema: `ResNetModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `custom_intro` | `unknown` | ✓ | - |
| `ResNet` | `unknown` | ✓ | - |
| `ImageNet` | `unknown` | ✓ | - |

**Schema: `ResNetForImageClassification`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `custom_intro` | `unknown` | ✓ | - |
| `ResNet` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modeling_roberta.py

- **File**: `venv\Lib\site-packages\transformers\models\roberta\modeling_roberta.py`
- **Captured**: 4/28/2026, 12:51:14 PM
- **Category**: bugfix
**Summary:** Modified modeling_roberta.py: 1272 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\roberta\modeling_roberta.py` (+1272 / -0)
**Schema: `RobertaPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `base_model_prefix` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `_supports_flex_attn` | `unknown` | ✓ | - |
| `_supports_attention_backend` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |

**Schema: `RobertaModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_no_split_modules` | `unknown` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `RoBERTa` | `unknown` | ✓ | - |

**Schema: `RobertaForCausalLM`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_tied_weights_keys` | `unknown` | ✓ | - |

**Schema: `RobertaForMaskedLM`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_tied_weights_keys` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modular_roberta.py

- **File**: `venv\Lib\site-packages\transformers\models\roberta\modular_roberta.py`
- **Captured**: 4/28/2026, 12:51:13 PM
- **Category**: bugfix
**Summary:** Modified modular_roberta.py: 772 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\roberta\modular_roberta.py` (+772 / -0)
**Schema: `RobertaPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `base_model_prefix` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `_supports_flex_attn` | `unknown` | ✓ | - |
| `_supports_attention_backend` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |

**Schema: `RobertaModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `custom_intro` | `unknown` | ✓ | - |
| `RoBERTa` | `unknown` | ✓ | - |

**Schema: `RobertaForCausalLM`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_tied_weights_keys` | `unknown` | ✓ | - |

**Schema: `RobertaForMaskedLM`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_tied_weights_keys` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modeling_roberta_prelayernorm.py

- **File**: `venv\Lib\site-packages\transformers\models\roberta_prelayernorm\modeling_roberta_prelayernorm.py`
- **Captured**: 4/28/2026, 12:51:09 PM
- **Category**: bugfix
**Summary:** Modified modeling_roberta_prelayernorm.py: 1313 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\roberta_prelayernorm\modeling_roberta_prelayernorm.py` (+1313 / -0)
**Schema: `RobertaPreLayerNormPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `base_model_prefix` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `_supports_flex_attn` | `unknown` | ✓ | - |
| `_supports_attention_backend` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `cross` | `unknown` | ✓ | - |
| `all` | `unknown` | ✓ | - |
| `Kaiser` | `unknown` | ✓ | - |
| `To` | `unknown` | ✓ | - |
| `to` | `unknown` | ✓ | - |

**Schema: `RobertaPreLayerNormModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `custom_intro` | `unknown` | ✓ | - |
| `RoBERTa` | `unknown` | ✓ | - |

**Schema: `RobertaPreLayerNormForCausalLM`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_tied_weights_keys` | `unknown` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `RoBERTa` | `unknown` | ✓ | - |

**Schema: `RobertaPreLayerNormForMaskedLM`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_tied_weights_keys` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in specifiers.py

- **File**: `venv\Lib\site-packages\pip\_vendor\packaging\specifiers.py`
- **Captured**: 4/28/2026, 12:51:08 PM
- **Category**: bugfix
**Summary:** Modified specifiers.py: 1020 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\pip\_vendor\packaging\specifiers.py` (+1020 / -0)
**Schema: `Specifier`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_operator_regex_str` | `unknown` | ✓ | - |
| `_version_regex_str` | `unknown` | ✓ | - |
| `_regex` | `unknown` | ✓ | - |
| `_operators` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `not` | `unknown` | ✓ | - |
| `components` | `unknown` | ✓ | - |
| `version` | `unknown` | ✓ | - |
| `result` | `list[str]` | ✓ | - |
| `epoch` | `unknown` | ✓ | - |
| `result` | `unknown` | ✓ | - |
| `for` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `This` | `unknown` | ✓ | - |
| `first` | `unknown` | ✓ | - |
| `components` | `unknown` | ✓ | - |
| `epoch` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `left_split` | `unknown` | ✓ | - |
| `left_split` | `unknown` | ✓ | - |
| `right_split` | `unknown` | ✓ | - |
| `left_split` | `unknown` | ✓ | - |
| `right_split` | `unknown` | ✓ | - |
| `left_split` | `unknown` | ✓ | - |
| `right_split` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in version.py

- **File**: `venv\Lib\site-packages\pip\_vendor\packaging\version.py`
- **Captured**: 4/28/2026, 12:51:07 PM
- **Category**: bugfix
**Summary:** Modified version.py: 583 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\pip\_vendor\packaging\version.py` (+583 / -0)
**Schema: `Version`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `A` | `class` | ✓ | - |
| `sorted` | `unknown` | ✓ | - |
| `True` | `unknown` | ✓ | - |
| `False` | `unknown` | ✓ | - |
| `False` | `unknown` | ✓ | - |
| `False` | `unknown` | ✓ | - |
| `True` | `unknown` | ✓ | - |
| `_regex` | `unknown` | ✓ | - |
| `_key` | `CmpKey` | ✓ | - |

### [New] [bugfix] Changes in modeling_roc_bert.py

- **File**: `venv\Lib\site-packages\transformers\models\roc_bert\modeling_roc_bert.py`
- **Captured**: 4/28/2026, 12:51:04 PM
- **Category**: bugfix
**Summary:** Modified modeling_roc_bert.py: 1661 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\roc_bert\modeling_roc_bert.py` (+1661 / -0)
**Schema: `RoCBertPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `base_model_prefix` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `_supports_flex_attn` | `unknown` | ✓ | - |
| `_supports_attention_backend` | `unknown` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `cross` | `unknown` | ✓ | - |
| `all` | `unknown` | ✓ | - |
| `Llion` | `unknown` | ✓ | - |
| `To` | `unknown` | ✓ | - |
| `to` | `unknown` | ✓ | - |

**Schema: `RoCBertModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `custom_intro` | `unknown` | ✓ | - |
| `RoCBert` | `unknown` | ✓ | - |

**Schema: `RoCBertForPreTraining`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_tied_weights_keys` | `unknown` | ✓ | - |

**Schema: `RoCBertForMaskedLM`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_tied_weights_keys` | `unknown` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `RoCBert` | `unknown` | ✓ | - |

**Schema: `RoCBertForCausalLM`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_tied_weights_keys` | `unknown` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `RoCBert` | `unknown` | ✓ | - |
| `the` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in code39.py

- **File**: `venv\Lib\site-packages\reportlab\graphics\barcode\code39.py`
- **Captured**: 4/28/2026, 12:51:00 PM
- **Category**: bugfix
**Summary:** Modified code39.py: 245 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\reportlab\graphics\barcode\code39.py` (+245 / -0)
**Schema: `Standard39`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Options` | `unknown` | ✓ | - |
| `Sources` | `unknown` | ✓ | - |
| `http` | `unknown` | ✓ | - |
| `http` | `unknown` | ✓ | - |
| `http` | `unknown` | ✓ | - |
| `Official` | `unknown` | ✓ | - |
| `http` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in code93.py

- **File**: `venv\Lib\site-packages\reportlab\graphics\barcode\code93.py`
- **Captured**: 4/28/2026, 12:50:58 PM
- **Category**: bugfix
**Summary:** Modified code93.py: 235 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\reportlab\graphics\barcode\code93.py` (+235 / -0)
**Schema: `Standard93`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Code` | `unknown` | ✓ | - |
| `See` | `unknown` | ✓ | - |
| `128` | `unknown` | ✓ | - |
| `Options` | `unknown` | ✓ | - |
| `Sources` | `unknown` | ✓ | - |
| `http` | `unknown` | ✓ | - |
| `Official` | `unknown` | ✓ | - |
| `http` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modeling_roformer.py

- **File**: `venv\Lib\site-packages\transformers\models\roformer\modeling_roformer.py`
- **Captured**: 4/28/2026, 12:50:54 PM
- **Category**: bugfix
**Summary:** Modified modeling_roformer.py: 1308 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\roformer\modeling_roformer.py` (+1308 / -0)
**Schema: `RoFormerPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `RoFormerConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `supports_gradient_checkpointing` | `unknown` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `cross` | `unknown` | ✓ | - |
| `all` | `unknown` | ✓ | - |
| `Llion` | `unknown` | ✓ | - |
| `To` | `unknown` | ✓ | - |
| `to` | `unknown` | ✓ | - |

**Schema: `RoFormerForMaskedLM`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_tied_weights_keys` | `unknown` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `RoFormer` | `unknown` | ✓ | - |

**Schema: `RoFormerForCausalLM`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_tied_weights_keys` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in file_cache.py

- **File**: `venv\Lib\site-packages\pip\_vendor\cachecontrol\caches\file_cache.py`
- **Captured**: 4/28/2026, 12:50:51 PM
- **Category**: bugfix
**Summary:** Modified file_cache.py: 146 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\pip\_vendor\cachecontrol\caches\file_cache.py` (+146 / -0)
**Schema: `FileCache`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Traditional` | `unknown` | ✓ | - |
| `downloads` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modeling_rt_detr.py

- **File**: `venv\Lib\site-packages\transformers\models\rt_detr\modeling_rt_detr.py`
- **Captured**: 4/28/2026, 12:50:49 PM
- **Category**: bugfix
**Summary:** Modified modeling_rt_detr.py: 1848 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\rt_detr\modeling_rt_detr.py` (+1848 / -0)
**Schema: `RTDetrDecoderOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `intermediate_hidden_states` | `unknown` | ✓ | - |
| `intermediate_logits` | `unknown` | ✓ | - |
| `intermediate_reference_points` | `unknown` | ✓ | - |
| `intermediate_predicted_corners` | `unknown` | ✓ | - |
| `initial_reference_points` | `unknown` | ✓ | - |
| `cross_attentions` | `unknown` | ✓ | - |
| `last_hidden_state` | `torch` | ✓ | - |
| `intermediate_hidden_states` | `torch` | ✓ | - |
| `intermediate_logits` | `torch` | ✓ | - |
| `intermediate_reference_points` | `torch` | ✓ | - |
| `intermediate_predicted_corners` | `torch` | ✓ | - |
| `initial_reference_points` | `torch` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[torch` | ✓ | - |
| `cross_attentions` | `tuple[torch` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `Base` | `unknown` | ✓ | - |

**Schema: `RTDetrModelOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `last_hidden_state` | `unknown` | ✓ | - |
| `intermediate_hidden_states` | `unknown` | ✓ | - |
| `intermediate_logits` | `unknown` | ✓ | - |
| `intermediate_reference_points` | `unknown` | ✓ | - |
| `intermediate_predicted_corners` | `unknown` | ✓ | - |
| `initial_reference_points` | `unknown` | ✓ | - |
| `init_reference_points` | `unknown` | ✓ | - |
| `enc_topk_logits` | `unknown` | ✓ | - |
| `enc_topk_bboxes` | `unknown` | ✓ | - |
| `enc_outputs_coord_logits` | `unknown` | ✓ | - |
| `denoising_meta_values` | `unknown` | ✓ | - |
| `last_hidden_state` | `torch` | ✓ | - |
| `intermediate_hidden_states` | `torch` | ✓ | - |
| `intermediate_logits` | `torch` | ✓ | - |
| `intermediate_reference_points` | `torch` | ✓ | - |
| `intermediate_predicted_corners` | `torch` | ✓ | - |
| `initial_reference_points` | `torch` | ✓ | - |
| `decoder_hidden_states` | `tuple[torch` | ✓ | - |
| `decoder_attentions` | `tuple[torch` | ✓ | - |
| `cross_attentions` | `tuple[torch` | ✓ | - |
| `encoder_last_hidden_state` | `torch` | ✓ | - |
| `encoder_hidden_states` | `tuple[torch` | ✓ | - |
| `encoder_attentions` | `tuple[torch` | ✓ | - |
| `init_reference_points` | `torch` | ✓ | - |
| `enc_topk_logits` | `torch` | ✓ | - |
| `enc_topk_bboxes` | `torch` | ✓ | - |
| `enc_outputs_coord_logits` | `torch` | ✓ | - |
| `denoising_meta_values` | `dict` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `Output` | `unknown` | ✓ | - |

**Schema: `RTDetrObjectDetectionOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `loss` | `unknown` | ✓ | - |
| `loss_dict` | `unknown` | ✓ | - |
| `logits` | `unknown` | ✓ | - |
| `pred_boxes` | `unknown` | ✓ | - |
| `auxiliary_outputs` | `unknown` | ✓ | - |
| `last_hidden_state` | `unknown` | ✓ | - |
| `intermediate_hidden_states` | `unknown` | ✓ | - |
| `intermediate_logits` | `unknown` | ✓ | - |
| `intermediate_reference_points` | `unknown` | ✓ | - |
| `intermediate_predicted_corners` | `unknown` | ✓ | - |
| `initial_reference_points` | `unknown` | ✓ | - |
| `init_reference_points` | `unknown` | ✓ | - |
| `enc_topk_logits` | `unknown` | ✓ | - |
| `enc_topk_bboxes` | `unknown` | ✓ | - |
| `enc_outputs_coord_logits` | `unknown` | ✓ | - |
| `denoising_meta_values` | `unknown` | ✓ | - |
| `loss` | `torch` | ✓ | - |
| `loss_dict` | `dict` | ✓ | - |
| `logits` | `torch` | ✓ | - |
| `pred_boxes` | `torch` | ✓ | - |
| `auxiliary_outputs` | `list[dict]` | ✓ | - |
| `last_hidden_state` | `torch` | ✓ | - |
| `intermediate_hidden_states` | `torch` | ✓ | - |
| `intermediate_logits` | `torch` | ✓ | - |
| `intermediate_reference_points` | `torch` | ✓ | - |
| `intermediate_predicted_corners` | `torch` | ✓ | - |
| `initial_reference_points` | `torch` | ✓ | - |
| `decoder_hidden_states` | `tuple[torch` | ✓ | - |
| `decoder_attentions` | `tuple[torch` | ✓ | - |
| `cross_attentions` | `tuple[torch` | ✓ | - |
| `encoder_last_hidden_state` | `torch` | ✓ | - |
| `encoder_hidden_states` | `tuple[torch` | ✓ | - |
| `encoder_attentions` | `tuple[torch` | ✓ | - |
| `init_reference_points` | `tuple[torch` | ✓ | - |
| `enc_topk_logits` | `torch` | ✓ | - |
| `enc_topk_bboxes` | `torch` | ✓ | - |
| `enc_outputs_coord_logits` | `torch` | ✓ | - |
| `denoising_meta_values` | `dict` | ✓ | - |

**Schema: `RTDetrPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `RTDetrConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `main_input_name` | `unknown` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_supports_attention_backend` | `unknown` | ✓ | - |
| `_supports_flex_attn` | `unknown` | ✓ | - |

**Schema: `RTDetrHybridEncoder`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Hybrid` | `unknown` | ✓ | - |
| `a` | `unknown` | ✓ | - |
| `More` | `unknown` | ✓ | - |
| `Args` | `config` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |
| `x` | `unknown` | ✓ | - |
| `x1` | `unknown` | ✓ | - |
| `x2` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |

**Schema: `RTDetrDecoder`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_can_record_outputs` | `unknown` | ✓ | - |
| `targets` | `unknown` | ✓ | - |
| `num_queries` | `unknown` | ✓ | - |
| `num_denoising_queries` | `unknown` | ✓ | - |
| `label_noise_ratio` | `unknown` | ✓ | - |
| `box_noise_scale` | `unknown` | ✓ | - |
| `Creates` | `unknown` | ✓ | - |
| `Args` | `targets` | ✓ | - |
| `Returns` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `num_ground_truths` | `unknown` | ✓ | - |
| `device` | `unknown` | ✓ | - |
| `max_gt_num` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `num_groups_denoising_queries` | `unknown` | ✓ | - |
| `num_groups_denoising_queries` | `unknown` | ✓ | - |
| `batch_size` | `unknown` | ✓ | - |
| `input_query_bbox` | `unknown` | ✓ | - |
| `pad_gt_mask` | `unknown` | ✓ | - |
| `for` | `unknown` | ✓ | - |
| `input_query_bbox` | `unknown` | ✓ | - |
| `pad_gt_mask` | `unknown` | ✓ | - |
| `negative_gt_mask` | `unknown` | ✓ | - |
| `negative_gt_mask` | `unknown` | ✓ | - |
| `negative_gt_mask` | `unknown` | ✓ | - |
| `positive_gt_mask` | `unknown` | ✓ | - |
| `positive_gt_mask` | `unknown` | ✓ | - |
| `denoise_positive_idx` | `unknown` | ✓ | - |
| `denoise_positive_idx` | `unknown` | ✓ | - |
| `num_denoising_queries` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `target_size` | `unknown` | ✓ | - |
| `attn_mask` | `unknown` | ✓ | - |
| `attn_mask` | `unknown` | ✓ | - |
| `for` | `unknown` | ✓ | - |
| `denoising_meta_values` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `RT` | `unknown` | ✓ | - |

**Schema: `RTDetrModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `custom_intro` | `unknown` | ✓ | - |
| `RT` | `unknown` | ✓ | - |
| `decoded` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modeling_rt_detr_resnet.py

- **File**: `venv\Lib\site-packages\transformers\models\rt_detr\modeling_rt_detr_resnet.py`
- **Captured**: 4/28/2026, 12:50:48 PM
- **Category**: bugfix
**Summary:** Modified modeling_rt_detr_resnet.py: 413 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\rt_detr\modeling_rt_detr_resnet.py` (+413 / -0)
**Schema: `RTDetrResNetPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `RTDetrResNetConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `main_input_name` | `unknown` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `ResNet` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in modular_rt_detr.py

- **File**: `venv\Lib\site-packages\transformers\models\rt_detr\modular_rt_detr.py`
- **Captured**: 4/28/2026, 12:50:46 PM
- **Category**: bugfix
**Summary:** Modified modular_rt_detr.py: 2154 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\rt_detr\modular_rt_detr.py` (+2154 / -0)
**Schema: `RTDetrDecoderOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `intermediate_hidden_states` | `unknown` | ✓ | - |
| `intermediate_logits` | `unknown` | ✓ | - |
| `intermediate_reference_points` | `unknown` | ✓ | - |
| `intermediate_predicted_corners` | `unknown` | ✓ | - |
| `initial_reference_points` | `unknown` | ✓ | - |
| `cross_attentions` | `unknown` | ✓ | - |
| `last_hidden_state` | `torch` | ✓ | - |
| `intermediate_hidden_states` | `torch` | ✓ | - |
| `intermediate_logits` | `torch` | ✓ | - |
| `intermediate_reference_points` | `torch` | ✓ | - |
| `intermediate_predicted_corners` | `torch` | ✓ | - |
| `initial_reference_points` | `torch` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[torch` | ✓ | - |
| `cross_attentions` | `tuple[torch` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `Base` | `unknown` | ✓ | - |

**Schema: `RTDetrModelOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `last_hidden_state` | `unknown` | ✓ | - |
| `intermediate_hidden_states` | `unknown` | ✓ | - |
| `intermediate_logits` | `unknown` | ✓ | - |
| `intermediate_reference_points` | `unknown` | ✓ | - |
| `intermediate_predicted_corners` | `unknown` | ✓ | - |
| `initial_reference_points` | `unknown` | ✓ | - |
| `init_reference_points` | `unknown` | ✓ | - |
| `enc_topk_logits` | `unknown` | ✓ | - |
| `enc_topk_bboxes` | `unknown` | ✓ | - |
| `enc_outputs_coord_logits` | `unknown` | ✓ | - |
| `denoising_meta_values` | `unknown` | ✓ | - |
| `last_hidden_state` | `torch` | ✓ | - |
| `intermediate_hidden_states` | `torch` | ✓ | - |
| `intermediate_logits` | `torch` | ✓ | - |
| `intermediate_reference_points` | `torch` | ✓ | - |
| `intermediate_predicted_corners` | `torch` | ✓ | - |
| `initial_reference_points` | `torch` | ✓ | - |
| `decoder_hidden_states` | `tuple[torch` | ✓ | - |
| `decoder_attentions` | `tuple[torch` | ✓ | - |
| `cross_attentions` | `tuple[torch` | ✓ | - |
| `encoder_last_hidden_state` | `torch` | ✓ | - |
| `encoder_hidden_states` | `tuple[torch` | ✓ | - |
| `encoder_attentions` | `tuple[torch` | ✓ | - |
| `init_reference_points` | `torch` | ✓ | - |
| `enc_topk_logits` | `torch` | ✓ | - |
| `enc_topk_bboxes` | `torch` | ✓ | - |
| `enc_outputs_coord_logits` | `torch` | ✓ | - |
| `denoising_meta_values` | `dict` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `Output` | `unknown` | ✓ | - |

**Schema: `RTDetrObjectDetectionOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `loss` | `unknown` | ✓ | - |
| `loss_dict` | `unknown` | ✓ | - |
| `logits` | `unknown` | ✓ | - |
| `pred_boxes` | `unknown` | ✓ | - |
| `auxiliary_outputs` | `unknown` | ✓ | - |
| `last_hidden_state` | `unknown` | ✓ | - |
| `intermediate_hidden_states` | `unknown` | ✓ | - |
| `intermediate_logits` | `unknown` | ✓ | - |
| `intermediate_reference_points` | `unknown` | ✓ | - |
| `intermediate_predicted_corners` | `unknown` | ✓ | - |
| `initial_reference_points` | `unknown` | ✓ | - |
| `init_reference_points` | `unknown` | ✓ | - |
| `enc_topk_logits` | `unknown` | ✓ | - |
| `enc_topk_bboxes` | `unknown` | ✓ | - |
| `enc_outputs_coord_logits` | `unknown` | ✓ | - |
| `denoising_meta_values` | `unknown` | ✓ | - |
| `loss` | `torch` | ✓ | - |
| `loss_dict` | `dict` | ✓ | - |
| `logits` | `torch` | ✓ | - |
| `pred_boxes` | `torch` | ✓ | - |
| `auxiliary_outputs` | `list[dict]` | ✓ | - |
| `last_hidden_state` | `torch` | ✓ | - |
| `intermediate_hidden_states` | `torch` | ✓ | - |
| `intermediate_logits` | `torch` | ✓ | - |
| `intermediate_reference_points` | `torch` | ✓ | - |
| `intermediate_predicted_corners` | `torch` | ✓ | - |
| `initial_reference_points` | `torch` | ✓ | - |
| `decoder_hidden_states` | `tuple[torch` | ✓ | - |
| `decoder_attentions` | `tuple[torch` | ✓ | - |
| `cross_attentions` | `tuple[torch` | ✓ | - |
| `encoder_last_hidden_state` | `torch` | ✓ | - |
| `encoder_hidden_states` | `tuple[torch` | ✓ | - |
| `encoder_attentions` | `tuple[torch` | ✓ | - |
| `init_reference_points` | `tuple[torch` | ✓ | - |
| `enc_topk_logits` | `torch` | ✓ | - |
| `enc_topk_bboxes` | `torch` | ✓ | - |
| `enc_outputs_coord_logits` | `torch` | ✓ | - |
| `denoising_meta_values` | `dict` | ✓ | - |

**Schema: `RTDetrPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `config` | `RTDetrConfig` | ✓ | - |
| `base_model_prefix` | `unknown` | ✓ | - |
| `main_input_name` | `unknown` | ✓ | - |
| `input_modalities` | `unknown` | ✓ | - |
| `_no_split_modules` | `unknown` | ✓ | - |
| `_supports_sdpa` | `unknown` | ✓ | - |
| `_supports_flash_attn` | `unknown` | ✓ | - |
| `_supports_attention_backend` | `unknown` | ✓ | - |
| `_supports_flex_attn` | `unknown` | ✓ | - |

**Schema: `RTDetrHybridEncoder`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Hybrid` | `unknown` | ✓ | - |
| `a` | `unknown` | ✓ | - |
| `More` | `unknown` | ✓ | - |
| `Args` | `config` | ✓ | - |
| `_can_record_outputs` | `unknown` | ✓ | - |

**Schema: `RTDetrDecoder`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_can_record_outputs` | `unknown` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `RT` | `unknown` | ✓ | - |

**Schema: `RTDetrModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `custom_intro` | `unknown` | ✓ | - |
| `RT` | `unknown` | ✓ | - |
| `decoded` | `unknown` | ✓ | - |

### [New] [bugfix] Changes in styledpil.py

- **File**: `venv\Lib\site-packages\qrcode\image\styledpil.py`
- **Captured**: 4/28/2026, 12:50:43 PM
- **Category**: bugfix
**Summary:** Modified styledpil.py: 121 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\qrcode\image\styledpil.py` (+121 / -0)
**Schema: `StyledPilImage`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Styled` | `unknown` | ✓ | - |
| `This` | `unknown` | ✓ | - |
| `color_mask` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `drawrect_context` | `unknown` | ✓ | - |
| `initialize` | `unknown` | ✓ | - |
| `the` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `implement` | `unknown` | ✓ | - |
| `put` | `unknown` | ✓ | - |
| `can` | `unknown` | ✓ | - |
| `QRColorMask` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |
| `is` | `unknown` | ✓ | - |
| `ensure` | `unknown` | ✓ | - |
| `there` | `unknown` | ✓ | - |
| `data` | `unknown` | ✓ | - |
| `PIL` | `unknown` | ✓ | - |

## Architecture Decisions

### [New] [architecture] Changes in modeling_outputs.py

- **File**: `venv\Lib\site-packages\transformers\modeling_outputs.py`
- **Captured**: 4/28/2026, 1:05:25 PM
- **Category**: architecture
**Summary:** Modified modeling_outputs.py: 1707 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\modeling_outputs.py` (+1707 / -0)
**Schema: `BaseModelOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Base` | `unknown` | ✓ | - |
| `Args` | `last_hidden_state` | ✓ | - |
| `last_hidden_state` | `torch` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[torch` | ✓ | - |

**Schema: `BaseModelOutputWithNoAttention`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Base` | `unknown` | ✓ | - |
| `Args` | `last_hidden_state` | ✓ | - |
| `last_hidden_state` | `torch` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |

**Schema: `BaseModelOutputWithPooling`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Base` | `unknown` | ✓ | - |
| `Args` | `last_hidden_state` | ✓ | - |
| `last_hidden_state` | `torch` | ✓ | - |
| `pooler_output` | `torch` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[torch` | ✓ | - |

**Schema: `BaseModelOutputWithPoolingAndNoAttention`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Base` | `unknown` | ✓ | - |
| `Args` | `last_hidden_state` | ✓ | - |
| `last_hidden_state` | `torch` | ✓ | - |
| `pooler_output` | `torch` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |

**Schema: `BaseModelOutputWithPast`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Base` | `unknown` | ✓ | - |
| `Args` | `last_hidden_state` | ✓ | - |
| `last_hidden_state` | `torch` | ✓ | - |
| `past_key_values` | `Cache` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[torch` | ✓ | - |

**Schema: `BaseModelOutputWithCrossAttentions`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Base` | `unknown` | ✓ | - |
| `Args` | `last_hidden_state` | ✓ | - |
| `last_hidden_state` | `torch` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[torch` | ✓ | - |
| `cross_attentions` | `tuple[torch` | ✓ | - |

**Schema: `BaseModelOutputWithPoolingAndCrossAttentions`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Base` | `unknown` | ✓ | - |
| `Args` | `last_hidden_state` | ✓ | - |
| `last_hidden_state` | `torch` | ✓ | - |
| `pooler_output` | `torch` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `past_key_values` | `Cache` | ✓ | - |
| `attentions` | `tuple[torch` | ✓ | - |
| `cross_attentions` | `tuple[torch` | ✓ | - |

**Schema: `BaseModelOutputWithPastAndCrossAttentions`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Base` | `unknown` | ✓ | - |
| `Args` | `last_hidden_state` | ✓ | - |
| `last_hidden_state` | `torch` | ✓ | - |
| `past_key_values` | `Cache` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[torch` | ✓ | - |
| `cross_attentions` | `tuple[torch` | ✓ | - |

**Schema: `MoECausalLMOutputWithPast`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Base` | `unknown` | ✓ | - |
| `states` | `unknown` | ✓ | - |
| `Args` | `loss` | ✓ | - |
| `loss` | `torch` | ✓ | - |
| `logits` | `torch` | ✓ | - |
| `past_key_values` | `Cache` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[torch` | ✓ | - |
| `z_loss` | `torch` | ✓ | - |
| `aux_loss` | `torch` | ✓ | - |
| `router_logits` | `tuple[torch` | ✓ | - |

**Schema: `MoEModelOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Base` | `unknown` | ✓ | - |
| `Args` | `last_hidden_state` | ✓ | - |
| `last_hidden_state` | `torch` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[torch` | ✓ | - |
| `router_probs` | `tuple[torch` | ✓ | - |
| `router_logits` | `tuple[torch` | ✓ | - |

**Schema: `MoeModelOutputWithPast`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Base` | `unknown` | ✓ | - |
| `Args` | `last_hidden_state` | ✓ | - |
| `last_hidden_state` | `torch` | ✓ | - |
| `past_key_values` | `Cache` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[torch` | ✓ | - |
| `router_logits` | `tuple[torch` | ✓ | - |

**Schema: `MoeCausalLMOutputWithPast`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Base` | `unknown` | ✓ | - |
| `Args` | `loss` | ✓ | - |
| `loss` | `torch` | ✓ | - |
| `aux_loss` | `torch` | ✓ | - |
| `logits` | `torch` | ✓ | - |
| `past_key_values` | `Cache` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[torch` | ✓ | - |
| `router_logits` | `tuple[torch` | ✓ | - |

**Schema: `MoEModelOutputWithPastAndCrossAttentions`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Base` | `unknown` | ✓ | - |
| `Mixture` | `unknown` | ✓ | - |
| `Args` | `last_hidden_state` | ✓ | - |
| `last_hidden_state` | `torch` | ✓ | - |
| `past_key_values` | `Cache` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[torch` | ✓ | - |
| `cross_attentions` | `tuple[torch` | ✓ | - |
| `router_probs` | `tuple[torch` | ✓ | - |
| `router_logits` | `tuple[torch` | ✓ | - |

**Schema: `Seq2SeqModelOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Base` | `unknown` | ✓ | - |
| `decoding` | `unknown` | ✓ | - |
| `Args` | `last_hidden_state` | ✓ | - |
| `last_hidden_state` | `torch` | ✓ | - |
| `past_key_values` | `EncoderDecoderCache` | ✓ | - |
| `decoder_hidden_states` | `tuple[torch` | ✓ | - |
| `decoder_attentions` | `tuple[torch` | ✓ | - |
| `cross_attentions` | `tuple[torch` | ✓ | - |
| `encoder_last_hidden_state` | `torch` | ✓ | - |
| `encoder_hidden_states` | `tuple[torch` | ✓ | - |
| `encoder_attentions` | `tuple[torch` | ✓ | - |

**Schema: `Seq2SeqMoEModelOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Base` | `unknown` | ✓ | - |
| `decoding` | `unknown` | ✓ | - |
| `Args` | `last_hidden_state` | ✓ | - |
| `last_hidden_state` | `torch` | ✓ | - |
| `past_key_values` | `EncoderDecoderCache` | ✓ | - |
| `decoder_hidden_states` | `tuple[torch` | ✓ | - |
| `decoder_attentions` | `tuple[torch` | ✓ | - |
| `decoder_router_logits` | `tuple[torch` | ✓ | - |
| `cross_attentions` | `tuple[torch` | ✓ | - |
| `encoder_last_hidden_state` | `torch` | ✓ | - |
| `encoder_hidden_states` | `tuple[torch` | ✓ | - |
| `encoder_attentions` | `tuple[torch` | ✓ | - |
| `encoder_router_logits` | `tuple[torch` | ✓ | - |

**Schema: `CausalLMOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Base` | `unknown` | ✓ | - |
| `Args` | `loss` | ✓ | - |
| `loss` | `torch` | ✓ | - |
| `logits` | `torch` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[torch` | ✓ | - |

**Schema: `CausalLMOutputWithPast`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Base` | `unknown` | ✓ | - |
| `Args` | `loss` | ✓ | - |
| `loss` | `torch` | ✓ | - |
| `logits` | `torch` | ✓ | - |
| `past_key_values` | `Cache` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[torch` | ✓ | - |

**Schema: `CausalLMOutputWithCrossAttentions`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Base` | `unknown` | ✓ | - |
| `Args` | `loss` | ✓ | - |
| `loss` | `torch` | ✓ | - |
| `logits` | `torch` | ✓ | - |
| `past_key_values` | `Cache` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[torch` | ✓ | - |
| `cross_attentions` | `tuple[torch` | ✓ | - |

**Schema: `SequenceClassifierOutputWithPast`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Base` | `unknown` | ✓ | - |
| `Args` | `loss` | ✓ | - |
| `loss` | `torch` | ✓ | - |
| `logits` | `torch` | ✓ | - |
| `past_key_values` | `Cache` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[torch` | ✓ | - |

**Schema: `MaskedLMOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Base` | `unknown` | ✓ | - |
| `Args` | `loss` | ✓ | - |
| `loss` | `torch` | ✓ | - |
| `logits` | `torch` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[torch` | ✓ | - |

**Schema: `Seq2SeqLMOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Base` | `unknown` | ✓ | - |
| `Args` | `loss` | ✓ | - |
| `loss` | `torch` | ✓ | - |
| `logits` | `torch` | ✓ | - |
| `past_key_values` | `EncoderDecoderCache` | ✓ | - |
| `decoder_hidden_states` | `tuple[torch` | ✓ | - |
| `decoder_attentions` | `tuple[torch` | ✓ | - |
| `cross_attentions` | `tuple[torch` | ✓ | - |
| `encoder_last_hidden_state` | `torch` | ✓ | - |
| `encoder_hidden_states` | `tuple[torch` | ✓ | - |
| `encoder_attentions` | `tuple[torch` | ✓ | - |

**Schema: `Seq2SeqMoEOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Base` | `unknown` | ✓ | - |
| `Args` | `loss` | ✓ | - |
| `loss` | `torch` | ✓ | - |
| `logits` | `torch` | ✓ | - |
| `encoder_z_loss` | `torch` | ✓ | - |
| `decoder_z_loss` | `torch` | ✓ | - |
| `encoder_aux_loss` | `torch` | ✓ | - |
| `decoder_aux_loss` | `torch` | ✓ | - |
| `past_key_values` | `EncoderDecoderCache` | ✓ | - |
| `decoder_hidden_states` | `tuple[torch` | ✓ | - |
| `decoder_attentions` | `tuple[torch` | ✓ | - |
| `decoder_router_logits` | `tuple[torch` | ✓ | - |
| `cross_attentions` | `tuple[torch` | ✓ | - |
| `encoder_last_hidden_state` | `torch` | ✓ | - |
| `encoder_hidden_states` | `tuple[torch` | ✓ | - |
| `encoder_attentions` | `tuple[torch` | ✓ | - |
| `encoder_router_logits` | `tuple[torch` | ✓ | - |

**Schema: `NextSentencePredictorOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Base` | `unknown` | ✓ | - |
| `Args` | `loss` | ✓ | - |
| `loss` | `torch` | ✓ | - |
| `logits` | `torch` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[torch` | ✓ | - |

**Schema: `SequenceClassifierOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Base` | `unknown` | ✓ | - |
| `Args` | `loss` | ✓ | - |
| `loss` | `torch` | ✓ | - |
| `logits` | `torch` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[torch` | ✓ | - |

**Schema: `Seq2SeqSequenceClassifierOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Base` | `unknown` | ✓ | - |
| `Args` | `loss` | ✓ | - |
| `loss` | `torch` | ✓ | - |
| `logits` | `torch` | ✓ | - |
| `past_key_values` | `EncoderDecoderCache` | ✓ | - |
| `decoder_hidden_states` | `tuple[torch` | ✓ | - |
| `decoder_attentions` | `tuple[torch` | ✓ | - |
| `cross_attentions` | `tuple[torch` | ✓ | - |
| `encoder_last_hidden_state` | `torch` | ✓ | - |
| `encoder_hidden_states` | `tuple[torch` | ✓ | - |
| `encoder_attentions` | `tuple[torch` | ✓ | - |

**Schema: `MultipleChoiceModelOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Base` | `unknown` | ✓ | - |
| `Args` | `loss` | ✓ | - |
| `loss` | `torch` | ✓ | - |
| `logits` | `torch` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[torch` | ✓ | - |

**Schema: `TokenClassifierOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Base` | `unknown` | ✓ | - |
| `Args` | `loss` | ✓ | - |
| `loss` | `torch` | ✓ | - |
| `logits` | `torch` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[torch` | ✓ | - |

**Schema: `QuestionAnsweringModelOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Base` | `unknown` | ✓ | - |
| `Args` | `loss` | ✓ | - |
| `loss` | `torch` | ✓ | - |
| `start_logits` | `torch` | ✓ | - |
| `end_logits` | `torch` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[torch` | ✓ | - |

**Schema: `Seq2SeqQuestionAnsweringModelOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Base` | `unknown` | ✓ | - |
| `Args` | `loss` | ✓ | - |
| `loss` | `torch` | ✓ | - |
| `start_logits` | `torch` | ✓ | - |
| `end_logits` | `torch` | ✓ | - |
| `past_key_values` | `EncoderDecoderCache` | ✓ | - |
| `decoder_hidden_states` | `tuple[torch` | ✓ | - |
| `decoder_attentions` | `tuple[torch` | ✓ | - |
| `cross_attentions` | `tuple[torch` | ✓ | - |
| `encoder_last_hidden_state` | `torch` | ✓ | - |
| `encoder_hidden_states` | `tuple[torch` | ✓ | - |
| `encoder_attentions` | `tuple[torch` | ✓ | - |

**Schema: `SemanticSegmenterOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Base` | `unknown` | ✓ | - |
| `Args` | `loss` | ✓ | - |
| `loss` | `torch` | ✓ | - |
| `logits` | `torch` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[torch` | ✓ | - |

**Schema: `ImageClassifierOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Base` | `unknown` | ✓ | - |
| `Args` | `loss` | ✓ | - |
| `loss` | `torch` | ✓ | - |
| `logits` | `torch` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[torch` | ✓ | - |

**Schema: `ImageClassifierOutputWithNoAttention`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Base` | `unknown` | ✓ | - |
| `Args` | `loss` | ✓ | - |
| `loss` | `torch` | ✓ | - |
| `logits` | `torch` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |

**Schema: `DepthEstimatorOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Base` | `unknown` | ✓ | - |
| `Args` | `loss` | ✓ | - |
| `loss` | `torch` | ✓ | - |
| `predicted_depth` | `torch` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[torch` | ✓ | - |

**Schema: `ImageSuperResolutionOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Base` | `unknown` | ✓ | - |
| `Args` | `loss` | ✓ | - |
| `loss` | `torch` | ✓ | - |
| `reconstruction` | `torch` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[torch` | ✓ | - |

**Schema: `Wav2Vec2BaseModelOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Base` | `unknown` | ✓ | - |
| `Args` | `last_hidden_state` | ✓ | - |
| `last_hidden_state` | `torch` | ✓ | - |
| `extract_features` | `torch` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[torch` | ✓ | - |

**Schema: `XVectorOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Output` | `unknown` | ✓ | - |
| `Args` | `loss` | ✓ | - |
| `loss` | `torch` | ✓ | - |
| `logits` | `torch` | ✓ | - |
| `embeddings` | `torch` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[torch` | ✓ | - |

**Schema: `BackboneOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Base` | `unknown` | ✓ | - |
| `Args` | `feature_maps` | ✓ | - |
| `feature_maps` | `tuple[torch` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[torch` | ✓ | - |

**Schema: `BaseModelOutputWithPoolingAndProjection`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Base` | `unknown` | ✓ | - |
| `Args` | `last_hidden_state` | ✓ | - |
| `last_hidden_state` | `torch` | ✓ | - |
| `pooler_output` | `torch` | ✓ | - |
| `hidden_states` | `tuple[torch` | ✓ | - |
| `attentions` | `tuple[torch` | ✓ | - |
| `projection_state` | `tuple[torch` | ✓ | - |

**Schema: `Seq2SeqSpectrogramOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Base` | `unknown` | ✓ | - |
| `Args` | `loss` | ✓ | - |
| `loss` | `torch` | ✓ | - |
| `spectrogram` | `torch` | ✓ | - |
| `past_key_values` | `EncoderDecoderCache` | ✓ | - |
| `decoder_hidden_states` | `tuple[torch` | ✓ | - |
| `decoder_attentions` | `tuple[torch` | ✓ | - |
| `cross_attentions` | `tuple[torch` | ✓ | - |
| `encoder_last_hidden_state` | `torch` | ✓ | - |
| `encoder_hidden_states` | `tuple[torch` | ✓ | - |
| `encoder_attentions` | `tuple[torch` | ✓ | - |

**Schema: `Seq2SeqTSModelOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Base` | `unknown` | ✓ | - |
| `sequential` | `unknown` | ✓ | - |
| `Args` | `last_hidden_state` | ✓ | - |
| `last_hidden_state` | `torch` | ✓ | - |
| `past_key_values` | `EncoderDecoderCache` | ✓ | - |
| `decoder_hidden_states` | `tuple[torch` | ✓ | - |
| `decoder_attentions` | `tuple[torch` | ✓ | - |
| `cross_attentions` | `tuple[torch` | ✓ | - |
| `encoder_last_hidden_state` | `torch` | ✓ | - |
| `encoder_hidden_states` | `tuple[torch` | ✓ | - |
| `encoder_attentions` | `tuple[torch` | ✓ | - |
| `loc` | `torch` | ✓ | - |
| `scale` | `torch` | ✓ | - |
| `static_features` | `torch` | ✓ | - |

**Schema: `Seq2SeqTSPredictionOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Base` | `unknown` | ✓ | - |
| `chosen` | `unknown` | ✓ | - |
| `Args` | `loss` | ✓ | - |
| `loss` | `torch` | ✓ | - |
| `params` | `tuple[torch` | ✓ | - |
| `past_key_values` | `EncoderDecoderCache` | ✓ | - |
| `decoder_hidden_states` | `tuple[torch` | ✓ | - |
| `decoder_attentions` | `tuple[torch` | ✓ | - |
| `cross_attentions` | `tuple[torch` | ✓ | - |
| `encoder_last_hidden_state` | `torch` | ✓ | - |
| `encoder_hidden_states` | `tuple[torch` | ✓ | - |
| `encoder_attentions` | `tuple[torch` | ✓ | - |
| `loc` | `torch` | ✓ | - |
| `scale` | `torch` | ✓ | - |
| `static_features` | `torch` | ✓ | - |

**Schema: `SampleTSPredictionOutput`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Base` | `unknown` | ✓ | - |
| `distribution` | `unknown` | ✓ | - |
| `Args` | `sequences` | ✓ | - |
| `sequences` | `torch` | ✓ | - |

### [New] [architecture] Changes in modular_apertus.py

- **File**: `venv\Lib\site-packages\transformers\models\apertus\modular_apertus.py`
- **Captured**: 4/28/2026, 1:04:54 PM
- **Category**: architecture
**Summary:** Modified modular_apertus.py: 269 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\apertus\modular_apertus.py` (+269 / -0)
**Schema: `ApertusPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `pass` | `unknown` | ✓ | - |

**Schema: `ApertusModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `pass` | `unknown` | ✓ | - |

### [New] [architecture] Changes in modular_audioflamingo3.py

- **File**: `venv\Lib\site-packages\transformers\models\audioflamingo3\modular_audioflamingo3.py`
- **Captured**: 4/28/2026, 1:04:17 PM
- **Category**: architecture
**Summary:** Modified modular_audioflamingo3.py: 305 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\audioflamingo3\modular_audioflamingo3.py` (+305 / -0)
**Schema: `AudioFlamingo3PreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `pass` | `unknown` | ✓ | - |
| `custom_intro` | `unknown` | ✓ | - |
| `The` | `unknown` | ✓ | - |

### [New] [architecture] Changes in _models.py

- **File**: `venv\Lib\site-packages\scipy\odr\_models.py`
- **Captured**: 4/28/2026, 12:58:39 PM
- **Category**: architecture
**Summary:** Modified _models.py: 334 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\scipy\odr\_models.py` (+334 / -0)
**Schema: `_MultilinearModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `Arbitrary` | `unknown` | ✓ | - |
| `This` | `unknown` | ✓ | - |
| `Examples` | `unknown` | ✓ | - |
| `We` | `unknown` | ✓ | - |
| `dimensional` | `unknown` | ✓ | - |
| `multilinear` | `unknown` | ✓ | - |
| `Factory` | `unknown` | ✓ | - |
| `Parameters` | `unknown` | ✓ | - |
| `order` | `int or sequence` | ✓ | - |
| `Returns` | `unknown` | ✓ | - |
| `polynomial` | `Model instance` | ✓ | - |
| `Examples` | `unknown` | ✓ | - |
| `We` | `unknown` | ✓ | - |
| `a` | `unknown` | ✓ | - |
| `powers` | `unknown` | ✓ | - |
| `if` | `unknown` | ✓ | - |
| `powers` | `unknown` | ✓ | - |
| `len_beta` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |

**Schema: `_ExponentialModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `Exponential` | `unknown` | ✓ | - |
| `This` | `unknown` | ✓ | - |
| `Examples` | `unknown` | ✓ | - |
| `We` | `unknown` | ✓ | - |
| `exponential` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `_ret` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `_ret` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |
| `return` | `unknown` | ✓ | - |

**Schema: `_UnilinearModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `r` | `unknown` | ✓ | - |
| `Univariate` | `unknown` | ✓ | - |
| `This` | `unknown` | ✓ | - |
| `Examples` | `unknown` | ✓ | - |
| `We` | `unknown` | ✓ | - |
| `unilinear` | `unknown` | ✓ | - |

### [New] [architecture] Changes in modular_phi3.py

- **File**: `venv\Lib\site-packages\transformers\models\phi3\modular_phi3.py`
- **Captured**: 4/28/2026, 12:58:19 PM
- **Category**: architecture
**Summary:** Modified modular_phi3.py: 265 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\phi3\modular_phi3.py` (+265 / -0)
**Schema: `Phi3PreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_version` | `unknown` | ✓ | - |

### [New] [architecture] Changes in report.py

- **File**: `venv\Lib\site-packages\scipy\optimize\_trustregion_constr\report.py`
- **Captured**: 4/28/2026, 12:56:57 PM
- **Category**: architecture
**Summary:** Modified report.py: 50 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\scipy\optimize\_trustregion_constr\report.py` (+50 / -0)
**Schema: `BasicReport`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `COLUMN_NAMES` | `unknown` | ✓ | - |
| `COLUMN_WIDTHS` | `unknown` | ✓ | - |
| `ITERATION_FORMATS` | `unknown` | ✓ | - |

**Schema: `SQPReport`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `COLUMN_NAMES` | `unknown` | ✓ | - |
| `COLUMN_WIDTHS` | `unknown` | ✓ | - |
| `ITERATION_FORMATS` | `unknown` | ✓ | - |

### [New] [architecture] Changes in modular_pp_ocrv5_mobile_det.py

- **File**: `venv\Lib\site-packages\transformers\models\pp_ocrv5_mobile_det\modular_pp_ocrv5_mobile_det.py`
- **Captured**: 4/28/2026, 12:55:09 PM
- **Category**: architecture
**Summary:** Modified modular_pp_ocrv5_mobile_det.py: 271 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\pp_ocrv5_mobile_det\modular_pp_ocrv5_mobile_det.py` (+271 / -0)
**Schema: `PPOCRV5MobileDetPreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `pass` | `unknown` | ✓ | - |

**Schema: `PPOCRV5MobileDetModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `custom_intro` | `unknown` | ✓ | - |
| `PPOCRV5` | `unknown` | ✓ | - |
| `and` | `unknown` | ✓ | - |

### [New] [architecture] Changes in modular_pp_ocrv5_mobile_rec.py

- **File**: `venv\Lib\site-packages\transformers\models\pp_ocrv5_mobile_rec\modular_pp_ocrv5_mobile_rec.py`
- **Captured**: 4/28/2026, 12:55:02 PM
- **Category**: architecture
**Summary:** Modified modular_pp_ocrv5_mobile_rec.py: 84 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\pp_ocrv5_mobile_rec\modular_pp_ocrv5_mobile_rec.py` (+84 / -0)
**Schema: `PPOCRV5MobileRecModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `pass` | `unknown` | ✓ | - |

### [New] [architecture] Changes in model_card.py

- **File**: `venv\Lib\site-packages\sentence_transformers\sentence_transformer\model_card.py`
- **Captured**: 4/28/2026, 12:53:01 PM
- **Category**: architecture
**Summary:** Modified model_card.py: 197 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\sentence_transformers\sentence_transformer\model_card.py` (+197 / -0)
**Schema: `SentenceTransformerModelCardCallback`** (pydantic)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `pass` | `unknown` | ✓ | - |

**Schema: `SentenceTransformerModelCardData`** (pydantic)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Args` | `language` | ✓ | - |
| `Example` | `unknown` | ✓ | - |
| `task_name` | `str` | ✓ | - |
| `tags` | `list[str]` | ✓ | - |

### [New] [architecture] Changes in modular_qwen3_moe.py

- **File**: `venv\Lib\site-packages\transformers\models\qwen3_moe\modular_qwen3_moe.py`
- **Captured**: 4/28/2026, 12:52:41 PM
- **Category**: architecture
**Summary:** Modified modular_qwen3_moe.py: 206 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\transformers\models\qwen3_moe\modular_qwen3_moe.py` (+206 / -0)
**Schema: `Qwen3MoePreTrainedModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `_can_record_outputs` | `unknown` | ✓ | - |

**Schema: `Qwen3MoeModel`** (django/sqlalchemy)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `pass` | `unknown` | ✓ | - |

### [New] [architecture] Changes in model_card.py

- **File**: `venv\Lib\site-packages\sentence_transformers\sparse_encoder\model_card.py`
- **Captured**: 4/28/2026, 12:51:46 PM
- **Category**: architecture
**Summary:** Modified model_card.py: 155 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\sentence_transformers\sparse_encoder\model_card.py` (+155 / -0)
**Schema: `SparseEncoderModelCardCallback`** (pydantic)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `pass` | `unknown` | ✓ | - |

### [New] [architecture] Changes in heuristics.py

- **File**: `venv\Lib\site-packages\pip\_vendor\cachecontrol\heuristics.py`
- **Captured**: 4/28/2026, 12:50:45 PM
- **Category**: architecture
**Summary:** Modified heuristics.py: 158 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\pip\_vendor\cachecontrol\heuristics.py` (+158 / -0)
**Schema: `OneDayCache`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Cache` | `unknown` | ✓ | - |
| `future` | `unknown` | ✓ | - |

**Schema: `ExpiresAfter`** (python)

| Field | Type | Required | Attributes |
|-------|------|----------|------------|
| `Cache` | `unknown` | ✓ | - |-----|------------|
| `Cache` | `unknown` | ✓ | - |

## Features & Implementation

### [New] Balloons.JTmp0dzs.js

- **File**: `venv\Lib\site-packages\streamlit\static\static\js\Balloons.JTmp0dzs.js`
- **Captured**: 4/28/2026, 1:02:19 PM
- **Category**: feature
**Files Modified:**
  - `venv\Lib\site-packages\streamlit\static\static\js\Balloons.JTmp0dzs.js` (+1 / -0)
**API Endpoints** (`Balloons.JTmp0dzs.js`):

| Method | Route | Handler | Middleware |
|--------|-------|---------|------------|
| `URL(`../MEDIA/BALLOON-0.CZJ7AKWE.PNG`,IMPORT` | `../media/balloon-0.Czj7AKwE.png` | - | - |
| `URL(`../MEDIA/BALLOON-1.CNVFFRND.PNG`,IMPORT` | `../media/balloon-1.CNvFFrND.png` | - | - |
| `URL(`../MEDIA/BALLOON-2.DTVC6B1T.PNG`,IMPORT` | `../media/balloon-2.DTvC6B1t.png` | - | - |
| `URL(`../MEDIA/BALLOON-3.CGSK4TBL.PNG`,IMPORT` | `../media/balloon-3.CgSk4tbL.png` | - | - |
| `URL(`../MEDIA/BALLOON-4.MBTFRZXF.PNG`,IMPORT` | `../media/balloon-4.mbtFrzxf.png` | - | - |
| `URL(`../MEDIA/BALLOON-5.CSWKUFRA.PNG`,IMPORT` | `../media/balloon-5.CSwkUfRA.png` | - | - |

### [UI] NexusAgent

- **File**: `frontend\dist\index.html`
- **Captured**: 4/28/2026, 1:00:30 PM
- **Category**: feature
**Summary:** **Page:** NexusAgent
**Libraries:** `index-IVqHpmXj.js`
**Files Modified:**
  - `frontend\dist\index.html` (+29 / -0)

### [UI] Workflows-CHpVij2M

- **File**: `frontend\dist\assets\Workflows-CHpVij2M.css`
- **Captured**: 4/28/2026, 1:00:30 PM
- **Category**: feature
**Summary:** **CSS Variables:**

| Variable | Value |
|----------|-------|
| `--xy-edge-stroke-default` | `#b1b1b7` |
| `--xy-edge-stroke-width-default` | `1` |
| `--xy-edge-stroke-selected-default` | `#555` |
| `--xy-connectionline-stroke-default` | `#b1b1b7` |
| `--xy-connectionline-stroke-width-default` | `1` |
| `--xy-attribution-background-color-default` | `#ffffff80` |
| `--xy-minimap-background-color-default` | `#fff` |
| `--xy-minimap-mask-background-color-default` | `#f0f0f099` |
| `--xy-minimap-mask-stroke-color-default` | `transparent` |
| `--xy-minimap-mask-stroke-width-default` | `1` |
| `--xy-minimap-node-background-color-default` | `#e2e2e2` |
| `--xy-minimap-node-stroke-color-default` | `transparent` |
| `--xy-minimap-node-stroke-width-default` | `2` |
| `--xy-background-color-default` | `transparent` |
| `--xy-background-pattern-dots-color-default` | `#91919a` |

**Animations/Keyframes:** `dashdraw`

**Component classes:** `.react-flow`
**Files Modified:**
  - `frontend\dist\assets\Workflows-CHpVij2M.css` (+2 / -0)

### [feature] Changes in sw.js

- **File**: `frontend\dist\sw.js`
- **Captured**: 4/28/2026, 1:00:29 PM
- **Category**: feature
**Summary:** Modified sw.js: 37 lines added, 0 lines removed.
**Files Modified:**
  - `frontend\dist\sw.js` (+37 / -0)

### [UI] index

- **File**: `frontend\src\index.css`
- **Captured**: 4/28/2026, 12:59:15 PM
- **Category**: feature
**Summary:** **CSS Variables:**

| Variable | Value |
|----------|-------|
| `--color-bg` | `#0a0b10` |
| `--color-surface-1` | `#10131b` |
| `--color-surface-2` | `#161a25` |
| `--color-surface-3` | `#1d2230` |
| `--color-border` | `#252a38` |
| `--color-border-strong` | `#343a4c` |
| `--color-text` | `#e6e8ee` |
| `--color-text-muted` | `#9197a8` |
| `--color-text-dim` | `#5e6377` |
| `--color-accent` | `#10b981` |
| `--color-accent-hover` | `#14c08b` |
| `--color-accent-soft` | `rgba(16, 185, 129, 0.12)` |
| `--color-accent-ring` | `rgba(16, 185, 129, 0.35)` |
| `--color-ok` | `#10b981` |
| `--color-warn` | `#f59e0b` |

**Animations/Keyframes:** `fade-in`, `fade-up`, `scale-in`, `pulse-dot`, `shimmer`, `spin`, `voice-orb-breathe`

**Breakpoints:** `(prefers-reduced-motion: reduce)`, `(max-width: 768px)`, `(max-width: 480px)`

**Component classes:** `.sidebar`, `.sidebar-logo`, `.sidebar-logo-icon`, `.nav-section`, `.nav-item`, `.conv-section`, `.conv-label`, `.conv-item`, `.status-bar`, `.status-dot`
**Files Modified:**
  - `frontend\src\index.css` (+778 / -0)

### [New] [feature] Changes in __init__.py

- **File**: `venv\Lib\site-packages\setuptools\config\__init__.py`
- **Captured**: 4/28/2026, 12:57:08 PM
- **Category**: feature
**Summary:** Modified __init__.py: 44 lines added, 0 lines removed.
**Files Modified:**
  - `venv\Lib\site-packages\setuptools\config\__init__.py` (+44 / -0)

### [UI] NexusAgent — Setup

- **File**: `desktop\setup.html`
- **Captured**: 4/28/2026, 12:55:24 PM
- **Category**: