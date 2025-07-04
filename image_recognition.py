import openai
import base64
import os
import cv2
import time

# --- 配置 ---
# 请将 "YOUR_OPENAI_API_KEY" 替换为您的 OpenAI API 密钥
# 强烈建议使用环境变量来设置您的 API 密钥，以避免泄露。
# 例如: os.environ.get("OPENAI_API_KEY")
API_KEY = "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" 
# 您想要使用的模型
MODEL = "openai/gpt-4.1-mini"
# API 地址, 如果您使用代理或第三方服务，请在此修改
BASE_URL = "https://openrouter.ai/api/v1"
# 图片保存的文件夹
IMGS_DIR = "imgs"

# 初始化 OpenAI 客户端
# 如果您已经设置了 OPENAI_API_KEY 环境变量，则无需传递 api_key 参数
client = openai.OpenAI(api_key=API_KEY, base_url=BASE_URL)

def capture_image_from_camera(save_dir):
    """
    调用摄像头拍照并保存图片。
    
    :param save_dir: 图片保存的目录。
    :return: 保存的图片路径，如果失败则返回 None。
    """
    # 确保保存目录存在
    if not os.path.exists(save_dir):
        print(f"创建目录: {save_dir}")
        os.makedirs(save_dir)
        
    # 0 代表系统默认的摄像头
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("错误：无法打开摄像头。请检查摄像头是否连接并可用。")
        return None
        
    print("摄像头已启动，3秒后拍照...")
    time.sleep(1)
    print("2...")
    time.sleep(1)
    print("1...")
    time.sleep(1)
    print("拍照！")

    # 读取一帧
    ret, frame = cap.read()
    
    if not ret:
        print("错误：无法从摄像头捕获图像。")
        cap.release()
        return None
        
    # 生成文件名
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    image_name = f"capture_{timestamp}.jpg"
    image_path = os.path.join(save_dir, image_name)
    
    # 保存图片
    cv2.imwrite(image_path, frame)
    print(f"图片已保存到: {image_path}")
    
    # 释放摄像头资源
    cap.release()
    cv2.destroyAllWindows()
    
    return image_path

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
    else:
        # 1. 拍照
        image_to_recognize = capture_image_from_camera(IMGS_DIR)
        
        # 2. 如果拍照成功，则进行识别
        if image_to_recognize:
            description = recognize_image_content(image_to_recognize)
            if description:
                print("\n--- 识别结果 ---")
                print(description) 