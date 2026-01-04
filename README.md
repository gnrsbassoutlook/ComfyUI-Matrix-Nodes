# ComfyUI Matrix Nodes (Image Loader & Prompt Splitter)

[English] | [中文说明]

A powerful set of custom nodes designed for **Prompt-Driven** or **Excel/CSV-Driven** workflows. It supports dynamic batch loading (up to 10 channels), robust string parsing, and visual error reporting.

一套专为 **提示词驱动** 或 **Excel/表格驱动** 工作流设计的强大节点。支持 10 通道动态加载、强大的文本拆分以及可视化错误报错功能。

---

## ✨ Key Features / 核心功能

- **Max 10 Channels (十通道全开)**: All nodes support up to 10 simultaneous inputs/outputs. You can use any number from 1 to 10.
  所有节点支持 1-10 路输入输出。你可以任意使用 1 到 10 个插槽，未使用的插槽会自动休眠。

- **Visual Error Reporting (可视化报错)**: Instead of crashing your workflow, missing files generate a **Grey Image with Large Red Text** (e.g., "MISSING: A1").
  找不到图片时，不会导致工作流崩溃，而是生成一张**带有巨大红字警告的灰色图片**，方便快速排查错误。

- **Smart Fuzzy Matching (智能搜索)**: Input `"X1"` and it automatically finds `"X1.jpg"`, `"X1_Monkey.png"`, etc.
  输入 `"X1"` 即可自动匹配 `"X1.jpg"` 或 `"X1_猴子.png"` 等文件，无需输入全名。

- **Robust Text Splitter (万能拆分)**: Supports custom brackets (`[]`, `{}`, `【】`, `“”`) and separators (`|`, `,`, `-`).
  支持自定义中英文括号和各种分隔符，完美适配各种 Prompt 格式。

- **Zero-Value Handling (零值处理)**: Input `"0"`, `"None"`, or empty strings to generate pure White/Black placeholder images.
  输入 `"0"` 或 `"None"` 自动生成纯白或纯黑的占位图。

---

## 📦 Nodes Included / 包含节点

### 1. Matrix Image Loader (Direct String 10)
**The Ultimate Loader**. Accepts strings directly.
- **Inputs**: Strings (Filenames/Keywords).
- **Usage**: Connect your Prompt split results here. It finds the images or shows "MISSING" alerts.
- **中文**: **终极加载器**。直接接受字符串输入（文件名或关键词）。通常连接文本拆分器的输出，自动搜图或报错。

### 2. Matrix Prompt Splitter (10)
**The Parser**. Splits a long string into 10 separate outputs.
- **Inputs**: Long text (e.g., `Scene1 [A1 | B2 | C3]`).
- **Config**: Select Bracket Style (e.g., `[]`) and Separator (e.g., `|`).
- **中文**: **解析器**。将长文本根据你选择的括号和分隔符，拆分成 10 个独立的字符串。

### 3. Matrix Image Loader (Index 10)
**The Classic**. Slider-based control.
- **Inputs**: Prefix (e.g., "X") + Index Slider (Int).
- **中文**: **经典版**。通过“前缀+数字滑块”的方式组合文件名进行加载。

---

## 🛠 Installation / 安装方法

1. Navigate to your ComfyUI `custom_nodes` folder.
   进入 ComfyUI 的 `custom_nodes` 文件夹。
   
2. Clone this repository:
   运行 git 命令克隆本仓库：
   ```bash
   git clone https://github.com/YOUR_USERNAME/ComfyUI-Matrix-Nodes.git
   ```

3. Restart ComfyUI.
   重启 ComfyUI。

---

## 🚀 Usage Example / 使用示例

**Scenario**: You have a prompt: `Shot_01 [Background_A | Character_02 | 0 | 0 | 88]`
**场景**: 你的提示词是：`Shot_01 [Background_A | Character_02 | 0 | 0 | 88]`

1. **Splitter Node**:
   - Set **Bracket Style** to `[]`.
   - Set **Separator** to `|`.
   - Output: `Str_1="Background_A"`, `Str_2="Character_02"`, `Str_5="88"`.

2. **Loader Node**:
   - Connect `Str_1` -> `image1_input`.
   - Output 1: Loads `Background_A.jpg`.
   - Output 3: Generates a **White Placeholder** (because input is "0").
   - Output 5: Generates a **MISSING FILE** image (if "88" is not found).

---

## 📄 License

MIT License