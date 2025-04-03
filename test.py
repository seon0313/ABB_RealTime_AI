import pyaudio
import numpy as np
import noisereduce as nr

CHUNK = 1024
FORMAT = pyaudio.paFloat32
CHANNELS = 1
RATE = 44100
THRESHOLD = 5

p = pyaudio.PyAudio()

def save_noise_sample():
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    print("Recording noise sample...")
    frames = [np.frombuffer(stream.read(CHUNK), dtype=np.float32) for _ in range(50)]
    stream.stop_stream()
    stream.close()
    audio.terminate()
    noise_sample = np.concatenate(frames)
    return noise_sample
    print("Noise sample saved.")


# 스트림 열기
input_stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
output_stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True, frames_per_buffer=CHUNK)
old = save_noise_sample()
try:
    while True:
        print(old)
        data = input_stream.read(CHUNK)
        #if type(old) == type(None): old = data
        audio_array = np.frombuffer(data, dtype=np.int32)
        
        # 노이즈 게이트 적용
        filtered_audio = np.where(np.abs(audio_array) > THRESHOLD, audio_array, 0)

        output_stream.write(filtered_audio)

        #old=data

except KeyboardInterrupt:
    print("종료 중...")

finally:
    # 스트림 정리
    input_stream.stop_stream()
    input_stream.close()
    output_stream.stop_stream()
    output_stream.close()
    p.terminate()