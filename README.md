# AI GIF 生成器（SiliconFlow + Qwen-Image）
基于 SiliconFlow 平台 Qwen-Image 文生图模型构建的异步 GIF 动画生成工具，支持从文本提示词批量生成图片并自动拼接为动态 GIF，适配国内网络环境，开箱即用。

## 🌟 核心特性
- **异步高效**：基于 `AsyncOpenAI` 实现非阻塞图片生成，支持并发控制，大幅提升批量生成效率
- **鲁棒容错**：指数退避重试策略 + 精细化异常捕获，应对网络波动、API 限流、超时等问题
- **简洁易用**：端到端自动化流程，仅需提供文本提示词即可生成完整 GIF
- **灵活配置**：支持自定义图片尺寸、GIF 帧间隔、并发数、重试次数等参数
- **环境兼容**：同时支持普通 Python 脚本和 Jupyter Notebook 运行环境
- **自动清理**：生成完成后自动删除临时图片文件，避免冗余存储

## 📋 环境准备
### 1. 依赖安装
```bash
pip install openai python-dotenv aiohttp pillow
```

### 2. API 密钥配置
1. 注册 [SiliconFlow 账号](https://siliconflow.cn/)，进入「API 密钥」页面创建密钥
2. 在项目根目录创建 `.env` 文件，添加以下内容：
```env
SILICONFLOW_API_KEY=你的SiliconFlow API密钥
```
> ⚠️ 重要：请勿将 API 密钥硬编码到代码中，避免泄露

### 3. 模型权限确认
确保账号已开通 `Qwen/Qwen-Image` 模型调用权限（部分模型需申请试用）

## 🚀 快速开始
### 方式1：直接运行示例（Python 脚本）
```bash
python gif_generator.py
```
运行后会生成 `cat_chase_butterfly.gif` 文件，展示「小猫追蝴蝶」的5帧动画效果。

### 方式2：自定义生成 GIF
```python
from gif_generator import main
import asyncio

# 定义每帧动画的提示词（建议3-8帧，保证动画连贯性）
custom_prompts = [
    "清晨，小兔子在草地上啃胡萝卜，卡通风格，明亮色彩",
    "小兔子听到声响，抬头张望，耳朵竖起",
    "小兔子放下胡萝卜，起身向森林方向跑去",
    "小兔子蹦跳着穿过花丛，尾巴一甩一甩",
    "小兔子躲到大树后，探出头来，好奇地看着前方"
]

# 生成GIF（输出路径可自定义）
asyncio.run(main(custom_prompts, output_gif="rabbit_animation.gif"))
```

### 方式3：Jupyter Notebook 运行
Notebook 环境需替换 `asyncio.run()` 为直接 `await` 调用：
```python
from gif_generator import main

# 定义提示词
notebook_prompts = ["第一帧提示词", "第二帧提示词", "第三帧提示词"]

# 生成GIF
await main(notebook_prompts, "notebook_demo.gif")
```

## 📖 核心功能说明
### 关键函数参数
| 函数名 | 功能描述 | 核心参数 | 默认值 |
|--------|----------|----------|--------|
| `create_image` | 生成单张图片 | `prompt`：图片提示词<br>`retries`：重试次数<br>`timeout`：超时时间 | 3次重试<br>30秒超时 |
| `generate_images_batch` | 批量生成图片 | `prompts`：提示词列表<br>`max_concurrent`：最大并发数 | 2（避免限流） |
| `assemble_gif` | 拼接生成GIF | `image_urls`：图片URL列表<br>`duration`：帧间隔（毫秒） | 500ms |
| `main` | 端到端生成 | `prompts`：提示词列表<br>`output_gif`：输出路径 | output.gif |

### 自定义参数示例
```python
# 生成慢动作GIF（帧间隔1000ms），并增加重试次数
asyncio.run(
    main(
        prompts=custom_prompts,
        output_gif="slow_motion.gif"
    )
)

# 修改图片生成参数（需修改create_image调用处）
response = await client.images.generate(
    model="Qwen/Qwen-Image",
    prompt=prompt,
    size="512x512",  # 更小尺寸，生成更快
    n=1
)
```

## ❌ 常见问题解决
| 问题现象 | 原因分析 | 解决方案 |
|----------|----------|----------|
| `AuthenticationError (401)` | API 密钥无效/过期/错误 | 1. 检查 `.env` 文件密钥是否正确<br>2. 确认密钥未被重置<br>3. 核对密钥所属平台（必须是SiliconFlow） |
| `RuntimeError: asyncio.run() cannot be called from a running event loop` | Jupyter 环境已有事件循环 | 替换 `asyncio.run(main())` 为 `await main()` |
| 图片生成超时 | 网络波动/模型生成慢 | 1. 增大 `timeout` 参数至60秒<br>2. 降低图片尺寸为512x512<br>3. 减少并发数（设为1） |
| GIF 生成失败 | 无有效图片URL | 1. 检查提示词是否合规<br>2. 确认模型调用返回正常<br>3. 增加重试次数 |
| 批量生成部分图片失败 | API 限流 | 1. 降低 `max_concurrent` 至1<br>2. 增大重试间隔（`delay` 参数） |

## ⚙️ 配置优化建议
1. **动画连贯性**：提示词保持统一风格（如卡通/写实）、相同主体、连续动作
2. **生成效率**：短提示词 + 512x512 尺寸生成速度更快
3. **稳定性**：并发数建议设为1-2，避免触发平台速率限制
4. **效果优化**：每帧提示词明确动作变化，避免画面跳变

## 📄 项目结构
```
gif-generator/
├── gif_generator.py  # 核心代码（包含所有生成逻辑）
├── .env              # API 密钥配置（需手动创建）
├── README.md         # 项目说明文档
└── output.gif        # 生成的GIF文件（运行后自动创建）
```

## 📝 注意事项
1. Qwen-Image 模型仅支持 `n=1`（每次生成1张图片），设置更大值会报错
2. 生成的临时图片会自动清理，无需手动删除
3. 建议单张图片提示词控制在50字以内，避免生成效果偏差
4. 若长时间无响应，检查网络是否能正常访问 SiliconFlow 服务器
