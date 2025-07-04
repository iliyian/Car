import cv2
import numpy as np

# 生成0-9的模板数字（白底黑字）
for num in range(10):
    img = np.zeros((100, 100), dtype=np.uint8) + 255  # 白底
    cv2.putText(img, str(num), (30, 70), cv2.FONT_HERSHEY_SIMPLEX, 2, 0, 3)  # 黑字
    cv2.imwrite(f"digits/{num}.png", img)  # 保存到digits文件夹