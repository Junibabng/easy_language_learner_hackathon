# PLAN

## 1. 목표
- 사용자가 자신의 LLM API 키를 직접 사용하여 언어를 학습할 수 있는 경량 웹 애플리케이션 개발
- MVP(Minimum Viable Product) 단계에서는 백엔드 API 기능의 완성도와 안정성을 최우선으로 함
- 철저한 BYOK(Bring Your Own Key) 정책을 통해 사용자 개인정보 및 자산 보호

## 2. 아키텍처 및 배포 전략
- **Frontend**: Next.js (TypeScript)
  - 배포 플랫폼: Vercel
  - 특징: 반응형 UI, 클라이언트 사이드 상태 관리
- **Backend**: FastAPI (Python)
  - 배포 플랫폼: Render 또는 Railway
  - 특징: 비동기 처리, 빠른 API 응답속도, 자동 API 문서화(Swagger)
- **환경 변수 구성 (Render/Railway)**:
  - `APP_ENV`: 애플리케이션 실행 환경 (production, development)
  - `CORS_ORIGIN`: 프론트엔드 도메인 허용을 위한 설정
  - `LOG_LEVEL`: 시스템 로그 출력 수준 (INFO, DEBUG, ERROR)

## 3. 구현 단계 (체크리스트)

### 3.1. 백엔드 개발 (FastAPI) [x]
- [x] 프로젝트 초기 구조 설정 및 필수 라이브러리(FastAPI, Pydantic 등) 설치
- [x] BYOK 정책 설계: 매 요청마다 헤더를 통해 API 키를 수신하는 구조 확립
- [x] 주요 API 엔드포인트 구현:
  - [x] `POST /v1/vocab/bulk`: 대량 단어 추가 및 학습 목록화
  - [x] `POST /v1/chat`: AI 튜터와의 실시간 대화 학습
  - [x] `POST /v1/quiz/generate`: 사용자 맞춤형 퀴즈 생성
  - [x] `POST /v1/quiz/submit`: 퀴즈 결과 제출 및 피드백 수신
  - [x] `GET /v1/session/{id}`: 현재 학습 세션의 상태 조회
- [x] API 유닛 테스트 및 통합 테스트 수행

### 3.2. 프론트엔드 및 배포 [ ]
- [ ] Next.js 프로젝트 스캐폴딩 및 Vercel 배포 설정
- [ ] UI 컴포넌트 개발: 챗 인터페이스, 퀴즈 카드, 단어 목록 뷰
- [ ] 백엔드 API 연동 로직 작성 및 에러 핸들링
- [ ] Render 또는 Railway 환경에 백엔드 서비스 배포 및 도메인 연결
- [ ] 프론트엔드-백엔드 간 CORS 및 보안 설정 최종 점검

## 4. 최소 검증
- BYOK 키를 본문/헤더로 전달해도 서버 DB/파일/로그에 저장 흔적이 남지 않는지 확인
- `POST /v1/quiz/generate` 호출 시 학습된 단어 데이터 기반으로 퀴즈가 생성되는지 검증
- 프론트엔드에서 백엔드로의 API 호출이 CORS 정책 위반 없이 정상 작동하는지 확인
- 배포된 환경에서 환경 변수(`APP_ENV`, `CORS_ORIGIN`)가 정상적으로 로드되는지 확인

## 5. 비범위 (Out of Scope)
- **BYOK 엄격 준수**: 서버 데이터베이스, 파일 시스템, 서버 로그, 브라우저 로컬 스토리지 및 쿠키 등 어떤 저장소에도 사용자 API 키를 저장하지 않음 (휘발성 처리)
- 사용자 계정 생성, 소셜 로그인 및 영구 프로필 관리 기능
- 영구적인 단어 저장 DB 구축 (모든 데이터는 세션 단위로 처리)
- 다국어 UI 지원 및 고도화된 그래픽 디자인 요소 적용
