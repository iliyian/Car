import cv2
import numpy as np

# 加载模板数字图片（0-9）
templates = []
for i in range(10):
    template = cv2.imread(f'digits/{i}.png', 0)
    templates.append(template)

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 120, 255, cv2.THRESH_BINARY_INV)

    # 查找轮廓
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        if w > 20 and h > 30:  # 过滤小区域
            roi = thresh[y:y+h, x:x+w]

            # 与每个模板匹配
            max_score = -1
            best_match = -1
            for i, template in enumerate(templates):
                resized = cv2.resize(roi, (template.shape[1], template.shape[0]))
                res = cv2.matchTemplate(resized, template, cv2.TM_CCOEFF_NORMED)
                score = cv2.minMaxLoc(res)[1]
                if score > max_score:
                    max_score = score
                    best_match = i

            if max_score > 0.7:  # 置信度阈值
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(frame, str(best_match), (x, y-10),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    cv2.imshow('Digit Recognition', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()