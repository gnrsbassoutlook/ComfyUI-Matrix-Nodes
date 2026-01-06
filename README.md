# ComfyUI Matrix Nodes

**[🇨🇳 中文说明](README_CN.md)**

A powerful set of custom nodes designed for **Prompt-Driven** workflows. It supports dynamic batch loading (up to 10 channels), robust string parsing, smart text extraction, visual error reporting, and includes a specialized Qwen-VL encoding node.

---

## ✨ Key Features

- **Max 10 Channels**: Matrix nodes support up to 10 simultaneous inputs/outputs. **Unconnected slots are safely ignored** (no errors).
- **Smart ID Parsing**:
  - Input `"X1"` automatically matches `X1.jpg`, `X01.png`, or `X1-Description.webp`.
  - Input `"Y2a"` automatically matches `Y2a.jpg`, `Y02a_Rainy.png`.
- **Visual Error Reporting**: Missing files generate a **Grey Image with Large Red Text** (e.g., "MISSING: A1") instead of crashing the workflow.
- **Advanced Text Extraction**: Extract specific IDs (e.g., `003`, `X15a`) from narrative text with the new **Matrix Text Extractor**.
- **Chinese Tooltips**: Hover over parameters to see detailed explanations (in Chinese).
- **Qwen-VL Integration**: Includes a standalone, locally-run Text Encode node optimized for Qwen-VL (5 reference images).

---

## 📦 Nodes Included

### 1. Matrix Image Loader (Direct String 10)
**The Ultimate Loader**. Accepts strings directly.
- **Inputs**: Strings (Filenames, IDs like "X1", or Keywords).
- **Smart Logic**: Automatically normalizes IDs (e.g., `X1` == `X01`). Fallback to fuzzy matching if no ID is found.
- **Optional Inputs**: You can leave slots empty without errors.

### 2. Matrix Prompt Splitter (10)
**The Parser**. Splits a long string into 10 separate outputs.
- **Inputs**: Long text (e.g., `Scene1 [A1 | B2 | C3]`).
- **Config**: Select Bracket Style (e.g., `[]`, `【】`) and Separator (e.g., `|`, `,`).

### 3. Matrix Text Extractor (Smart ID)
**The Miner**. Extracts specific IDs and descriptions from a text block.
- **Auto Mode**: Automatically finds 3-5 character IDs (e.g., `X15a`, `003`).
- **Custom Mode**: Define exact rules for each character position (e.g., "Digit-Digit-Digit").
- **Features**: Select which match to extract (1st, 2nd...) and control the length of the remaining text.

### 4. Matrix Image Loader (Index 10)
**The Classic**. Slider-based control.
- **Inputs**: Prefix (e.g., "X") + Index Slider (Int).

### 5. Qwen Text Encode (5 Images)
**Modified Qwen-VL Encoder**.
- **Features**: Pure local run (no API required).
- **Optimization**: Supports **1-5 reference images** for optimal attention distribution.

---

## 🛠 Installation

1. Navigate to your ComfyUI `custom_nodes` folder.

2. Clone this repository:

    git clone https://github.com/gnrsbassoutlook/ComfyUI-Matrix-Nodes.git

3. Restart ComfyUI.

---

## 🚀 Usage Example

**Scenario**: You have a text: `"Shot_01: The hero (X1a) is wearing a raincoat."`

1. **Text Extractor**:
   - Input: `"Shot_01: The hero (X1a) is wearing a raincoat."`
   - Mode: `Auto`.
   - Output ID: `X1a`.
   - Output Remainder: `is wearing a raincoat.`

2. **Loader Node**:
   - Connect `ID` -> `image1_input`.
   - Result: Loads `X01a_Hero.jpg`.

3. **Qwen Encode Node**:
   - Connect the image and the remainder text to guide the generation.

---

## 📄 License

MIT License