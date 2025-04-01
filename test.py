import pyaudio
import webrtcvad
import numpy as np
import adaptfilt as af

# 설정
CHUNK = 1024  # 한 번에 처리할 샘플 수
FORMAT = pyaudio.paFloat32  # 32비트 float 포맷
CHANNELS = 1  # 모노 채널
RATE = 44100  # webrtcvad 지원 샘플레이트

# PyAudio 초기화
p = pyaudio.PyAudio()
vad = webrtcvad.Vad(2)  # 감도 설정

# 스트림 열기
input_stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
output_stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True, frames_per_buffer=CHUNK)

# 적응형 필터 파라미터
M = 32  # 필터 길이
mu = 0.01  # 학습률 (step size)

# 스피커 출력 신호 (참조 신호) - 예시로 임의의 신호 사용
# 실제로는 재생 중인 오디오 데이터를 사용해야 함
reference_signal = np.zeros(CHUNK, dtype=np.float32)  # 초기화
# 예: 재생 중인 WAV 파일에서 데이터를 가져오거나, 직접 생성

print("소음 제거 시작... Ctrl+C로 종료")

try:
    while True:
        # 마이크에서 데이터 읽기
        input_data = np.frombuffer(input_stream.read(CHUNK), dtype=np.float32)

        # 적응형 필터 적용 (LMS 알고리즘)
        # input_data: 마이크 입력 (desired signal)
        # reference_signal: 스피커 출력 (reference signal)
        filtered_output, error, weights = af.lms(input_data, reference_signal, M, mu)

        # 필터링된 출력 재생 (선택 사항)
        output_stream.write(filtered_output.astype(np.float32).tobytes())

        # 참조 신호 업데이트 (실제 구현에서는 스피커 출력 데이터를 동기화)
        # 예: reference_signal = 현재 재생 중인 오디오 데이터
        #reference_signal = input_data  # 임시로 이전 입력 사용 (실제로는 스피커 신호로 대체)

except KeyboardInterrupt:
    print("종료 중...")

finally:
    # 스트림 정리
    input_stream.stop_stream()
    input_stream.close()
    output_stream.stop_stream()
    output_stream.close()
    p.terminate()