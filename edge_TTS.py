import os

project_root = os.getcwd()

os.environ["FUNASR_CACHE"] = os.path.join(project_root, "models", "cached_models")
os.environ["HF_HOME"] = os.path.join(project_root, "models", "hf_cache")
os.environ["MODELSCOPE_CACHE"] = os.path.join(project_root, "models", "modelscope_cache")
# 导入所需的库
import asyncio
import edge_tts
import pygame
import io
from pygame import mixer
import sys

# 尝试使用更快的JSON库
try:
    import ujson as json
    print("EdgeTTS模块使用ujson")
except ImportError:
    import json
    print("EdgeTTS模块使用标准json库")

# 定义支持的语音列表 - 将由 load_config() 动态填充
SUPPORTED_VOICES = []
CONFIG_LOADED = False

def load_config():
    """加载配置文件并填充SUPPORTED_VOICES"""
    global SUPPORTED_VOICES, CONFIG_LOADED
    if CONFIG_LOADED:
        return

    config_path = os.path.join(project_root, 'config.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        # 从配置的 tts_config.voices 加载语音
        tts_voices = config_data.get('tts_config', {}).get('voices', [])
        SUPPORTED_VOICES.clear()
        SUPPORTED_VOICES.extend(tts_voices)
        
        if not SUPPORTED_VOICES:
            print("警告：配置文件中未找到有效的TTS语音信息 (tts_config.voices 为空或不存在)。")
        else:
            print("EdgeTTS模块配置加载成功，语音列表已更新。")
        CONFIG_LOADED = True

    except FileNotFoundError:
        print(f"错误：配置文件 config.json 未找到于 {config_path} (EdgeTTS模块)")
        SUPPORTED_VOICES.clear() # 确保列表为空
    except json.JSONDecodeError:
        print(f"错误：解析配置文件 config.json 失败 (EdgeTTS模块)。请检查JSON格式。")
        SUPPORTED_VOICES.clear()
    except Exception as e:
        print(f"加载TTS配置时发生未知错误: {e}")
        SUPPORTED_VOICES.clear()

# 在模块加载时执行配置加载
load_config()

# # 定义支持的语音列表 (此部分将被移除，由load_config替代)
# # 结构: {"language_display": "用户界面语言名", "gender_display": "性别", "locale_display": "地区/方言", "voice_display": "语音名", "short_name": "edge-tts短名称"}
# SUPPORTED_VOICES = [
#     # ... (此处省略了所有硬编码的语音条目) ...
# ]

async def play_audio_from_memory(audio_data):
    """直接从内存播放音频数据 (假定mixer已初始化)"""
    if not mixer.get_init():
        print("错误: Pygame Mixer 未初始化。")
        return

    audio_io = io.BytesIO(audio_data)
    print("正在播放语音...")
    mixer.music.load(audio_io)
    mixer.music.play()

    while mixer.music.get_busy():
        await asyncio.sleep(0.1)
    mixer.music.unload()
    print("播放完成！")

async def text_to_speech(text, voice, rate=None, volume=None):
    """将文本转换为语音并直接播放（不保存文件）

    参数:
        text (str): 要转换的文本.
        voice (str): 使用的语音名称 (e.g., \'en-US-AriaNeural\').
        rate (str, optional): 语速调整 (e.g., \'+20%\', \'-10%\'). 默认为 None.
        volume (str, optional): 音量调整 (e.g., \'+15%\', \'-5%\'). 默认为 None.
    """
    log_message = f"正在使用音色 {voice}"
    if rate is not None:
        log_message += f", 语速: {rate}"
    if volume is not None:
        log_message += f", 音量: {volume}"
    log_message += " 生成语音..."
    print(log_message)

    try:
        tts_options = {}
        if rate is not None:
            tts_options['rate'] = rate
        if volume is not None:
            tts_options['volume'] = volume
        communicate = edge_tts.Communicate(text, voice, **tts_options)
        audio_data = bytes()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]

        if not audio_data:
            print("警告：未生成音频数据，可能是文本或语音选择有问题")
            return False

        print("语音生成完成，准备播放...")
        await play_audio_from_memory(audio_data)
        return True

    except edge_tts.exceptions.NoAudioReceived:
        print("错误：未收到音频数据。可能的原因：")
        print("1. 所选语音不支持输入的文本")
        print("2. 网络连接问题")
        print("3. 请尝试不同的语音或更简短的文本")
        return False
    except Exception as e:
        print(f"错误：生成语音时发生异常: {str(e)}")
        return False


async def main():
    """主函数，交互式运行TTS"""
    if not CONFIG_LOADED or not SUPPORTED_VOICES:
        print("错误：TTS 配置未能成功加载或语音列表为空，无法启动交互式演示。")
        print("请检查 config.json 文件是否存在且格式正确，并包含 tts_config.voices 列表。")
        return

    print("=== Edge TTS 交互式演示程序 (新流程) ===")

    try:
        mixer.init()  # 初始化 Pygame Mixer

        while True:
            # 1. 获取用户输入的文本
            text = input("请输入要转换为语音的文本 (输入\'退出\'结束程序): ")
            if text.lower() in ['退出', 'exit', 'quit']:
                print("程序已退出。")
                break

            # 2. 选择语种
            available_languages = sorted(list(set(v["language_display"] for v in SUPPORTED_VOICES)))
            print("\n可用的语种:")
            for i, lang_name in enumerate(available_languages, 1):
                print(f"{i}. {lang_name}")

            selected_language_display = None
            while True:
                try:
                    choice = int(input("\n请选择语种编号: "))
                    if 1 <= choice <= len(available_languages):
                        selected_language_display = available_languages[choice - 1]
                        break
                    else:
                        print("无效的选择，请重试。")
                except ValueError:
                    print("请输入数字。")
                except KeyboardInterrupt: print("\n程序已中断。"); sys.exit(0)


            # 3. 选择性别
            voices_in_lang = [v for v in SUPPORTED_VOICES if v["language_display"] == selected_language_display]
            available_genders = sorted(list(set(v["gender_display"] for v in voices_in_lang)))
            print(f"\n可用的性别 ({selected_language_display}):")
            for i, gender_name in enumerate(available_genders, 1):
                print(f"{i}. {gender_name}")
            
            selected_gender_display = None
            while True:
                try:
                    choice = int(input("\n请选择性别编号: "))
                    if 1 <= choice <= len(available_genders):
                        selected_gender_display = available_genders[choice - 1]
                        break
                    else:
                        print("无效的选择，请重试。")
                except ValueError:
                    print("请输入数字。")
                except KeyboardInterrupt: print("\n程序已中断。"); sys.exit(0)

            # 4. 选择音色
            voices_for_selection = [
                v for v in voices_in_lang if v["gender_display"] == selected_gender_display
            ]
            print(f"\n可用的音色 ({selected_language_display} - {selected_gender_display}):")
            for i, voice_info in enumerate(voices_for_selection, 1):
                # 组合显示名称：地区/方言 - 语音名
                display_name = f"{voice_info['locale_display']} - {voice_info['voice_display']}"
                print(f"{i}. {display_name}")

            selected_voice_short_name = None
            while True:
                try:
                    choice = int(input("\n请选择音色编号: "))
                    if 1 <= choice <= len(voices_for_selection):
                        selected_voice_short_name = voices_for_selection[choice - 1]["short_name"]
                        break
                    else:
                        print("无效的选择，请重试。")
                except ValueError:
                    print("请输入数字。")
                except KeyboardInterrupt: print("\n程序已中断。"); sys.exit(0)

            # 5. 执行文本到语音转换并播放
            if selected_voice_short_name:
                success = await text_to_speech(text, selected_voice_short_name)
                if success:
                    choice = input("\n是否继续? (y/n): ")
                    if choice.lower() not in ['y', 'yes', '是']:
                        print("程序已退出。")
                        break
                else:
                    print("TTS失败，请尝试其他选项。")
            else:
                print("未选择有效的音色。")

    except Exception as e:
        print(f"主程序发生错误: {e}")
    finally:
        if mixer.get_init():
            mixer.quit() # 关闭 Pygame Mixer

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n程序已被用户中断。")
    except Exception as e:
        print(f"程序启动时发生错误: {str(e)}")