# ComfyUI Matrix Nodes

**[🇨🇳 中文说明](README_CN.md)**

A powerful set of custom nodes designed for **Prompt-Driven** workflows. It supports dynamic batch loading (up to 10 channels), robust string parsing, smart text extraction, visual error reporting, and includes a specialized Qwen-VL encoding node.

---

## ✨ Key Features

- **Max 10 Channels**: Matrix nodes support up to 10 simultaneous inputs/outputs. **Unconnected slots are safely ignored**.
- **Smart ID Parsing**: Input `"X1"` automatically matches `X1.jpg`, `X01.png`, or `X1-Description.webp`.
- **String Slicer**: A new powerful node to cut text strings using custom left/right delimiters with precision.
- **Visual Error Reporting**: Missing files generate a **Grey Image with Large Red Text** instead of crashing.
- **Bilingual Display**: Node names are displayed as "English | Chinese" for better accessibility.
- **Qwen-VL Integration**: Includes a standalone, locally-run Text Encode node optimized for Qwen-VL.

---

## 📦 Nodes Included

### 1. Matrix Image Loader (String 10) | 矩阵-字符加载器
**The Ultimate Loader**. Accepts strings directly.
- **Inputs**: Strings (Filenames, IDs like "X1", or Keywords).
- **Smart Logic**: Automatically normalizes IDs. Fallback to fuzzy matching if no ID is found.

### 2. Matrix Prompt Splitter (10) | 矩阵-文本拆分器
**The Parser**. Splits a long string into 10 separate outputs.
- **Inputs**: Long text (e.g., `Scene1 [A1 | B2 | C3]`).
- **Config**: Select Bracket Style (e.g., `[]`, `【】`) and Separator.

### 3. Matrix Smart ID Extractor | 矩阵-ID智能提取
**The Miner**. Extracts specific IDs (e.g., `003`, `X15a`) and descriptions from a text block.
- **Auto Mode**: Automatically finds 3-5 character IDs.
- **Custom Mode**: Define exact rules for each character position.

### 4. Matrix String Slicer | 矩阵-字符切割刀
**The Scalpel**. Cuts text between two custom delimiters.
- **Example**: Input `004-[Data]-View`, Left `-`, Right `]`.
- **Output**: Extracts `[Data` (Middle), `004-` (Left), `-View` (Right).
- **Features**: Toggle to include/exclude delimiters; Select N-th match.

### 5. Matrix Image Loader (Index 10) | 矩阵-滑块加载器
**The Classic**. Slider-based control for file loading.

### 6. Qwen Text Encode (5 Images) | Qwen-VL编码器
**Modified Qwen-VL Encoder**.
- **Features**: Pure local run (no API required).
- **Optimization**: Supports **1-5 reference images** for optimal attention.

---

## 🛠 Installation

1. Navigate to your ComfyUI custom_nodes folder.

2. Clone this repository:

    git clone https://github.com/gnrsbassoutlook/ComfyUI-Matrix-Nodes.git

3. Restart ComfyUI.

---

## 🚀 Usage Example (String Slicer)

**Scenario**: You have a string: `"004-[X1b|X3|Y6|0|0]-View01"`

1. **Matrix String Slicer**:
   - **Text Input**: `"004-[X1b|X3|Y6|0|0]-View01"`
   - **Left Delimiter**: `-`
   - **Right Delimiter**: `]`
   - **Include Delimiters**: `False`

2. **Outputs**:
   - **Middle**: `[X1b|X3|Y6|0|0`
   - **Left**: `004-`
   - **Right**: `-View01`

---

## 📄 License

MIT License