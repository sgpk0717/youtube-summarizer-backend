import json
import requests

# API 호출해서 보고서 가져오기
response = requests.get("http://localhost:8000/api/test/reports")
data = response.json()

print(f"총 보고서 개수: {data['count']}")
print("-" * 50)

if data['reports']:
    latest = data['reports'][0]
    print("최신 보고서 필드 확인:")
    print(f"ID: {latest['id']}")
    print(f"Video ID: {latest['video_id']}")
    print(f"Title: {latest['title'][:50]}...")
    print(f"Channel: {latest['channel']}")
    print(f"Duration: {latest['duration']}")
    print(f"Language: {latest['language']}")
    print(f"Analysis Result: {'있음' if latest['analysis_result'] else '없음'}")
    print(f"Final Report: {'있음' if latest['final_report'] else '없음'}")
    print(f"Processing Time: {latest['processing_time']}")
    print(f"User Nickname: {latest['user_nickname']}")

    # 상세 확인
    print("\n필드별 상세 정보:")
    for key, value in latest.items():
        if value is None:
            print(f"  ❌ {key}: NULL")
        elif isinstance(value, (dict, list)) and len(str(value)) > 100:
            print(f"  ✅ {key}: {type(value).__name__} (데이터 있음)")
        else:
            print(f"  ✅ {key}: {value}")
else:
    print("저장된 보고서가 없습니다.")