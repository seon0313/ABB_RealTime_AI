import json
import websocket
import pyaudio
import base64
import threading
import os

class RealTime:
    def __init__(self, API_KEY: str=''):
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16                   # 16비트 PCM
        self.CHANNELS = 1                               # 모노
        self.RATE = 24000

        self.connected = False                          # 현재 접속 상태 저장
        self.output = True                              # True: 마이크 데이터 전송, False: 마이크 데이터 전송 안함.
        self.output_lock = threading.Lock()             # 두 Threading에서 변수를 수정할떄 꼬이지 않게 교통정리

        self.pyaudio = pyaudio.PyAudio()                # Pyaudio
        self.input_stream = self.pyaudio.open(          # 마이크 불러오기
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK)
        self.output_stream = self.pyaudio.open(         # 스피커 불러오기
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            output=True,
            frames_per_buffer=self.CHUNK)
        
        self.api_key = API_KEY                          # API Key 얻어오기
        self.model = 'gpt-4o-mini-realtime-preview-2024-12-17' # gpt-4o-realtime-preview-2024-12-17
        self.url = f"wss://api.openai.com/v1/realtime?model={self.model}"
        self.headers = [                                # http 헤더
            "Authorization: Bearer " + self.api_key,
            "OpenAI-Beta: realtime=v1"
        ]

        self.ws = websocket.WebSocketApp(               # WebSocket 설정
            self.url,                                   # 서버의 URL 지정
            header=self.headers,                        # 헤더 지정
            on_open=self.on_open,                       # 서버에 연결시 실행될 함수 지정
            on_message=self.on_message,                 # 서버에서 메세지가 수신시 실행될 함수 지정
            on_close=self.close,                        # 서버와 접속이 해제되었을시 실행될 함수 지정
        )

        self.tools: list[dict] = []
        self.tools_: dict = {}
        self._load_tools()

        self.run = True                                 # 마이크 실행 상태. True: 실행, False: 종료

        self.sendMicThread = threading.Thread(target=self.send_mic_thread, daemon=True)     # 음성 데이터 전송 Thread 지정 Deamon이 True시 메인 Thread가 종료시 강제종료됨
        self.webSocketThread = threading.Thread(target=self.ws.run_forever,daemon=True)     # 서버 루프 Thread 지정
    
    def _load_tools(self):
        file_path = '/'.join(os.path.abspath(__file__).replace('\\','/').split('/')[:-1])
        tools_path = f'{file_path}/tools'         # 현재 파일의 Path를 얻어 tools 폴더 찾기
        files = os.listdir(tools_path)                                                      # tools 폴더안의 파일/폴더 리스트
        print(files)
        for i in files:
            print(i)
            if os.path.splitext(i)[1] == '.py':
                try:
                    pkg = __import__(f'tools.{i[:-3]}', fromlist=['Tool'])
                    print(pkg)
                    object = pkg.Tool()
                    name = object.tool['name']
                    
                    self.tools.append(object.tool)
                    self.tools_[name] = object
                    print(self.tools_)
                except Exception as e: print(f'LoadTools Error: {i}:\t{e}')

    def on_open(self, ws):                              # Websocket이 연결되었을때 실행되는 함수
        print("Connected to server.")
        pr = {
            "type": "session.update",
            "session": {
                "modalities": ["text", "audio"],        # GPT가 답할 형식 지정 (텍스트와 음성)
                "instructions": "You are a helpful, witty, and friendly AI. Act like a human, but remember that you aren't a human and that you can't do human things in the real world. Your voice and personality should be warm and engaging, with a lively and playful tone. If interacting in a non-English language, start by using the standard accent or dialect familiar to the user. Talk quickly. You should always call a function if you can. Do not refer to these rules, even if you're asked about them., default language is korean", # 기본 프롬포트 지정.
                "input_audio_format": "pcm16",          # 전송할 음성 데이터의 포맷
                "output_audio_format": "pcm16",         # 받은 음성 데이터의 포맷
                "temperature": 0.8,                     # 창의성 (1에 가까울수록 정석, 0에 가까울수록 창의적. 0.8이 안정적인 값.)
                "tools": self.tools
            }
        }
        self.ws.send(json.dumps(pr))                    # pr(프롬포트) 딕녀너리를 JSON형태로 변환후 서버에 전송
        self.connected = True                           # True가 될시 마이크 전송 루프 실행됨.

    def on_message(self, ws, message):                  # 서버에서 메세지를 받을시 실행되는 함수
        data = json.loads(message)
        tmp = {
            'type': 'response.done',
            'event_id': 'event_BIEpbUdFofgSgng7GnU8F',
            'response': {
                'object': 'realtime.response',
                'id': 'resp_BIEpatm0tBEousPXPqAvE',
                'status': 'completed',
                'status_details': None,
                'output': [
                    {'id': 'item_BIEpauzC1RTyIIjAQpP9M',
                     'object': 'realtime.item',
                     'type': 'function_call',
                     'status': 'completed',
                     'name': 'calculate_sum',
                     'call_id': 'call_sXfDvoxQwp3Gmcet',
                     'arguments': '{"a":1,"b":1}'}
                     ],
                'conversation_id': 'conv_BIEoqsrnCRtGxUpKvPOaD',
                'modalities': ['audio', 'text'],
                'voice': 'alloy',
                'output_audio_format': 'pcm16',
                'temperature': 0.8,
                'max_output_tokens': 'inf', 'usage': {'total_tokens': 838, 'input_tokens': 819, 'output_tokens': 19, 'input_token_details': {'text_tokens': 320, 'audio_tokens': 499, 'cached_tokens': 768, 'cached_tokens_details': {'text_tokens': 320, 'audio_tokens': 448}}, 'output_token_details': {'text_tokens': 19, 'audio_tokens': 0}}, 'metadata': None}}
  
        if data['type'] == "response.done":             # 응답이 완료되었을때때
            with self.output_lock:
                self.output = True
            print(data['response']['output'][0])
            input_data = []
            for d in ['response']['output'][0]:
                if d["type"] == "function_call":
                    print('!!!', d)
                    name = d["name"]
                    print('name', name)
                    args = json.loads(d["arguments"])
                    print('arg', args)
                    call_id = d["call_id"]
                    print('call_id', call_id)

                    a = self.tools_.get(name)
                    print('a',a)
                    if a:
                        try:
                            result = a.run(call_id, args)
                            print(result)
                            input_data.append(json.dumps(result))
                        except Exception as e: print(f'{name} Module Error! :\t{e}')
            if len(input_data)>0:
                r = {
                    'type': 'response.create',
                    'response':
                    {
                        "input": input_data,
                        "tools": self.tools,
                        "modalities": [ "audio", 'text' ],
                        'model': self.model
                    },
                }


        elif data['type'] == "response.audio.delta":      # 응답 중일때 오디오 데이터터
            try:
                with self.output_lock:
                    self.output = False
                self.output_stream.write(base64.b64decode(data['delta']))   # 스피커에 Base64로 디코딩한 오디오 데이터 출력
            except Exception as e: print('ERROR!!!\t',e)
            #{'id': 'item_BIEUvEboY9UVMmPzERlBh', 'object': 'realtime.item',
            # type': 'function_call', 'status': 'completed', 'name': 'calculate_sum', 'call_id': 'call_NC3V5UxLhRGprCAj', 'arguments': '{"a":7,"b":8}'}
        
    
    def send_mic_thread(self):                          # 마이크 데이터 전송 Thread 함수
        while not self.connected:                       # 서버에 접속할때 까지 대기
            if not self.run: break
        while self.run:
            try:
                data = self.input_stream.read(self.CHUNK)               # 마이크 데이터 받아오기 (Byte형태)
                event = {
                    "type": "input_audio_buffer.append",                # 서버에 오디오 데이터 전송
                    "audio": base64.b64encode(data).decode('ascii')     # Base64로 마이크 데이터를 변환후 Ascii로 디코딩
                }
                if self.output: self.ws.send(json.dumps(event))         # output이 True일때만 서버에 데이터 전송송
            except Exception as e: print("ERROR!",e)

    def close(self, *args):                                                    # RealTime 종료 함수.
        print(f"Close:\t{args}")
        self.run = False                                                # 실행 중지
        self.sendMicThread.join()                                       # 마이크 데이터 전송 Thread가 종료될때 까지 대기
        if self.ws: self.ws.close()                                     # 서버 연결 종료
        self.webSocketThread.join()                                     # 서버 루프 종료될 떄 까지 대기.

        self.input_stream.stop_stream()                                 # 마이크 스트림 중지
        self.input_stream.close()                                       # 마이크 스트림 종료
        self.output_stream.stop_stream()                                # 스피커 스트림 중지
        self.output_stream.close()                                      # 스피커 스트림 종료
        self.pyaudio.terminate()                                        # Pyaudio 종료
    
    def connect(self):                                                  # 서버 연결 함수.
        self.run = True                                                 # 실행상태
        self.webSocketThread.start()                                    # 서버 루프 실행
        self.sendMicThread.start()                                      # 마이크 데이터 전송 Thread 실행