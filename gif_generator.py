import asyncio
import os
import aiohttp
from PIL import Image
from openai import AsyncOpenAI
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# ====================== 1. 初始化配置 ======================
# 初始化SiliconFlow异步客户端
client = AsyncOpenAI(
    api_key=os.getenv("SILICONFLOW_API_KEY"),
    base_url="https://api.siliconflow.cn/v1",
    timeout=30.0
)

# 临时图片保存目录
TEMP_IMG_DIR = "temp_images"
os.makedirs(TEMP_IMG_DIR, exist_ok=True)

# ====================== 2. 核心函数：生成单张图片 ======================
async def create_image(
    prompt: str,
    retries: int = 3,
    delay: float = 2.0,
    timeout: float = 30.0
):
    """
    异步生成单张图片（适配SiliconFlow的Qwen-Image模型）
    :param prompt: 图片生成提示词
    :param retries: 重试次数
    :param delay: 初始重试间隔（秒）
    :param timeout: 单次请求超时时间
    :return: 图片URL / None
    """
    backoff = delay
    for attempt in range(retries):
        try:
            response = await asyncio.wait_for(
                client.images.generate(
                    model="Qwen/Qwen-Image",
                    prompt=prompt,
                    size="1024x1024",
                    n=1
                ),
                timeout=timeout
            )
            return response.data[0].url

        except asyncio.TimeoutError:
            print(f"⚠️ 图片生成尝试 {attempt+1}/{retries} 超时：{prompt[:50]}...")
            if attempt == retries - 1:
                return None
            await asyncio.sleep(backoff)
            backoff *= 2

        except Exception as e:
            error_type = type(e).__name__
            print(f"⚠️ 图片生成尝试 {attempt+1}/{retries} 失败：{error_type} - {str(e)[:100]}")
            if attempt == retries - 1:
                return None
            await asyncio.sleep(backoff)
            backoff *= 2

# ====================== 3. 批量生成图片（带并发限制） ======================
async def generate_images_batch(prompts: list[str], max_concurrent: int = 2):
    """
    批量生成图片，限制并发数避免限流
    :param prompts: 提示词列表
    :param max_concurrent: 最大并发数
    :return: 有效图片URL列表
    """
    semaphore = asyncio.Semaphore(max_concurrent)

    async def bounded_create_image(prompt):
        async with semaphore:
            return await create_image(prompt)

    tasks = [bounded_create_image(prompt) for prompt in prompts]
    results = await asyncio.gather(*tasks)
    valid_urls = [url for url in results if url is not None]
    print(f"\n✅ 批量生成完成：成功 {len(valid_urls)}/{len(prompts)} 张图片")
    return valid_urls

# ====================== 4. 下载图片并生成GIF ======================
async def download_image(url: str, save_path: str):
    """异步下载图片"""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                with open(save_path, "wb") as f:
                    f.write(await resp.read())

async def assemble_gif(image_urls: list[str], output_path: str, duration: int = 500):
    """
    将图片URL列表组装为GIF
    :param image_urls: 图片URL列表
    :param output_path: GIF输出路径
    :param duration: 每帧间隔（毫秒）
    """
    # 下载所有图片
    image_paths = []
    for idx, url in enumerate(image_urls):
        save_path = os.path.join(TEMP_IMG_DIR, f"frame_{idx}.png")
        await download_image(url, save_path)
        image_paths.append(save_path)

    # 组装GIF
    images = [Image.open(path).convert("RGB") for path in image_paths]
    images[0].save(
        output_path,
        save_all=True,
        append_images=images[1:],
        duration=duration,
        loop=0
    )

    # 清理临时文件
    for path in image_paths:
        os.remove(path)

    print(f"\n🎬 GIF生成完成！保存路径：{output_path}")

# ====================== 5. 主函数：端到端生成GIF ======================
async def main(prompts: list[str], output_gif: str = "output.gif"):
    """
    主函数：从提示词生成GIF
    :param prompts: 每帧图片的提示词列表
    :param output_gif: 输出GIF文件名
    """
    # 1. 批量生成图片
    image_urls = await generate_images_batch(prompts)
    if not image_urls:
        print("❌ 无有效图片，无法生成GIF")
        return

    # 2. 组装GIF
    await assemble_gif(image_urls, output_gif)

# ====================== 6. 测试入口 ======================
if __name__ == "__main__":
    # 测试用提示词（5帧动画）
    test_prompts = [
        "一只可爱的橘猫趴在草地上，看到蝴蝶，卡通风格",
        "橘猫起身，准备追逐蝴蝶，尾巴竖起",
        "橘猫跳跃起来，爪子伸向蝴蝶",
        "蝴蝶飞开，橘猫扑空，身体悬在空中",
        "橘猫落地，有点失落但依然可爱"
    ]

    # 运行主函数
    asyncio.run(main(test_prompts, "cat_chase_butterfly.gif"))
