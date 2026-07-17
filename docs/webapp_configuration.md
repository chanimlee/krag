# Streamlit 웹앱 설정

웹앱의 기본 OpenAI 모델은 `gpt-5.5`이다. `OPENAI_MODEL` 환경변수로 다른 모델을 지정할 수 있으며, `OPENAI_API_KEY`와 `OPENAI_MODEL`은 Streamlit Secrets에서도 읽을 수 있다. 같은 설정이 두 곳에 있으면 환경변수가 우선한다.

```powershell
$env:OPENAI_API_KEY="YOUR_API_KEY"
$env:OPENAI_MODEL="gpt-4.1-mini"
python -m streamlit run app.py
```

`OPENAI_MODEL`을 지정하지 않으면 `gpt-5.5`를 사용한다. 특정 계정에서 `gpt-5.5` 사용 권한이 없거나 해당 모델을 지원하지 않으면 `OPENAI_MODEL`을 계정에서 접근 가능한 다른 모델명으로 변경한다.

Streamlit Cloud에서는 `.streamlit/secrets.toml`에 다음과 같이 설정할 수 있다.

```toml
OPENAI_API_KEY = "YOUR_API_KEY"
OPENAI_MODEL = "gpt-4.1-mini"
```

샘플 결과 보기 모드는 API 키 없이 동작한다. 새 문항 생성 기능은 `OPENAI_API_KEY`가 설정된 경우에만 활성화된다.
