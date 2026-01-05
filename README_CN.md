# ComfyUI Matrix Nodes

**[🇺🇸 English](README.md)**

一套专为 **提示词驱动 (Prompt-Driven)** 工作流设计的强大节点。支持 10 通道动态加载、强大的文本拆分、可视化错误报错，并内置了增强版的 Qwen-VL 编码节点。

---

## ✨ 核心功能

- **十通道全开 (Max 10 Channels)**: 矩阵类节点支持 1-10 路输入输出。未使用的插槽会自动休眠。
- **可视化报错 (Visual Error Reporting)**: 找不到图片时，不会导致工作流崩溃，而是生成一张**带有巨大红字警告的灰色图片**（例如 "MISSING: A1"），方便快速排查错误。
- **智能搜索 (Smart Fuzzy Matching)**: 输入 "X1" 即可自动匹配 "X1.jpg" 或 "X1_猴子.png" 等文件，无需输入全名。
- **万能拆分 (Robust Text Splitter)**: 支持自定义中英文括号（[], {}, 【】, “”）和各种分隔符（|, ,, -），完美适配各种 Prompt 格式。
- **Qwen-VL 集成**: 内置独立的 Qwen 文本编码节点，剥离了 API 依赖，纯本地运行。经过优化，支持 **5 张参考图** 输入，以保证模型最佳的注意力分配。

---

## 📦 包含节点

### 1. Matrix Image Loader (Direct String 10)
**终极加载器**。直接接受字符串输入（文件名或关键词）。
- **输入**: 字符串（文件名或关键词）。
- **用法**: 通常连接文本拆分器的输出，自动搜图或报错。

### 2. Matrix Prompt Splitter (10)
**解析器**。将长文本拆分为 10 个独立的输出字符串。
- **输入**: 长文本 (例如: Scene1 [A1 | B2 | C3])。
- **配置**: 选择括号样式 (例如 []) 和分隔符 (例如 |)。

### 3. Matrix Image Loader (Index 10)
**经典版**。通过“前缀+数字滑块”的方式控制。
- **输入**: 前缀字符串 (例如 "X") + 数字滑块 (整数)。

### 4. Qwen Text Encode (5 Images)
**魔改版 Qwen-VL 编码器**。
- **纯净版**: 移除了原版插件中不必要的 API 调用代码，仅保留核心编码功能，纯本地运行。
- **最佳实践**: 将输入限制为 **1-5 张图片**。根据官方模型特性和工程经验，控制在 5 张以内能有效避免注意力分散，提升指令遵循效果。

---

## 🛠 安装方法

1. 进入 ComfyUI 的 `custom_nodes` 文件夹。

2. 运行 git 命令克隆本仓库：

    git clone https://github.com/gnrsbassoutlook/ComfyUI-Matrix-Nodes.git

3. 重启 ComfyUI。

---

## 🚀 使用示例

**场景**: 你的提示词是：`Shot_01 [Background_A | Character_02 | 0 | 0 | 88]`

1. **拆分节点 (Splitter Node)**:
   - 设置 **Bracket Style** 为 `[]`。
   - 设置 **Separator** 为 `|`。
   - 输出: `Str_1="Background_A"`, `Str_2="Character_02"`, `Str_5="88"`。

2. **加载节点 (Loader Node)**:
   - 将 `Str_1` 连接到 `image1_input`。
   - 输出 1: 加载 `Background_A.jpg`。
   - 输出 3: 生成 **纯白占位图** (因为输入是 "0")。
   - 输出 5: 生成 **MISSING FILE 警告图** (如果找不到 "88" 这张图)。

3. **Qwen 编码节点**:
   - 将加载好的图片连接到 `Qwen Text Encode (5 Images)` 对应的插槽中，用于引导 Qwen-VL 模型生成。

---

## 📄 License

MIT License