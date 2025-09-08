"""
YouTube Transcript API 테스트 스크립트
자막 추출 문제 디버깅용
"""
from youtube_transcript_api import YouTubeTranscriptApi

def test_transcript(video_id):
    print(f"테스트 시작: {video_id}")
    
    # YouTubeTranscriptApi 인스턴스 생성
    api = YouTubeTranscriptApi()
    
    try:
        # 방법 1: 직접 fetch 시도 (한국어 우선)
        try:
            transcript = api.fetch(video_id, languages=['ko', 'ko-KR'])
            print(f"한국어 자막 발견!")
            print(f"자막 길이: {len(transcript)} 항목")
            if transcript:
                print(f"첫 3개 항목: {transcript[:3]}")
            return True
        except Exception as e:
            print(f"한국어 자막 실패: {e}")
            
        # 방법 2: 언어 지정 없이 시도
        try:
            transcript = api.fetch(video_id)
            print(f"자막 발견!")
            print(f"자막 길이: {len(transcript)} 항목")
            if transcript:
                print(f"첫 3개 항목: {transcript[:3]}")
            return True
        except Exception as e:
            print(f"기본 자막 실패: {e}")
            
        # 방법 3: list를 사용해서 사용 가능한 자막 확인
        try:
            transcript_list = api.list(video_id)
            print("\n사용 가능한 자막:")
            
            # 자막 목록 출력
            for transcript in transcript_list:
                print(f"  - {transcript}")
                # transcript 객체의 속성 확인
                attrs = [attr for attr in dir(transcript) if not attr.startswith('_')]
                print(f"    속성: {attrs}")
                
                # 속성 값 확인
                if hasattr(transcript, 'language'):
                    print(f"    언어: {transcript.language}")
                if hasattr(transcript, 'language_code'):
                    print(f"    언어 코드: {transcript.language_code}")
                if hasattr(transcript, 'is_generated'):
                    print(f"    자동 생성: {transcript.is_generated}")
                
            # 첫 번째 자막 가져오기 시도
            for transcript in transcript_list:
                try:
                    print(f"\n자막 가져오기 시도...")
                    # fetch 메서드가 있는지 확인
                    if hasattr(transcript, 'fetch'):
                        data = transcript.fetch()
                        print(f"fetch 성공! 타입: {type(data)}")
                    else:
                        # 다른 방법 시도
                        data = transcript
                        print(f"직접 사용! 타입: {type(data)}")
                        
                    if isinstance(data, list) and data:
                        print(f"자막 길이: {len(data)} 항목")
                        print(f"첫 3개 항목: {data[:3]}")
                        return True
                    elif data:
                        print(f"데이터 있음: {data}")
                        return True
                except Exception as e:
                    print(f"실패: {e}")
                    import traceback
                    traceback.print_exc()
                    continue
                    
        except Exception as e:
            print(f"list 메서드 실패: {e}")
            import traceback
            traceback.print_exc()
                    
    except Exception as e:
        print(f"전체 에러: {e}")
        print(f"에러 타입: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        
    return False

if __name__ == "__main__":
    # 테스트할 비디오 ID
    video_id = "Lg0rXSsESbA"
    test_transcript(video_id)