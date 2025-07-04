import openai
import base64
import os

# --- 配置 ---
# 请将 "YOUR_OPENAI_API_KEY" 替换为您的 OpenAI API 密钥
# 强烈建议使用环境变量来设置您的 API 密钥，以避免泄露。
# 例如: os.environ.get("OPENAI_API_KEY")
API_KEY = "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" 
# 您想要使用的模型
MODEL = "openai/gpt-4.1-mini"
# 您要识别的图片路径
IMAGE_PATH = "path/to/your/image.jpg"

# 初始化 OpenAI 客户端
# 如果您已经设置了 OPENAI_API_KEY 环境变量，则无需传递 api_key 参数
client = openai.OpenAI(api_key=API_KEY)

def encode_image_to_base64(image_path):
    """将图片文件编码为 Base64 字符串"""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except FileNotFoundError:
        print(f"错误：找不到图片文件 {image_path}")
        return None
    except Exception as e:
        print(f"读取或编码图片时发生错误: {e}")
        return None

def recognize_image_content(image_path, prompt="这张图片里有什么？请仅输出识别出的主要结果，不要输出任何其他东西。"):
    """
    :param image_path: 本地图片文件的路径。
    :param prompt: 您想对图片提出的问题。
    :return: 模型的回答，如果出错则返回 None。
    """
    print(f"正在识别图片: {image_path}")
    
    base64_image = encode_image_to_base64(image_path)
    if not base64_image:
        return None

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=300, # 您可以根据需要调整返回内容的最大长度
        )
        
        # 提取并返回模型的回答
        return response.choices[0].message.content
        
    except openai.APIConnectionError as e:
        print(f"无法连接到 OpenAI API: {e.__cause__}")
    except openai.RateLimitError as e:
        print(f"达到 OpenAI API 的速率限制: {e.response.text}")
    except openai.APIStatusError as e:
        print(f"OpenAI API 返回错误状态: status={e.status_code}, response={e.response}")
    except Exception as e:
        print(f"调用 API 时发生未知错误: {e}")
        
    return None

if __name__ == "__main__":
    if API_KEY == "YOUR_OPENAI_API_KEY":
        print("错误：请在代码中设置您的 OpenAI API 密钥 (API_KEY)。")
    elif not os.path.exists(IMAGE_PATH):
         print(f"错误：图片文件不存在，请检查路径 '{IMAGE_PATH}' 是否正确。")
    else:
        description = recognize_image_content(IMAGE_PATH)
        if description:
            print("\n--- 识别结果 ---")
            print(description) 