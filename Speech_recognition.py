import speech_recognition as sr
import re
from gtts import gTTS
import os

def play_voice_prompt():
    prompt_text = "请报出场次科目二考试考生的编号"
    tts = gTTS(prompt_text, lang='zh')  # 使用中文语音
    tts.save("prompt.mp3")
    os.system("mpg321 prompt.mp3")  # 播放语音提示

# 初始化语音识别器
recognizer = sr.Recognizer()

play_voice_prompt()

# 使用麦克风作为输入源
with sr.Microphone() as source:
    print("Please say your exam number...")
    recognizer.adjust_for_ambient_noise(source)  # Adjust for ambient noise
    audio = recognizer.listen(source)

# 将音频转换为文本
print("Recognizing...")

try:
    # 使用 Google 语音识别 API 将语音转换为中文文本
    result = recognizer.recognize_google(audio, language="zh-CN", show_all=True)
    print("Recognized speech content:", result)
    
    # 选择最佳候选结果（有可能是数字）
    best_transcript = None
    for alternative in result['alternative']:
        if '1234567' in alternative['transcript']:  # 如果识别到数字，选这个结果
            best_transcript = alternative['transcript']
            break
        elif re.search(r'\d+', alternative['transcript']):  # 如果识别到数字，选这个结果
            best_transcript = alternative['transcript']
            break

    if best_transcript:
        print("Best transcript:", best_transcript)
        
        # 使用正则表达式提取文本中的所有数字
        numbers = re.findall(r'\d+', best_transcript)  # 提取文本中的所有数字（连续的数字）
        
        # 如果识别到的数字中有空格，拼接成一个完整的数字
        if numbers:
            exam_number = ''.join(numbers)  # 合并识别到的所有数字

            # 构造文本
            speech_text = f"欢迎{exam_number}号考生参加科目二考试"
            
            # 使用 gTTS 将文本转换为语音
            tts = gTTS(speech_text, lang='zh')  # 使用中文语音

            # 保存为 MP3 文件
            output_filename = "exam_welcome.mp3"
            tts.save(output_filename)

            # 播放生成的音频
            os.system(f"mpg321 {output_filename}")  # 或者使用 aplay

        else:
            print("No valid number recognized in the speech.")

    else:
        print("No valid transcript found.")

except sr.UnknownValueError:
    print("Sorry, I couldn't understand the speech")
except sr.RequestError:
    print("Unable to connect to the speech recognition service")
