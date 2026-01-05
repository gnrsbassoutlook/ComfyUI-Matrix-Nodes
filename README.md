# ComfyUI Matrix Nodes

**[🇨🇳 中文说明](README_CN.md)**

A powerful set of custom nodes designed for **Prompt-Driven** workflows. It supports dynamic batch loading (up to 10 channels), robust string parsing, visual error reporting, and includes a specialized Qwen-VL encoding node.

---

## ✨ Key Features

- **Max 10 Channels**: Matrix nodes support up to 10 simultaneous inputs/outputs. Unused slots automatically sleep.
- **Visual Error Reporting**: Instead of crashing your workflow, missing files generate a **Grey Image with Large Red Text** (e.g., "MISSING: A1"), making debugging instant.
- **Smart Fuzzy Matching**: Input "X1" and it automatically finds "X1.jpg", "X1_Monkey.png", etc. No need for full filenames.
- **Robust Text Splitter**: Supports custom brackets ([], {}, 【】, “”) and separators (|, ,, -). Perfect for complex prompt structures.
- **Qwen-VL Integration**: Includes a standalone, locally-run Text Encode node optimized for Qwen-VL, supporting up to **6 reference images**.

---

## 📦 Nodes Included

### 1. Matrix Image Loader (Direct String 10)
**The Ultimate Loader**. Accepts strings directly.
- **Inputs**: Strings (Filenames/Keywords).
- **Usage**: Connect your Prompt split results here. It finds the images or shows "MISSING" alerts.

### 2. Matrix Prompt Splitter (10)
**The Parser**. Splits a long string into 10 separate outputs.
- **Inputs**: Long text (e.g., Scene1 [A1 | B2 | C3]).
- **Config**: Select Bracket Style (e.g., []) and Separator (e.g., |).

### 3. Matrix Image Loader (Index 10)
**The Classic**. Slider-based control.
- **Inputs**: Prefix (e.g., "X") + Index Slider (Int).

### 4. Qwen Text Encode (6 Images)
**Modified Qwen-VL Encoder**.
- **Features**: Stripped of all API dependencies (runs purely locally within the ComfyUI environment).
- **Upgrade**: Expanded input slots from 3 to **6 images** to support complex multi-reference workflows.
- **Usage**: Encodes text and multiple images for Qwen-VL models.

---

## 🛠 Installation

1. Navigate to your ComfyUI `custom_nodes` folder.

2. Clone this repository:

    git clone https://github.com/gnrsbassoutlook/ComfyUI-Matrix-Nodes.git

3. Restart ComfyUI.

---

## 🚀 Usage Example

**Scenario**: You have a prompt: `Shot_01 [Background_A | Character_02 | 0 | 0 | 88]`

1. **Splitter Node**:
   - Set **Bracket Style** to `[]`.
   - Set **Separator** to `|`.
   - Output: `Str_1="Background_A"`, `Str_2="Character_02"`, `Str_5="88"`.

2. **Loader Node**:
   - Connect `Str_1` -> `image1_input`.
   - Output 1: Loads `Background_A.jpg`.
   - Output 3: Generates a **White Placeholder** (because input is "0").
   - Output 5: Generates a **MISSING FILE** image (if "88" is not found).

3. **Qwen Encode Node**:
   - Connect images from the Loader Node to the `Qwen Text Encode (6 Images)` slots to guide generation.

---

## 📄 License

MIT License