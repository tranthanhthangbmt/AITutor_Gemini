import asyncio
import base64
import streamlit as st
import edge_tts


def generate_audio_filename(text, voice="vi-VN-HoaiMyNeural"):
    """
    Tạo tên file âm thanh duy nhất từ đoạn text.
    """
    return f"audio_{hash(text + voice)}.mp3"


async def generate_audio_async(text, voice="vi-VN-HoaiMyNeural"):
    """
    Tạo file âm thanh từ văn bản sử dụng Microsoft Edge TTS.
    """
    filename = generate_audio_filename(text, voice)
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(filename)
    return filename


def play_audio(text, voice="vi-VN-HoaiMyNeural"):
    """
    Phát âm đoạn văn bản trong Streamlit.
    """
    if not text.strip():
        st.warning("⚠️ Không có nội dung để phát âm.")
        return

    filename = asyncio.run(generate_audio_async(text, voice))

    with open(filename, "rb") as f:
        audio_bytes = f.read()
        b64 = base64.b64encode(audio_bytes).decode()
        audio_html = f"""
            <audio autoplay controls>
                <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
                Trình duyệt của bạn không hỗ trợ audio.
            </audio>
        """
        st.markdown(audio_html, unsafe_allow_html=True)


# Gợi ý giọng đọc tiếng Việt:
# "vi-VN-HoaiMyNeural", "vi-VN-NamMinhNeural"
# Xem thêm danh sách voice tại https://learn.microsoft.com/en-us/azure/cognitive-services/speech-service/language-support
