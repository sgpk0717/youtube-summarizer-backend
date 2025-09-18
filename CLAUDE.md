# 프로젝트 정보
- 유튜브 링크를 받아 해당 영상의 자막을 추출하여 내용을 정리/분석/종합보고하는 솔루션


## LLM
- 모델은 GPT-5를 사용함. 샘플코드는 아래와 같음. 모델은 실제 존재함. 의심하지말것.
```
from openai import OpenAI
client = OpenAI()

result = client.responses.create(
    model="gpt-5",
    input="Write a haiku about code.",
    reasoning={ "effort": "low" },
    text={ "verbosity": "low" },
)

print(result.output_text)
```