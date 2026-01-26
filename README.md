# ComfyUI Matrix Nodes

**[🇨🇳 中文说明](README_CN.md)**

A powerful set of custom nodes designed for **Prompt-Driven** workflows. It supports dynamic batch loading, robust string parsing, smart text extraction, visual error reporting, local Qwen-VL encoding, and high-efficiency video synthesis.

---

## ✨ Key Features

- **Max 10 Channels**: Matrix nodes support up to 10 simultaneous inputs/outputs. **Unconnected slots are safely ignored**.
- **Smart ID Parsing**: Input `"X1"` automatically matches `X1.jpg`, `X01.png`, or `X1-Description.webp`.
- **String Slicer**: A powerful node to cut text strings using custom left/right delimiters.
- **Efficient Video Combine**: Direct FFmpeg pipe encoding (no intermediate image files) with audio mixing support.
- **Qwen-VL Integration**: Includes a standalone, locally-run Text Encode node optimized for Qwen-VL.
- **Visual Error Reporting**: Missing files generate a **Grey Image with Large Red Text** instead of crashing.

---

## 📦 Nodes Included

### 1. Matrix Image Loader (String 5 / 10) | 矩阵-字符加载器
**The Ultimate Loader**. Accepts strings directly.
- **Inputs**: Strings (Filenames, IDs like "X1", or Keywords).
- **Smart Logic**: Automatically normalizes IDs. Fallback to fuzzy matching if no ID is found.

### 2. Matrix Prompt Splitter (5 / 10) | 矩阵-文本拆分器
**The Parser**. Splits a long string into 5 or 10 separate outputs.
- **Config**: Select Bracket Style (e.g., `[]`, `【】`) and Separator.

### 3. Matrix ID Extractor | 矩阵-ID智能提取
**The Miner**. Extracts specific IDs (e.g., `003`, `X15a`) and descriptions from a text block.
- **Auto Mode**: Automatically finds 3-5 character IDs.
- **Custom Mode**: Define exact rules for each character position.

### 4. Matrix String Slicer | 矩阵-字符切割刀
**The Scalpel**. Cuts text between two custom delimiters.
- **Example**: Input `004-[Data]-View`, Left `-`, Right `]`.
- **Output**: Extracts `[Data` (Middle), `004-` (Left), `-View` (Right).

### 5. Matrix Loader (Index 5 / 10) | 矩阵-滑块加载器
**The Classic**. Slider-based control for file loading.

### 6. Matrix Qwen Encode (5 / 10) | Qwen-VL编码器
**Modified Qwen-VL Encoder**.
- **Features**: Pure local run (no API required).
- **Optimization**: Supports **1-10 reference images**. Smartly filters out empty/placeholder images.
- **Auto Shuffle**: Automatically moves the target "Align Latent" image to the first position for optimal model attention.

### 7. Matrix Video Combine | 矩阵-视频合成
**The Efficient Encoder**. Encodes images to video directly via FFmpeg pipes.
- **Clean**: No intermediate image files saved to disk.
- **Features**: Supports Audio mixing, MP4/WebP/GIF formats.
- **Preview**: Generates a temporary low-res WebP animation for quick preview (saves GPU).

---

## 🛠 Installation

1. Navigate to your ComfyUI custom_nodes folder.

2. Clone this repository:

    git clone https://github.com/gnrsbassoutlook/ComfyUI-Matrix-Nodes.git

3. Restart ComfyUI.

---

## 🚀 Usage Example (Video Combine)

**Scenario**: You have a sequence of images and an audio file.

1. **Matrix Video Combine**:
   - **Connect Images**: Connect your image sequence.
   - **Connect Audio**: (Optional) Connect audio output from Load Audio node.
   - **Format**: `video/h264-mp4`.
   - **Preview GIF**: `True` (See a quick animation in the node).

2. **Result**:
   - A high-quality MP4 saved in your output folder.
   - No junk files left behind.

---

## 📄 License

MIT License