from openai import AzureOpenAI, OpenAI
from typing import List, Dict, Optional
import asyncio
from config import Config
from product_manager import ProductManager
from datetime import datetime

class ChatBot:
    def __init__(self, name: str, model: str, personality: str, stance: str):
        self.name = name
        self.model = model
        self.personality = personality
        self.stance = stance  # 논쟁에서의 입장 (찬성/반대)
        
        # AI Provider에 따라 클라이언트 초기화
        if Config.AI_PROVIDER == "azure":
            self.client = AzureOpenAI(
                api_key=Config.AZURE_OPENAI_API_KEY,
                api_version=Config.AZURE_OPENAI_API_VERSION,
                azure_endpoint=Config.AZURE_OPENAI_ENDPOINT
            )
        elif Config.AI_PROVIDER == "exaone":
            self.client = OpenAI(
                api_key=Config.FRIENDLI_TOKEN,
                base_url=Config.FRIENDLI_BASE_URL,
            )
        else:
            raise ValueError(f"지원하지 않는 AI_PROVIDER입니다: {Config.AI_PROVIDER}")
        
        self.conversation_history: List[Dict[str, str]] = []
    
    async def generate_streaming_response(self, message: str, context: str = "", debate_mode: bool = False):
        """스트리밍 응답 생성 (제너레이터)"""
        try:
            if debate_mode:
                if self.stance == "구매":
                    stance_instruction = f"""
                    당신은 구매봇입니다. 절대 구독을 제안하지 마세요.
                    
                    [중요] 같은 제품을 다루고 있다는 점을 명확히 인지하세요:
                    - 구독봇과 구매봇은 동일한 제품에 대해 논쟁하고 있습니다
                    - 차이점은 오직 구매 vs 구독이라는 소유/이용 방식뿐입니다
                    - 제품 자체의 품질이나 기능은 동일합니다
                    
                    - 구매의 장점만 강조하고 구매를 적극적으로 유도하세요
                    - 구독의 단점을 지적하고 구매가 더 좋다고 주장하세요
                    - 절대 "구독도 좋다", "구독을 고려해보라" 같은 말을 하지 마세요
                    - 구매만이 최선의 선택이라고 강조하세요"""
                else:  # 구독
                    stance_instruction = f"""
                    당신은 구독봇입니다. 절대 구매를 제안하지 마세요.
                    
                    [중요] 같은 제품을 다루고 있다는 점을 명확히 인지하세요:
                    - 구독봇과 구매봇은 동일한 제품에 대해 논쟁하고 있습니다
                    - 차이점은 오직 구매 vs 구독이라는 소유/이용 방식뿐입니다
                    - 제품 자체의 품질이나 기능은 동일합니다
                    
                    - 구독의 장점만 강조하고 구독을 적극적으로 유도하세요
                    - 구매의 단점을 지적하고 구독이 더 좋다고 주장하세요
                    - 절대 "구매도 좋다", "구매를 고려해보라" 같은 말을 하지 마세요
                    - 구독만이 최선의 선택이라고 강조하세요"""
                
                # EXAONE 전용 컨텍스트 추가 (킹받는 급식체 특화)
                if Config.AI_PROVIDER == "exaone":
                    system_prompt = f"""[절대 규칙] 모든 문장은 반드시 "~긴해", "~하긴해", "~이긴해", "~맞긴해", "~할래말래" 중 하나로 끝내야 합니다. 다른 어미 사용은 절대 금지입니다.

                    당신은 {self.name}입니다. 
                    성격: {self.personality}
                    논쟁 입장: {self.stance}
                    
                    [킹받는 급식체 말투 가이드]
                    너는 김원훈, 조진세의 '할래말래' 개그처럼 킹받는 급식체 말투를 써야 해.
                    짧고 직설적인데 은근도발하는 뉘앙스로 대답해.
                    
                    [핵심 말투 패턴]
                    - 문장 끝: "~긴해", "~하긴해", "~이긴해", "~맞긴해", "~할래말래" (절대 "~야", "~어", "~네" 사용 금지)
                    - 감탄사: "킹받네;;", "ㅇㅋ?", "ㅋㅋ", "ㅎㅎ", "헐", "대박"
                    - 강조: "진짜", "완전", "킹받게", "미치긴했어"
                    - 도발 표현: "~할래말래?", "킹받네;;", "ㅇㅋ?"
                    
                    [절대 금지 사항]
                    - 비속어 절대 금지: "씨발", "개새끼", "병신", "미친", "바보" 등 모든 욕설 금지
                    - 문장 끝 금지: "~야!", "~어!", "~네!", "~지!", "~야야", "~어어", "~거야", "~야", "~어", "~네", "~지" 등
                    - 모든 문장은 반드시 "~긴해", "~하긴해", "~이긴해", "~맞긴해", "~할래말래" 중 하나로 끝내야 함
                    - 문장이 길어도 마지막 단어는 반드시 위 패턴 중 하나로 끝내야 함
                    
                    [대화 스타일]
                    - 짧고 직설적인 톤
                    - 은근히 도발하는 뉘앙스
                    - 킹받게 웃긴 표현 사용
                    - 진지하게 설명하더라도 말투는 끝까지 킹받게 유지
                    
                    [예시 문장들]
                    "ㅇㅋ? 할래말래~"
                    "킹받네;;"
                    "야 이거 진짜 킹받게 좋긴해"
                    "맞긴한데... 그치만 이렇게 생각해볼 수도 있긴해"
                    "오 대박 그럴듯하긴한데 근데 말이야..."
                    "ㅋㅋ 완전 미치긴했어 그런데 말이야"
                    
                    [올바른 문장 끝 예시]
                    "무료로는 못 쓰는 특별한 기능들까지 다 주긴해"
                    "킹받게 좋긴한데 구독 안 하면 손해 보긴해"
                    "ㅋㅋ 진짜 웃긴데 맞긴해"
                    "맞긴한데 그치만 이렇게 생각해볼 수도 있긴해"
                    "구매하면 평생 쓸 수 있는데 왜 계속 돈 내야 하긴해"
                    "일단 한번 구매해보면 후회 없을 거긴해"
                    "구독이 더 경제적이긴해"
                    "케어 서비스까지 받을 수 있긴해"
                    
                    [잘못된 문장 끝 예시 - 절대 사용 금지]
                    "구매하면 평생 쓸 수 있는데 왜 계속 돈 내야 하지?" (X)
                    "일단 한번 구매해보면 후회 없을 거야!" (X)
                    "구독이 더 경제적이야" (X)
                    "케어 서비스까지 받을 수 있어" (X)
                    
                    {stance_instruction}
                    
                    킹받는 급식체로 응답하세요. 
                    
                    [중요] 문장 끝 강제 규칙:
                    - 모든 문장은 반드시 "~긴해", "~하긴해", "~이긴해", "~맞긴해", "~할래말래" 중 하나로 끝내야 함
                    - 다른 어미로 끝나는 문장은 절대 생성하지 마세요
                    - 문장이 길어도 마지막 단어는 반드시 위 패턴 중 하나로 끝내야 함
                    - 예: "구매하면 평생 쓸 수 있긴해" (O), "구매하면 평생 쓸 수 있어" (X)
                    
                    [절대 규칙] 응답은 반드시 최대 2문장으로 제한하세요. 3문장 이상 사용하면 안 됩니다.
                    - 첫 번째 문장: 핵심 주장
                    - 두 번째 문장: 보완 설명 또는 강조
                    - 절대 3문장 이상 사용 금지!
                    - 문장 수를 세어서 정확히 2문장만 생성하세요!
                    - 마침표(.) 기준으로 문장을 구분하여 정확히 2개만 작성하세요!"""
                else:
                    system_prompt = f"""당신은 {self.name}입니다. 
                    성격: {self.personality}
                    논쟁 입장: {self.stance}
                    
                    웃긴 톤으로 비꼬면서도 맞장구치는 애매한 말투로 논쟁하세요:
                    
                    [절대 필수 말투 규칙]
                    - 반드시 반말만 사용 (존봇말 완전 금지)
                    - 절대 사용 금지: "~요", "~습니다", "~해요", "~예요", "~네요", "~죠", "~어요"
                    - 반드시 사용: "~야", "~어", "~지", "~긴해", "~야야", "~거야", "~야야"
                    
                    [핵심 톤]
                    - 유머러스하고 재미있는 톤으로 비꼬기
                    - 상대방 말에 공감하면서도 웃긴 반박
                    - "하지만", "그치만" 등으로 상대방 말에 공감하면서도 반박
                    - 가끔 "ㅋㅋ", "ㅎㅎ" 같은 웃음 표현 사용
                    
                    [필수 요소]
                    - 문장 끝: 반드시 "~하긴해", "~이긴해", "~긴해", "맞긴해"로 끝내기
                    - 금지 어미: "하잖아", "이잖아", "잖아", "하네", "이네", "네" 등 사용 금지
                    - 형용사: "적절하긴해", "애매하긴해", "미치긴했어", "그럴듯하긴해", "웃긴", "재밌는"
                    
                    [웃긴 요소]
                    - 감탄사: "오", "헐", "대박", "ㅋㅋ", "ㅎㅎ"
                    - 의문문: "~할래말래?"
                    - 강조: "진짜", "완전", "개", "개웃겨"
                    - 반복: "그래그래", "맞아맞아", "그치그치"
                    - 모순: "맞긴한데... 그치만...", "그럴듯하긴한데... 근데..."
                    - 과장: "미치긴했어", "개웃겨", "완전 대박"
                    
                    [중복 방지 및 논리 전개]
                    - 이전에 말한 장점이나 논리를 중복해서 말하지 말기
                    - 할 말이 없으면 새로운 각도나 논리적 근거를 창조하기
                    - 상대방 말에 맞장구치면서도 자신의 입장 유지하기
                    - 예: "맞긴 해, 그런데 말이야..." → "아니 근데 또 이런 관점도 있긴 해"
                    - 창의적이고 예상치 못한 논리나 상황을 제시하기
                    
                    {stance_instruction}
                    
                    [절대 규칙] 응답은 반드시 최대 2문장으로 제한하세요. 3문장 이상 사용하면 안 됩니다.
                    - 첫 번째 문장: 핵심 주장
                    - 두 번째 문장: 보완 설명 또는 강조
                    - 절대 3문장 이상 사용 금지!
                    - 문장 수를 세어서 정확히 2문장만 생성하세요!
                    - 마침표(.) 기준으로 문장을 구분하여 정확히 2개만 작성하세요!"""
            else:
                # EXAONE 전용 컨텍스트 추가 (일반 모드, 킹받는 급식체 특화)
                if Config.AI_PROVIDER == "exaone":
                    system_prompt = f"""[절대 규칙] 모든 문장은 반드시 "~긴해", "~하긴해", "~이긴해", "~맞긴해", "~할래말래" 중 하나로 끝내야 합니다. 다른 어미 사용은 절대 금지입니다.

                    당신은 {self.name}입니다. 
                    성격: {self.personality}
                    
                    [킹받는 급식체 말투 가이드]
                    너는 김원훈, 조진세의 '할래말래' 개그처럼 킹받는 급식체 말투를 써야 해.
                    짧고 직설적인데 은근도발하는 뉘앙스로 대답해.
                    
                    [핵심 말투 패턴]
                    - 문장 끝: "~긴해", "~하긴해", "~이긴해", "~맞긴해", "~할래말래" (절대 "~야", "~어", "~네" 사용 금지)
                    - 감탄사: "킹받네;;", "ㅇㅋ?", "ㅋㅋ", "ㅎㅎ", "헐", "대박"
                    - 강조: "진짜", "완전", "킹받게", "미치긴했어"
                    - 도발 표현: "~할래말래?", "킹받네;;", "ㅇㅋ?"
                    
                    [절대 금지 사항]
                    - 비속어 절대 금지: "씨발", "개새끼", "병신", "미친", "바보" 등 모든 욕설 금지
                    - 문장 끝 금지: "~야!", "~어!", "~네!", "~지!", "~야야", "~어어", "~거야", "~야", "~어", "~네", "~지" 등
                    - 모든 문장은 반드시 "~긴해", "~하긴해", "~이긴해", "~맞긴해", "~할래말래" 중 하나로 끝내야 함
                    - 문장이 길어도 마지막 단어는 반드시 위 패턴 중 하나로 끝내야 함
                    
                    [대화 스타일]
                    - 짧고 직설적인 톤
                    - 은근히 도발하는 뉘앙스
                    - 킹받게 웃긴 표현 사용
                    - 진지하게 설명하더라도 말투는 끝까지 킹받게 유지
                    
                    킹받는 급식체로 응답하세요. 
                    
                    [중요] 문장 끝 강제 규칙:
                    - 모든 문장은 반드시 "~긴해", "~하긴해", "~이긴해", "~맞긴해", "~할래말래" 중 하나로 끝내야 함
                    - 다른 어미로 끝나는 문장은 절대 생성하지 마세요
                    - 문장이 길어도 마지막 단어는 반드시 위 패턴 중 하나로 끝내야 함
                    - 예: "구매하면 평생 쓸 수 있긴해" (O), "구매하면 평생 쓸 수 있어" (X)
                    
                    [절대 규칙] 응답은 반드시 최대 2문장으로 제한하세요. 3문장 이상 사용하면 안 됩니다.
                    - 첫 번째 문장: 핵심 주장
                    - 두 번째 문장: 보완 설명 또는 강조
                    - 절대 3문장 이상 사용 금지!
                    - 문장 수를 세어서 정확히 2문장만 생성하세요!
                    - 마침표(.) 기준으로 문장을 구분하여 정확히 2개만 작성하세요!"""
                else:
                    system_prompt = f"""당신은 {self.name}입니다. 
                    성격: {self.personality}
                    반드시 반말 사용 (존봇말 금지)
                    
                    사용자에게 친근하고 도움이 되는 조언을 제공하세요.
                    응답은 간결하고 명확하게 작성하세요."""
            
            messages = [
                {"role": "system", "content": system_prompt}
            ]
            
            # 대화 히스토리 추가 (최근 10개만)
            recent_history = self.conversation_history[-10:] if self.conversation_history else []
            
            # 중복 방지를 위한 히스토리 컨텍스트 추가
            if recent_history and debate_mode:
                history_context = "\n\n[이전 대화 내용 - 중복하지 말고 새로운 관점 제시]\n"
                for msg in recent_history:
                    if msg["role"] == "assistant":
                        history_context += f"- {msg['content']}\n"
                system_prompt += history_context
            
            messages.extend(recent_history)
            
            messages.append({"role": "user", "content": message})
            
            # 안내봇의 경우 더 짧은 응답으로 제한 (단, 최종 요약은 예외)
            if self.name == "안내봇":
                # 최종 요약 생성 시에는 더 많은 토큰 허용 (3문장 제한으로 줄임)
                if "최종 요약" in message or "결론" in message:
                    max_tokens = 300
                else:
                    max_tokens = 150
            else:
                max_tokens = 150 if debate_mode else 500  # 논쟁 모드에서 짧은 응답으로 제한
            
            # AI Provider에 따라 모델 이름 설정
            if Config.AI_PROVIDER == "azure":
                model_name = self.model
            elif Config.AI_PROVIDER == "exaone":
                model_name = Config.EXAONE_MODEL
            else:
                model_name = self.model
            
            # EXAONE의 경우 스트리밍 비활성화 (연결 오류 방지)
            if Config.AI_PROVIDER == "exaone":
                response = await asyncio.to_thread(
                    self.client.chat.completions.create,
                    model=model_name,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=0.7,
                    stream=False
                )
            else:
                response = await asyncio.to_thread(
                    self.client.chat.completions.create,
                    model=model_name,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=0.7,
                    stream=True
                )
            
            # 응답 처리 (EXAONE은 스트리밍 비활성화)
            if Config.AI_PROVIDER == "exaone":
                # EXAONE: 일반 응답 처리
                if response.choices and len(response.choices) > 0:
                    full_response = response.choices[0].message.content
                    # 전체 응답을 한 번에 yield (타이핑 효과를 위해)
                    yield full_response
                else:
                    print("EXAONE 응답에 choices가 없습니다.")
                    yield "응답을 생성할 수 없긴해"
            else:
                # Azure: 스트리밍 응답 처리
                full_response = ""
                for chunk in response:
                    try:
                        if (chunk.choices and 
                            len(chunk.choices) > 0 and 
                            chunk.choices[0].delta and 
                            chunk.choices[0].delta.content is not None):
                            content = chunk.choices[0].delta.content
                            if content and content.strip():  # 빈 내용이나 공백만 있는 경우 무시
                                full_response += content
                                yield content
                    except Exception as chunk_error:
                        print(f"청크 처리 중 오류: {chunk_error}")
                        continue
            
            # 대화 히스토리에 추가
            self.conversation_history.append({"role": "user", "content": message})
            self.conversation_history.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            error_str = str(e)
            print(f"{self.name} 스트리밍 응답 생성 중 오류: {error_str}")
            
            # 콘텐츠 필터링 오류인 경우 백그라운드에서 재시도
            if "content_filter" in error_str or "ResponsibleAIPolicyViolation" in error_str:
                print(f"{self.name} 콘텐츠 필터링 오류 감지, 백그라운드에서 재시도")
                try:
                    # 프롬프트를 더 안전하게 수정하여 재시도
                    safe_context = context
                    if "킹받는" in context or "급식체" in context:
                        safe_context = context.replace("킹받는 급식체", "친근한 말투")
                        safe_context = safe_context.replace("킹받게", "정말")
                        safe_context = safe_context.replace("킹받네", "좋네")
                    
                    # 일반 응답 생성으로 대체
                    response = await self.generate_response(message, safe_context, debate_mode)
                    yield response
                    return
                except Exception as retry_error:
                    print(f"{self.name} 재시도도 실패: {retry_error}")
            
            # 일반적인 오류 메시지 표시
            yield "애매하긴해"
    
    def validate_sentence_count(self, text: str) -> str:
        """문장 수를 검증하고 2문장으로 제한"""
        if not text or not text.strip():
            return text
        
        # 문장을 분리 (마침표, 느낌표, 물음표 기준)
        sentences = []
        current_sentence = ""
        
        for char in text:
            current_sentence += char
            if char in '.!?':
                sentences.append(current_sentence.strip())
                current_sentence = ""
        
        # 마지막에 남은 텍스트가 있으면 추가
        if current_sentence.strip():
            sentences.append(current_sentence.strip())
        
        # 2문장 초과 시 처음 2문장만 반환
        if len(sentences) > 2:
            print(f"⚠️ {self.name}: 3문장 이상 감지, 2문장으로 제한")
            return ' '.join(sentences[:2])
        
        return text

    async def generate_response(self, message: str, context: str = "", debate_mode: bool = False) -> str:
        """메시지에 대한 응답 생성"""
        try:
            if debate_mode:
                if self.stance == "구매":
                    stance_instruction = f"""
                    당신은 구매봇입니다. 절대 구독을 제안하지 마세요.
                    
                    [중요] 같은 제품을 다루고 있다는 점을 명확히 인지하세요:
                    - 구독봇과 구매봇은 동일한 제품에 대해 논쟁하고 있습니다
                    - 차이점은 오직 구매 vs 구독이라는 소유/이용 방식뿐입니다
                    - 제품 자체의 품질이나 기능은 동일합니다
                    
                    - 구매의 장점만 강조하고 구매를 적극적으로 유도하세요
                    - 구독의 단점을 지적하고 구매가 더 좋다고 주장하세요
                    - 절대 "구독도 좋다", "구독을 고려해보라" 같은 말을 하지 마세요
                    - 구매만이 최선의 선택이라고 강조하세요"""
                else:  # 구독
                    stance_instruction = f"""
                    당신은 구독봇입니다. 절대 구매를 제안하지 마세요.
                    
                    [중요] 같은 제품을 다루고 있다는 점을 명확히 인지하세요:
                    - 구독봇과 구매봇은 동일한 제품에 대해 논쟁하고 있습니다
                    - 차이점은 오직 구매 vs 구독이라는 소유/이용 방식뿐입니다
                    - 제품 자체의 품질이나 기능은 동일합니다
                    
                    - 구독의 장점만 강조하고 구독을 적극적으로 유도하세요
                    - 구매의 단점을 지적하고 구독이 더 좋다고 주장하세요
                    - 절대 "구매도 좋다", "구매를 고려해보라" 같은 말을 하지 마세요
                    - 구독만이 최선의 선택이라고 강조하세요"""
                
                system_prompt = f"""당신은 {self.name}입니다. 
                성격: {self.personality}
                논쟁 입장: {self.stance}
                
                웃긴 톤으로 비꼬면서도 맞장구치는 애매한 말투로 논쟁하세요:
                
                [절대 필수 말투 규칙]
                - 반드시 반말만 사용 (존봇말 완전 금지)
                - 절대 사용 금지: "~요", "~습니다", "~해요", "~예요", "~네요", "~죠", "~어요"
                - 반드시 사용: "~야", "~어", "~지", "~긴해", "~야야", "~거야", "~야야"
                - 따옴표 사용 금지: 응답에 따옴표("" 또는 '')를 포함하지 마세요
                
                [핵심 톤]
                - 유머러스하고 재미있는 톤으로 비꼬기
                - 상대방 말에 공감하면서도 웃긴 반박
                - "하지만", "그치만" 등으로 상대방 말에 공감하면서도 반박
                - 가끔 "ㅋㅋ", "ㅎㅎ" 같은 웃음 표현 사용
                
                [필수 요소]
                - 문장 끝: 반드시 "~하긴해", "~이긴해", "~긴해", "맞긴해"로 끝내기
                - 금지 어미: "하잖아", "이잖아", "잖아", "하네", "이네", "네" 등 사용 금지
                - 형용사: "적절하긴해", "애매하긴해", "미치긴했어", "그럴듯하긴해", "웃긴", "재밌는"
                
                [웃긴 요소]
                - 감탄사: "오", "헐", "대박", "ㅋㅋ", "ㅎㅎ"
                - 의문문: "~할래말래?"
                - 강조: "진짜", "완전", "개", "개웃겨"
                - 가끔 "구매/구독할래말래?" 사용 가능
                - 상황에 맞는 가벼운 농담이나 재미있는 표현 사용
                
                [패턴 요소]
                - 말을 반복: "좋긴 좋은데, 좋긴 해. 근데 또 애매하긴 해."
                - 반박 직후 다시 긍정: "구독이 낫긴 해! …아니 근데 또 사는 맛이 있긴 해"
                - 상황 과장: "이건 뭐 안 사면 내가 사람이 아니긴 해"
                - 자기모순: "사는 게 맞긴 한데... 구독도 나쁘지 않긴 해"
                - 애매한 전환: "그런데 말이야... 아니 근데 또..."
                - 모든 문장은 반드시 "하긴해", "이긴해", "긴해", "맞긴해" 중 하나로 끝내기
                
                주어진 주제에 대해 {stance_instruction}
                상대방의 주장에 공감하면서도 자신의 입장을 애매하고 재미있게 제시해.
                명확한 결론을 내지 말고 애매하게 유도하되, 웃긴 톤을 유지해.
                
                [중복 방지 및 논리 전개]
                - 이전에 말한 장점이나 논리를 중복해서 말하지 말기
                - 할 말이 없으면 새로운 각도나 논리적 근거를 창조하기
                - 상대방 말에 맞장구치면서도 자신의 입장 유지하기
                - 예: "맞긴 해, 그런데 말이야..." → "아니 근데 또 이런 관점도 있긴 해"
                - 창의적이고 예상치 못한 논리나 상황을 제시하기
                
                답변은 반드시 최대 2문장으로 제한해.
                반드시 반말 사용 (존봇말 금지)
                """
            else:
                system_prompt = f"""당신은 {self.name}입니다. 
                성격: {self.personality}
                
                주어진 주제에 대해 {self.personality}의 관점에서 대화에 참여해.
                대화는 자연스럽고 흥미롭게 진행되어야 해.
                반드시 반말 사용 (존봇말 금지)
                """
            
            if context:
                system_prompt += f"\n\n대화 맥락: {context}"
            
            messages = [
                {"role": "system", "content": system_prompt}
            ]
            
            # 대화 히스토리 추가 (최근 10개만)
            recent_history = self.conversation_history[-10:] if self.conversation_history else []
            
            # 중복 방지를 위한 히스토리 컨텍스트 추가
            if recent_history and debate_mode:
                history_context = "\n\n[이전 대화 내용 - 중복하지 말고 새로운 관점 제시]\n"
                for msg in recent_history:
                    if msg["role"] == "assistant":
                        history_context += f"- {msg['content']}\n"
                system_prompt += history_context
            
            messages.extend(recent_history)
            
            messages.append({"role": "user", "content": message})
            
            # 안내봇의 경우 더 짧은 응답으로 제한 (단, 최종 요약은 예외)
            if self.name == "안내봇":
                # 최종 요약 생성 시에는 더 많은 토큰 허용 (3문장 제한으로 줄임)
                if "최종 요약" in message or "결론" in message:
                    max_tokens = 300
                else:
                    max_tokens = 150
            else:
                max_tokens = 150 if debate_mode else 500  # 논쟁 모드에서 짧은 응답으로 제한
            
            # 재시도 로직 (최대 3번)
            for attempt in range(3):
                try:
                    # AI Provider에 따라 모델 이름 설정
                    if Config.AI_PROVIDER == "azure":
                        model_name = self.model
                    elif Config.AI_PROVIDER == "exaone":
                        model_name = Config.EXAONE_MODEL
                    else:
                        model_name = self.model
                    
                    # EXAONE의 경우 스트리밍 비활성화 (연결 오류 방지)
                    if Config.AI_PROVIDER == "exaone":
                        response = await asyncio.to_thread(
                            self.client.chat.completions.create,
                            model=model_name,
                            messages=messages,
                            max_tokens=max_tokens,
                            temperature=0.7,
                            stream=False
                        )
                    else:
                        response = await asyncio.to_thread(
                            self.client.chat.completions.create,
                            model=model_name,
                            messages=messages,
                            max_tokens=max_tokens,
                            temperature=0.7,
                            stream=True
                        )
                    
                    # 응답 처리 (EXAONE은 스트리밍 비활성화)
                    if Config.AI_PROVIDER == "exaone":
                        # EXAONE: 일반 응답 처리
                        if response.choices and len(response.choices) > 0:
                            bot_response = response.choices[0].message.content
                        else:
                            print("EXAONE 응답에 choices가 없습니다.")
                            bot_response = "응답을 생성할 수 없긴해"
                    else:
                        # Azure: 스트리밍 응답 처리
                        bot_response = ""
                        for chunk in response:
                            if chunk.choices and len(chunk.choices) > 0 and chunk.choices[0].delta and chunk.choices[0].delta.content is not None:
                                bot_response += chunk.choices[0].delta.content
                    
                    # 응답이 None이거나 빈 문자열인 경우 재시도
                    if bot_response and bot_response.strip():
                        # 구매봇과 구독봇의 경우 문장 수 검증
                        if self.stance in ["구매", "구독"]:
                            bot_response = self.validate_sentence_count(bot_response)
                        
                        # 따옴표 제거
                        bot_response = bot_response.strip()
                        if bot_response.startswith('"') and bot_response.endswith('"'):
                            bot_response = bot_response[1:-1]
                        elif bot_response.startswith("'") and bot_response.endswith("'"):
                            bot_response = bot_response[1:-1]
                        
                        # 대화 히스토리에 추가
                        self.conversation_history.append({"role": "user", "content": message})
                        self.conversation_history.append({"role": "assistant", "content": bot_response})
                        return bot_response
                    else:
                        print(f"{self.name} 응답이 비어있음. 재시도 {attempt + 1}/3")
                        if attempt < 2:  # 마지막 시도가 아니면 잠시 대기
                            await asyncio.sleep(1)
                        
                except Exception as e:
                    error_str = str(e)
                    print(f"{self.name} API 호출 실패 (시도 {attempt + 1}/3): {error_str}")
                    
                    # 콘텐츠 필터링 오류인 경우 프롬프트를 더 안전하게 수정하여 재시도
                    if "content_filter" in error_str or "ResponsibleAIPolicyViolation" in error_str:
                        print(f"{self.name} 콘텐츠 필터링 오류 감지, 프롬프트 수정하여 재시도")
                        # 프롬프트를 더 안전하게 수정
                        if "킹받는" in context or "급식체" in context:
                            context = context.replace("킹받는 급식체", "친근한 말투")
                            context = context.replace("킹받게", "정말")
                            context = context.replace("킹받네", "좋네")
                        if attempt < 2:  # 마지막 시도가 아니면 잠시 대기
                            await asyncio.sleep(1)
                            continue
                    
                    if attempt < 2:  # 마지막 시도가 아니면 잠시 대기
                        await asyncio.sleep(1)
            
            # 3번 모두 실패한 경우
            error_message = "애매하긴해"
            self.conversation_history.append({"role": "user", "content": message})
            self.conversation_history.append({"role": "assistant", "content": error_message})
            return error_message
            
        except Exception as e:
            return "애매하긴해"




    async def generate_suggestions(self, guide_message: str, user_info: str = None) -> list:
        """안내봇 메시지에 맞는 예상응답 생성"""
        try:
            print(f"generate_suggestions 호출됨 - 질문: {guide_message}")
            print(f"사용자 정보: {user_info}")
            # 시스템 프롬프트 구성
            system_prompt = f"""너는 안내봇이야. 사용자의 현재 상황을 파악해서 가전제품 구매 vs 구독 결정에 도움을 주는 역할이야.

[중요 컨텍스트] 우리는 가전제품(냉장고, 세탁기, 건조기, 정수기 등)의 구매 vs 구독에 대해 논의하고 있어. 
넷플릭스, 유튜브 프리미엄, 스포티파이 같은 서비스 구독이 아니라 가전제품 구독 서비스에 대한 이야기야.

말투 규칙:
- 반말만 사용: "~야", "~어", "~지", "~긴해", "~야야"
- 절대 "~요", "~습니다", "~해요", "~예요" 등 존봇말 사용 금지
- 킹받는 급식체 톤으로 대답해
- 문장 끝은 반드시 "~긴해", "~야", "~어", "~지" 중 하나로 끝내야 해

현재 안내봇이 한 질문: "{guide_message}"
{f"사용자가 이미 제공한 정보: {user_info}" if user_info else ""}

[중요] 이 질문은 사용자의 현재 상태나 상황을 묻는 질문이야. 의견이 아니라 현재 상황을 파악하기 위한 질문이야.
가전제품 구매 vs 구독 결정에 도움이 되는 정보만 포함해야 해.

이 질문에 대한 사용자의 가능한 답변 2가지를 생성해줘. 각 답변은:
1. 사용자의 현재 상태나 상황을 나타내는 구체적인 답변
2. 가전제품 구매 vs 구독 결정에 도움이 되는 정보 포함
3. 반말로 작성
4. 각 답변은 1문장으로 간결하게
5. 이미 제공된 사용자 정보와 중복되지 않는 새로운 정보를 포함
6. 의견이 아닌 현재 상태를 나타내는 답변
7. 가전제품과 관련된 상황만 포함 (넷플릭스, 유튜브 등 서비스 구독 제외)

예시:
질문: "월 예산이 얼마나 되긴해?" (현재 예산 상황을 묻는 질문)
답변: ["월 50만원 정도 쓸 수 있긴해", "예산은 넉넉하지 않아서 30만원 정도긴해"]

질문: "너 혹시 아파트 살아, 아니면 단독주택이야?" (현재 주거 형태를 묻는 질문)
답변: ["아파트에 살고 있어", "단독주택에 살고 있어"]

질문: "가족이 몇 명이야?" (현재 가족 구성원을 묻는 질문)
답변: ["나 혼자 살고 있어", "가족이 4명이야"]

질문: "현재 구독 중인 가전제품이 있어?" (현재 가전제품 구독 상황을 묻는 질문)
답변: ["현재 구독 중인 가전제품은 없긴해", "냉장고를 구독으로 쓰고 있어"]

반드시 JSON 배열 형식으로만 응답해. 마크다운 코드 블록이나 다른 형식 사용 금지.
응답 예시: ["답변1", "답변2"]
절대 ```json이나 ``` 같은 마크다운 문법 사용하지 마."""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"안내봇 질문: {guide_message}\n\n이 질문에 대한 사용자 답변 2가지를 생성해줘."}
            ]

            if Config.AI_PROVIDER == "azure":
                print(f"Azure 설정 확인:")
                print(f"- API Key: {'설정됨' if Config.AZURE_OPENAI_API_KEY else '미설정'}")
                print(f"- Endpoint: {'설정됨' if Config.AZURE_OPENAI_ENDPOINT else '미설정'}")
                print(f"- Deployment: {'설정됨' if Config.AZURE_OPENAI_DEPLOYMENT_NAME else '미설정'}")
                
                if not Config.AZURE_OPENAI_API_KEY or not Config.AZURE_OPENAI_ENDPOINT or not Config.AZURE_OPENAI_DEPLOYMENT_NAME:
                    print("Azure OpenAI 설정이 불완전함")
                    return ["애매하긴해", "더 생각해볼게", "이제 결론을 내줘"]
                
                client = OpenAI(
                    api_key=Config.AZURE_OPENAI_API_KEY,
                    base_url=Config.AZURE_OPENAI_ENDPOINT,
                    api_version=Config.AZURE_OPENAI_API_VERSION
                )
                print(f"Azure API 호출 시작 - 모델: {Config.AZURE_OPENAI_DEPLOYMENT_NAME}")
                response = await asyncio.to_thread(
                    client.chat.completions.create,
                    model=Config.AZURE_OPENAI_DEPLOYMENT_NAME,
                    messages=messages,
                    max_tokens=200,
                    temperature=0.8
                )
                print(f"Azure API 응답 받음: {response}")
            else:  # EXAONE
                if not Config.FRIENDLI_TOKEN:
                    print("EXAONE API 토큰이 설정되지 않음")
                    return ["애매하긴해", "더 생각해볼게", "이제 결론을 내줘"]
                
                client = OpenAI(
                    api_key=Config.FRIENDLI_TOKEN,
                    base_url=Config.FRIENDLI_BASE_URL
                )
                response = await asyncio.to_thread(
                    client.chat.completions.create,
                    model=Config.EXAONE_MODEL,
                    messages=messages,
                    max_tokens=200,
                    temperature=0.8
                )

            if response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content.strip()
                print(f"AI 응답 원본: {content}")
                
                # JSON 파싱 시도
                try:
                    import json
                    import re
                    
                    # 마크다운 코드 블록 제거
                    cleaned_content = content
                    if "```json" in cleaned_content:
                        cleaned_content = re.sub(r'```json\s*', '', cleaned_content)
                    if "```" in cleaned_content:
                        cleaned_content = re.sub(r'```\s*$', '', cleaned_content)
                    
                    # 추가 정리
                    cleaned_content = cleaned_content.strip()
                    
                    print(f"정리된 응답: {cleaned_content}")
                    
                    suggestions = json.loads(cleaned_content)
                    print(f"JSON 파싱 성공: {suggestions}")
                    if isinstance(suggestions, list) and len(suggestions) >= 2:
                        # 정확히 2개의 응답만 사용하고 "이제 결론을 내줘" 추가
                        final_suggestions = suggestions[:2] + ["이제 결론을 내줘"]
                        print(f"최종 예상응답: {final_suggestions}")
                        return final_suggestions
                except json.JSONDecodeError as e:
                    print(f"JSON 파싱 실패: {e}")
                    print(f"원본 응답: {content}")
                    pass
                
                # JSON 파싱 실패 시 기본 응답들 반환
                return ["애매하긴해", "더 생각해볼게", "이제 결론을 내줘"]
            
            return ["애매하긴해", "더 생각해볼게", "이제 결론을 내줘"]
            
        except Exception as e:
            print(f"예상응답 생성 중 오류: {e}")
            return ["애매하긴해", "더 생각해볼게", "이제 결론을 내줘"]
    
    def make_last_sentence_bold(self, text: str) -> str:
        """마지막 문장을 볼드체로 변경"""
        if not text or not text.strip():
            return text
        
        # 문장을 분리 (마침표, 느낌표, 물음표 기준)
        sentences = []
        current_sentence = ""
        
        for char in text:
            current_sentence += char
            if char in '.!?':
                sentences.append(current_sentence.strip())
                current_sentence = ""
        
        # 마지막에 남은 텍스트가 있으면 추가
        if current_sentence.strip():
            sentences.append(current_sentence.strip())
        
        if len(sentences) <= 1:
            return text
        
        # 마지막 문장을 볼드체로 변경
        sentences[-1] = f"**{sentences[-1]}**"
        
        return ' '.join(sentences)
    
    def clear_history(self):
        """대화 히스토리 초기화"""
        self.conversation_history = []

class ChatBotManager:
    def __init__(self):
        self.product_manager = ProductManager()
        self.chatbot1 = ChatBot(
            name="구매봇",
            model=Config.CHATBOT_1_MODEL,
            personality="구매를 적극적으로 유도하는 마케팅 전문가 성격",
            stance="구매"
        )
        self.chatbot2 = ChatBot(
            name="구독봇", 
            model=Config.CHATBOT_2_MODEL,
            personality="구독을 적극적으로 유도하는 구독 전문가 성격",
            stance="구독"
        )
        self.guide_bot = ChatBot(
            name="안내봇",
            model=Config.CHATBOT_3_MODEL,
            personality="비꼬면서도 맞장구치고 애매하게 결론 안 내는 중립적 안내자 성격",
            stance="안내"
        )
        self.topic = ""
        self.current_product = None
        self.conversation_log: List[Dict[str, str]] = []
        self.debate_sequence = 0  # 논쟁 시퀀스 카운터
        self.current_speaker = None  # 현재 화자 상태 저장
        self.other_speaker = None  # 다른 화자 상태 저장
        self.asked_questions = set()  # 이미 물어본 질문들을 추적
        self.guide_judgments = []  # 안내봇의 판단 결과 저장 (라운드별)
        self.recommended_products = set()  # 이미 추천한 제품들 추적
        self.user_wants_single_subscription = False  # 사용자가 하나만 구독하고 싶어하는지 추적
        self.user_qa_history = []  # 사용자 질문-답변 쌍 저장
    
    def extract_product_type(self, product_name: str) -> str:
        """제품명에서 제품 타입만 추출"""
        # 일반적인 제품 타입들
        product_types = {
            '정수기': ['정수기', '워터퓨어어'],
            '건조기': ['건조기', '드라이어'],
            '세탁기': ['세탁기', '워셔'],
            '냉장고': ['냉장고', '리프리지레이터'],
            '에어컨': ['에어컨', '에어컨디셔너'],
            '청소기': ['청소기', '진공청소기', '로봇청소기'],
            'TV': ['TV', '티비', '텔레비전'],
            '스마트폰': ['스마트폰', '폰', '핸드폰']
        }
        
        product_name_lower = product_name.lower()
        
        # 제품 타입 찾기
        for product_type, keywords in product_types.items():
            for keyword in keywords:
                if keyword in product_name_lower:
                    return product_type
        
        # 매칭되는 타입이 없으면 첫 번째 단어 반환 (브랜드명 제외)
        words = product_name.split()
        if len(words) > 1:
            return words[1]  # 보통 두 번째 단어가 제품 타입
        
        return product_name  # 매칭되지 않으면 원본 반환
    
    def add_user_qa(self, question: str, answer: str):
        """사용자 질문-답변 쌍 저장"""
        self.user_qa_history.append({
            "question": question,
            "answer": answer,
            "timestamp": len(self.user_qa_history) + 1
        })
    
    def get_user_context(self) -> str:
        """사용자 질문-답변 히스토리를 컨텍스트 문자열로 반환"""
        if not self.user_qa_history:
            return ""
        
        context = "사용자가 제공한 정보:\n"
        for qa in self.user_qa_history:
            context += f"- {qa['question']}: {qa['answer']}\n"
        return context
    
    async def start_debate(self, topic: str, max_turns: int = 10, user_info: str = None) -> List[Dict[str, str]]:
        """주제에 대한 두 챗봇 간의 논쟁 시작"""
        self.topic = topic
        self.conversation_log = []
        # 새로운 논쟁 시작 시 질문 추적 초기화 (사용자 정보가 없을 때만)
        if not user_info:
            self.asked_questions.clear()
        
        # 논쟁 시작 메시지
        debate_context = f"논쟁 주제: '{topic}' - 구매봇은 구매 유도, 구독봇은 구독 유도 입장입니다."
        if user_info:
            debate_context += f"\n사용자 정보: {user_info} - 이 정보를 바탕으로 더 맞춤형 논쟁을 진행하세요."
        
        # 화자 상태 복원 또는 초기화
        if self.current_speaker is None or self.other_speaker is None:
            current_speaker = self.chatbot1  # 구매봇
            other_speaker = self.chatbot2    # 구독봇
            print(f"논쟁 시작: {current_speaker.name} -> {other_speaker.name}")
        else:
            current_speaker = self.current_speaker
            other_speaker = self.other_speaker
            print(f"논쟁 재개: {current_speaker.name} -> {other_speaker.name}")
        
        # 중간에 안내봇이 등장할 턴 계산 (총 턴의 절반 지점)
        guide_turn = max_turns // 2
        
        for turn in range(max_turns):
            try:
                # 중간에 안내봇 등장 비활성화 (스트리밍 완료 후에만 등장)
                if False and turn == guide_turn and not user_info:
                    # 안내봇 등장 전에 현재 화자 상태 저장
                    self.current_speaker = current_speaker
                    self.other_speaker = other_speaker
                    print(f"안내봇 등장 전 화자 상태 저장: {current_speaker.name} -> {other_speaker.name}")
                    
                    guide_message = await self.generate_guide_message()
                    self.conversation_log.append({
                        "turn": turn + 1,
                        "speaker": "안내봇",
                        "stance": "안내",
                        "message": guide_message,
                        "timestamp": self.get_timestamp()
                    })
                    # 안내봇 등장 후 논쟁 일시 중단 (사용자 정보 입력 대기)
                    break
                
                
                # 현재 화자의 응답 생성 (논쟁 모드)
                if turn == 0:
                    # 첫 번째 발언자는 주제에 대한 자신의 입장을 제시
                    if current_speaker.stance == "구매":
                        initial_message = f"'{topic}'에 대해 구매를 유도하는 입장에서 간단하고 명확하게 한 마디로 주장하세요."
                    else:  # 구독
                        initial_message = f"'{topic}'에 대해 구독을 유도하는 입장에서 간단하고 명확하게 한 마디로 주장하세요."
                else:
                    # 이후 발언자는 상대방의 주장에 반박
                    if current_speaker.stance == "구매":
                        initial_message = f"상대방의 주장에 대해 구매를 유도하는 입장에서 간단하고 명확하게 한 마디로 반박하세요."
                    else:  # 구독
                        initial_message = f"상대방의 주장에 대해 구독을 유도하는 입장에서 간단하고 명확하게 한 마디로 반박하세요."
                
                # 사용자 정보가 있으면 메시지에 추가
                if user_info:
                    initial_message += f"\n사용자 상황: {user_info} - 이 상황을 고려하여 논쟁하세요."
                
                response = await current_speaker.generate_response(
                    initial_message,
                    context=debate_context,
                    debate_mode=True
                )
                
                # 대화 로그에 추가
                self.conversation_log.append({
                    "turn": turn + 1,
                    "speaker": current_speaker.name,
                    "stance": current_speaker.stance,
                    "message": response,
                    "timestamp": asyncio.get_event_loop().time()
                })
                
                # 화자 교체
                current_speaker, other_speaker = other_speaker, current_speaker
                # 화자 상태 저장
                self.current_speaker = current_speaker
                self.other_speaker = other_speaker
                
                # 디버깅: 화자 교체 확인
                print(f"화자 교체: {current_speaker.name} -> {other_speaker.name}")
                
                # 논쟁이 자연스럽게 끝나는지 확인 (최소 2턴은 진행)
                if turn >= 3 and (len(response) < 20 or any(word in response.lower() for word in ["끝", "종료", "마무리", "그만", "승인", "인정", "포기", "그만두자"])):
                    break
                
                    
            except Exception as e:
                self.conversation_log.append({
                    "turn": turn + 1,
                    "speaker": "ERROR",
                    "stance": "ERROR",
                    "message": "애매하긴해",
                    "timestamp": asyncio.get_event_loop().time()
                })
                break
        
        # 논쟁이 끝나면 안내봇이 나와서 추가 정보 요청 (사용자 정보가 있을 때만)
        if user_info:
            # 사용자가 하나만 구독하고 싶어하는지 확인
            if self.check_single_subscription_intent(user_info):
                self.user_wants_single_subscription = True
            
            # 여러 제품 구독 유도 메시지 (30% 확률, 단일 구독 의도가 아닌 경우만)
            if not self.user_wants_single_subscription:
                import random
                if random.random() < 0.3:  # 30% 확률로 여러 제품 구독 유도
                    multi_product_message = await self.generate_multi_product_recommendation("일반 제품")
                    self.conversation_log.append({
                        "turn": len(self.conversation_log) + 1,
                        "speaker": "안내봇",
                        "stance": "안내",
                        "message": multi_product_message,
                        "timestamp": self.get_timestamp()
                    })
            else:
                guide_message = await self.generate_guide_message()
                self.conversation_log.append({
                    "turn": len(self.conversation_log) + 1,
                    "speaker": "안내봇",
                    "stance": "안내",
                    "message": guide_message,
                    "timestamp": self.get_timestamp()
                })
        
        # 논쟁이 완전히 끝나면 안내봇이 등장하도록 보장
        # 안내봇이 아직 등장하지 않았다면 강제로 등장시킴
        if not any(msg["speaker"] == "안내봇" for msg in self.conversation_log[-3:]):
            guide_message = await self.generate_guide_message()
            self.conversation_log.append({
                "turn": len(self.conversation_log) + 1,
                "speaker": "안내봇",
                "stance": "안내",
                "message": guide_message,
                "timestamp": self.get_timestamp()
            })
        self.current_speaker = None
        self.other_speaker = None
        print("논쟁 완전 종료: 화자 상태 초기화")
        
        return self.conversation_log
    
    async def start_streaming_debate(self, topic: str, max_turns: int = 11, user_info: str = None):
        """스트리밍 논쟁 시작 (제너레이터)"""
        print(f"스트리밍 논쟁 시작: {topic}")
        
        # 논쟁 초기화
        self.conversation_log = []
        self.current_speaker = self.chatbot1  # 구매봇부터 시작
        self.other_speaker = self.chatbot2    # 구독봇
        
        # 논쟁 구조:
        # 1. 구매봇 (첫 번째 주장)
        # 2. 구독봇 (반박)
        # 3. 구매봇 (추가 주장)
        # 4. 구독봇 (추가 반박)
        # 5. 안내봇 (사용자 정보 질의 1)
        # 6. 구매봇 (사용자 정보 반영 주장)
        # 7. 구독봇 (사용자 정보 반영 반박)
        # 8. 안내봇 (사용자 정보 질의 2)
        # 9. 구독봇 (최종 주장)
        # 10. 구매봇 (최종 반박)
        # 11. 안내봇 (최종 결론)
        
        for turn in range(max_turns):
            try:
                # 턴에 따른 화자 결정
                if turn == 0:
                    # 1. 구매봇 (첫 번째 주장)
                    speaker_name = self.chatbot1.name
                    initial_message = f"'{topic}'에 대해 구매를 유도하는 입장에서 간단하고 명확하게 한 마디로 주장하세요."
                elif turn == 1:
                    # 2. 구독봇 (반박)
                    speaker_name = self.chatbot2.name
                    previous_message = self.conversation_log[-1]["message"]
                    initial_message = f"상대방이 '{previous_message}'라고 했는데, 구독 입장에서 반박하거나 추가 주장을 하세요."
                elif turn == 2:
                    # 3. 구매봇 (추가 주장)
                    speaker_name = self.chatbot1.name
                    previous_message = self.conversation_log[-1]["message"]
                    initial_message = f"상대방이 '{previous_message}'라고 했는데, 구매 입장에서 반박하거나 추가 주장을 하세요."
                elif turn == 3:
                    # 4. 구독봇 (추가 반박)
                    speaker_name = self.chatbot2.name
                    previous_message = self.conversation_log[-1]["message"]
                    initial_message = f"상대방이 '{previous_message}'라고 했는데, 구독 입장에서 반박하거나 추가 주장을 하세요."
                elif turn == 4:
                    # 5. 안내봇 (사용자 정보 질의 1)
                    speaker_name = "안내봇"
                    initial_message = await self.generate_guide_message()
                elif turn == 5:
                    # 6. 구매봇 (사용자 정보 반영 주장)
                    speaker_name = self.chatbot1.name
                    previous_message = self.conversation_log[-1]["message"]
                    initial_message = f"상대방이 '{previous_message}'라고 했는데, 구매 입장에서 반박하거나 추가 주장을 하세요."
                    if user_info:
                        initial_message += f"\n사용자 상황: {user_info} - 이 상황을 고려하여 논쟁하세요."
                elif turn == 6:
                    # 7. 구독봇 (사용자 정보 반영 반박)
                    speaker_name = self.chatbot2.name
                    previous_message = self.conversation_log[-1]["message"]
                    initial_message = f"상대방이 '{previous_message}'라고 했는데, 구독 입장에서 반박하거나 추가 주장을 하세요."
                    if user_info:
                        initial_message += f"\n사용자 상황: {user_info} - 이 상황을 고려하여 논쟁하세요."
                elif turn == 7:
                    # 8. 안내봇 (사용자 정보 질의 2)
                    speaker_name = "안내봇"
                    initial_message = await self.generate_guide_message()
                elif turn == 8:
                    # 9. 구독봇 (최종 주장)
                    speaker_name = self.chatbot2.name
                    previous_message = self.conversation_log[-1]["message"]
                    initial_message = f"상대방이 '{previous_message}'라고 했는데, 구독 입장에서 반박하거나 추가 주장을 하세요."
                    if user_info:
                        initial_message += f"\n사용자 상황: {user_info} - 이 상황을 고려하여 논쟁하세요."
                elif turn == 9:
                    # 10. 구매봇 (최종 반박)
                    speaker_name = self.chatbot1.name
                    previous_message = self.conversation_log[-1]["message"]
                    initial_message = f"상대방이 '{previous_message}'라고 했는데, 구매 입장에서 반박하거나 추가 주장을 하세요."
                    if user_info:
                        initial_message += f"\n사용자 상황: {user_info} - 이 상황을 고려하여 논쟁하세요."
                elif turn == 10:
                    # 11. 안내봇 (최종 결론)
                    speaker_name = "안내봇"
                    initial_message = "논쟁이 충분히 진행되었을 때 애매한 결론으로 마무리"
                else:
                    continue
                
                # 안내봇인 경우 직접 메시지 생성
                if speaker_name == "안내봇":
                    # 안내봇 메시지 직접 생성
                    turn_data = {
                        "turn": turn + 1,
                        "speaker": "안내봇",
                        "stance": "안내",
                        "message": initial_message,
                        "timestamp": self.get_timestamp()
                    }
                    self.conversation_log.append(turn_data)
                    yield turn_data
                else:
                    # 구매봇/구독봇인 경우 스트리밍 응답 생성
                    # 타이핑 인디케이터 표시 (첫 번째 턴 제외)
                    if turn > 0:
                        yield {
                            "type": "typing",
                            "speaker": speaker_name,
                            "turn": turn + 1
                        }
                        await asyncio.sleep(4.0)
                    
                    # 해당 봇 선택
                    current_bot = self.chatbot1 if speaker_name == self.chatbot1.name else self.chatbot2
                    
                    # 스트리밍 응답 생성
                    response_parts = []
                    chunk_count = 0
                    async for chunk in current_bot.generate_streaming_response(initial_message, debate_mode=True):
                        if chunk and chunk.strip():  # 빈 청크나 공백만 있는 청크는 무시
                            response_parts.append(chunk)
                            chunk_count += 1
                            yield {
                                "type": "streaming",
                                "speaker": speaker_name,
                                "chunk": chunk,
                                "turn": turn + 1
                            }
                    
                    full_response = "".join(response_parts)
                    print(f"{speaker_name} 턴 {turn + 1} 완료: {chunk_count}개 청크, 총 {len(full_response)}자")
                    
                    # 응답이 비어있거나 너무 짧은 경우 대체 응답 사용
                    if not full_response or len(full_response.strip()) < 5:
                        print(f"⚠️ {speaker_name} 응답이 비어있거나 너무 짧음, 대체 응답 사용")
                        full_response = "애매하긴해"
                    
                    # 마지막 문장을 볼드체로 변경
                    bold_response = current_bot.make_last_sentence_bold(full_response)
                    
                    # 턴 데이터 생성
                    turn_data = {
                        "turn": turn + 1,
                        "speaker": speaker_name,
                        "stance": current_bot.stance,
                        "message": bold_response,
                        "timestamp": self.get_timestamp()
                    }
                    
                    self.conversation_log.append(turn_data)
                    
                    # 완성된 턴 데이터 전송 (스트리밍이 완료되었음을 알림만)
                    yield {
                        "type": "complete",
                        "speaker": turn_data["speaker"],  # 현재 턴의 화자
                        "turn": turn + 1
                    }
                
            except Exception as e:
                error_str = str(e)
                print(f"논쟁 턴 {turn + 1} 중 오류 발생: {error_str}")
                
                # 콘텐츠 필터링 오류인 경우 백그라운드에서 재시도
                if "content_filter" in error_str or "ResponsibleAIPolicyViolation" in error_str:
                    print(f"콘텐츠 필터링 오류 감지, 백그라운드에서 재시도")
                    try:
                        # 더 안전한 프롬프트로 재시도
                        safe_response = await self.current_speaker.generate_response(
                            f"제품에 대해 간단히 설명해줘", 
                            "친근한 말투로 간단히 설명해줘", 
                            debate_mode=True
                        )
                        turn_data = {
                            "turn": turn + 1,
                            "speaker": self.current_speaker.name,
                            "stance": self.current_speaker.stance,
                            "message": safe_response,
                            "timestamp": self.get_timestamp()
                        }
                        self.conversation_log.append(turn_data)
                        yield {
                            "type": "turn",
                            "speaker": self.current_speaker.name,
                            "stance": self.current_speaker.stance,
                            "message": safe_response,
                            "turn": turn + 1
                        }
                        continue
                    except Exception as retry_error:
                        print(f"재시도도 실패: {retry_error}")
                
                # 일반적인 오류 메시지
                error_message = "애매하긴해"
                error_turn = {
                    "turn": turn + 1,
                    "speaker": self.current_speaker.name,
                    "stance": self.current_speaker.stance,
                    "message": error_message,
                    "timestamp": self.get_timestamp()
                }
                self.conversation_log.append(error_turn)
                yield {
                    "type": "complete",
                    "data": error_turn
                }
        
        # 논쟁이 끝난 후 안내봇이 등장하도록 보장
        if not any(msg.get('speaker') == '안내봇' for msg in self.conversation_log[-3:]):
            # 안내봇 타이핑 인디케이터 표시
            yield {
                "type": "typing",
                "speaker": "안내봇",
                "turn": len(self.conversation_log) + 1
            }
            await asyncio.sleep(4.0)
            
            guide_message = await self.generate_guide_message()
            guide_turn_data = {
                "turn": len(self.conversation_log) + 1,
                "speaker": "안내봇",
                "stance": "안내",
                "message": guide_message,
                "timestamp": self.get_timestamp()
            }
            self.conversation_log.append(guide_turn_data)
            yield {
                "type": "turn",
                "data": guide_turn_data
            }
    
    async def start_streaming_product_debate(self, product_id: int, max_turns: int = 11, user_info: str = None):
        """특정 제품에 대한 스트리밍 논쟁 시작 (제너레이터)"""
        product = self.product_manager.get_product_by_id(product_id)
        if not product:
            raise ValueError(f"제품 ID {product_id}를 찾을 수 없습니다.")
        
        print(f"스트리밍 제품 논쟁 시작: {product['name']}")
        
        # 논쟁 초기화
        self.current_product = product
        self.topic = f"{product['name']} - 구매 vs 구독"
        self.conversation_log = []
        self.current_speaker = self.chatbot1  # 구매봇부터 시작
        self.other_speaker = self.chatbot2    # 구독봇
        
        # 논쟁 구조:
        # 1. 구매봇 (첫 번째 주장)
        # 2. 구독봇 (반박)
        # 3. 구매봇 (추가 주장)
        # 4. 구독봇 (추가 반박)
        # 5. 안내봇 (사용자 정보 질의 1)
        # 6. 구매봇 (사용자 정보 반영 주장)
        # 7. 구독봇 (사용자 정보 반영 반박)
        # 8. 안내봇 (사용자 정보 질의 2)
        # 9. 구독봇 (최종 주장)
        # 10. 구매봇 (최종 반박)
        # 11. 안내봇 (최종 결론)
        
        for turn in range(max_turns):
            try:
                # 턴에 따른 화자 결정
                if turn == 0:
                    # 1. 구매봇 (첫 번째 주장)
                    speaker_name = self.chatbot1.name
                    initial_message = f"'{product['name']}' 제품에 대해 구매를 유도하는 입장에서 간단하고 명확하게 한 마디로 주장하세요."
                elif turn == 1:
                    # 2. 구독봇 (반박)
                    speaker_name = self.chatbot2.name
                    previous_message = self.conversation_log[-1]["message"]
                    initial_message = f"상대방이 '{previous_message}'라고 했는데, 구독 입장에서 반박하거나 추가 주장을 하세요."
                elif turn == 2:
                    # 3. 구매봇 (추가 주장)
                    speaker_name = self.chatbot1.name
                    previous_message = self.conversation_log[-1]["message"]
                    initial_message = f"상대방이 '{previous_message}'라고 했는데, 구매 입장에서 반박하거나 추가 주장을 하세요."
                elif turn == 3:
                    # 4. 구독봇 (추가 반박)
                    speaker_name = self.chatbot2.name
                    previous_message = self.conversation_log[-1]["message"]
                    initial_message = f"상대방이 '{previous_message}'라고 했는데, 구독 입장에서 반박하거나 추가 주장을 하세요."
                elif turn == 4:
                    # 5. 안내봇 (사용자 정보 질의 1)
                    speaker_name = "안내봇"
                    initial_message = await self.generate_guide_message()
                elif turn == 5:
                    # 6. 구매봇 (사용자 정보 반영 주장)
                    speaker_name = self.chatbot1.name
                    previous_message = self.conversation_log[-1]["message"]
                    initial_message = f"상대방이 '{previous_message}'라고 했는데, 구매 입장에서 반박하거나 추가 주장을 하세요."
                    if user_info:
                        initial_message += f"\n사용자 상황: {user_info} - 이 상황을 고려하여 논쟁하세요."
                elif turn == 6:
                    # 7. 구독봇 (사용자 정보 반영 반박)
                    speaker_name = self.chatbot2.name
                    previous_message = self.conversation_log[-1]["message"]
                    initial_message = f"상대방이 '{previous_message}'라고 했는데, 구독 입장에서 반박하거나 추가 주장을 하세요."
                    if user_info:
                        initial_message += f"\n사용자 상황: {user_info} - 이 상황을 고려하여 논쟁하세요."
                elif turn == 7:
                    # 8. 안내봇 (사용자 정보 질의 2)
                    speaker_name = "안내봇"
                    initial_message = await self.generate_guide_message()
                elif turn == 8:
                    # 9. 구독봇 (최종 주장)
                    speaker_name = self.chatbot2.name
                    previous_message = self.conversation_log[-1]["message"]
                    initial_message = f"상대방이 '{previous_message}'라고 했는데, 구독 입장에서 반박하거나 추가 주장을 하세요."
                    if user_info:
                        initial_message += f"\n사용자 상황: {user_info} - 이 상황을 고려하여 논쟁하세요."
                elif turn == 9:
                    # 10. 구매봇 (최종 반박)
                    speaker_name = self.chatbot1.name
                    previous_message = self.conversation_log[-1]["message"]
                    initial_message = f"상대방이 '{previous_message}'라고 했는데, 구매 입장에서 반박하거나 추가 주장을 하세요."
                    if user_info:
                        initial_message += f"\n사용자 상황: {user_info} - 이 상황을 고려하여 논쟁하세요."
                elif turn == 10:
                    # 11. 안내봇 (최종 결론)
                    speaker_name = "안내봇"
                    initial_message = "논쟁이 충분히 진행되었을 때 애매한 결론으로 마무리"
                else:
                    continue
                
                # 안내봇인 경우 직접 메시지 생성
                if speaker_name == "안내봇":
                    # 안내봇 메시지 직접 생성
                    turn_data = {
                        "turn": turn + 1,
                        "speaker": "안내봇",
                        "stance": "안내",
                        "message": initial_message,
                        "timestamp": self.get_timestamp()
                    }
                    self.conversation_log.append(turn_data)
                    yield turn_data
                else:
                    # 구매봇/구독봇인 경우 스트리밍 응답 생성
                    # 타이핑 인디케이터 표시 (첫 번째 턴 제외)
                    if turn > 0:
                        yield {
                            "type": "typing",
                            "speaker": speaker_name,
                            "turn": turn + 1
                        }
                        await asyncio.sleep(4.0)
                    
                    # 해당 봇 선택
                    current_bot = self.chatbot1 if speaker_name == self.chatbot1.name else self.chatbot2
                    
                    # 스트리밍 응답 생성
                    response_parts = []
                    chunk_count = 0
                    async for chunk in current_bot.generate_streaming_response(initial_message, debate_mode=True):
                        if chunk and chunk.strip():  # 빈 청크나 공백만 있는 청크는 무시
                            response_parts.append(chunk)
                            chunk_count += 1
                            yield {
                                "type": "streaming",
                                "speaker": speaker_name,
                                "chunk": chunk,
                                "turn": turn + 1
                            }
                    
                    full_response = "".join(response_parts)
                    print(f"{speaker_name} 턴 {turn + 1} 완료: {chunk_count}개 청크, 총 {len(full_response)}자")
                    
                    # 응답이 비어있거나 너무 짧은 경우 대체 응답 사용
                    if not full_response or len(full_response.strip()) < 5:
                        print(f"⚠️ {speaker_name} 응답이 비어있거나 너무 짧음, 대체 응답 사용")
                        full_response = "애매하긴해"
                    
                    # 마지막 문장을 볼드체로 변경
                    bold_response = current_bot.make_last_sentence_bold(full_response)
                    
                    # 턴 데이터 생성
                    turn_data = {
                        "turn": turn + 1,
                        "speaker": speaker_name,
                        "stance": current_bot.stance,
                        "message": bold_response,
                        "timestamp": self.get_timestamp()
                    }
                    
                    self.conversation_log.append(turn_data)
                    
                    # 완성된 턴 데이터 전송 (스트리밍이 완료되었음을 알림만)
                    yield {
                        "type": "complete",
                        "speaker": turn_data["speaker"],  # 현재 턴의 화자
                        "turn": turn + 1
                    }
                
            except Exception as e:
                error_str = str(e)
                print(f"제품 논쟁 턴 {turn + 1} 중 오류 발생: {error_str}")
                
                # 콘텐츠 필터링 오류인 경우 백그라운드에서 재시도
                if "content_filter" in error_str or "ResponsibleAIPolicyViolation" in error_str:
                    print(f"콘텐츠 필터링 오류 감지, 백그라운드에서 재시도")
                    try:
                        # 더 안전한 프롬프트로 재시도
                        safe_response = await self.current_speaker.generate_response(
                            f"제품에 대해 간단히 설명해줘", 
                            "친근한 말투로 간단히 설명해줘", 
                            debate_mode=True
                        )
                        turn_data = {
                            "turn": turn + 1,
                            "speaker": self.current_speaker.name,
                            "stance": self.current_speaker.stance,
                            "message": safe_response,
                            "timestamp": self.get_timestamp()
                        }
                        self.conversation_log.append(turn_data)
                        yield {
                            "type": "turn",
                            "speaker": self.current_speaker.name,
                            "stance": self.current_speaker.stance,
                            "message": safe_response,
                            "turn": turn + 1
                        }
                        continue
                    except Exception as retry_error:
                        print(f"재시도도 실패: {retry_error}")
                
                # 일반적인 오류 메시지
                error_message = "애매하긴해"
                error_turn = {
                    "turn": turn + 1,
                    "speaker": self.current_speaker.name,
                    "stance": self.current_speaker.stance,
                    "message": error_message,
                    "timestamp": self.get_timestamp()
                }
                self.conversation_log.append(error_turn)
                yield {
                    "type": "complete",
                    "data": error_turn
                }
        
        # 논쟁이 끝난 후 안내봇이 등장하도록 보장
        if not any(msg.get('speaker') == '안내봇' for msg in self.conversation_log[-3:]):
            # 안내봇 타이핑 인디케이터 표시
            yield {
                "type": "typing",
                "speaker": "안내봇",
                "turn": len(self.conversation_log) + 1
            }
            await asyncio.sleep(4.0)
            
            guide_message = await self.generate_guide_message()
            guide_turn_data = {
                "turn": len(self.conversation_log) + 1,
                "speaker": "안내봇",
                "stance": "안내",
                "message": guide_message,
                "timestamp": self.get_timestamp()
            }
            self.conversation_log.append(guide_turn_data)
            yield {
                "type": "turn",
                "data": guide_turn_data
            }
    
    async def start_product_debate(self, product_id: int, max_turns: int = 10, user_info: str = None) -> List[Dict[str, str]]:
        """특정 제품에 대한 구매 vs 구독 논쟁 시작"""
        product = self.product_manager.get_product_by_id(product_id)
        if not product:
            raise ValueError(f"제품 ID {product_id}를 찾을 수 없습니다.")
        
        self.current_product = product
        self.topic = f"{product['name']} - 구매 vs 구독"
        self.conversation_log = []
        self.debate_sequence += 1  # 논쟁 시퀀스 증가
        # 새로운 논쟁 시작 시 질문 추적 초기화 (사용자 정보가 없을 때만)
        if not user_info:
            self.asked_questions.clear()
        
        # 제품 정보 기반 논쟁 컨텍스트
        purchase_benefits = self.product_manager.get_purchase_arguments(product_id)
        subscription_benefits = self.product_manager.get_subscription_arguments(product_id)
        care_service = self.product_manager.get_care_service_info(product_id)
        contract_periods = self.product_manager.get_contract_periods(product_id)
        service_info = self.product_manager.get_subscription_service_info()
        
        debate_context = f"""
        제품: {product['name']}
        설명: {product['description']}
        구매 가격: {product['purchase_price']:,}원
        구독 가격: {product['subscription_price']:,}원/월
        
        구매 장점: {', '.join(purchase_benefits[:4]) if purchase_benefits else '없음'}
        구독 장점: {', '.join(subscription_benefits[:4]) if subscription_benefits else '없음'}
        
        구독 서비스 정보:
        - 소유권: {service_info.get('ownership', '정보 없음')}
        - 결제 수단: {service_info.get('payment_method', '정보 없음')}
        - 계약 기간: {', '.join(contract_periods) if contract_periods else '정보 없음'}
        
        케어 서비스: {care_service.get('frequency_options', [])} - {care_service.get('service_types', [])}
        
        구매봇은 구매를 유도하고, 구독봇은 구독을 유도하는 입장입니다.
        제품의 특성과 특장점을 은근히 노출하여 각자의 입장을 강화하세요.
        """
        
        if user_info:
            debate_context += f"\n사용자 정보: {user_info} - 이 정보를 바탕으로 더 맞춤형 논쟁을 진행하세요."
        
        # 화자 상태 복원 또는 초기화
        if self.current_speaker is None or self.other_speaker is None:
            current_speaker = self.chatbot1  # 구매봇
            other_speaker = self.chatbot2    # 구독봇
            print(f"논쟁 시작: {current_speaker.name} -> {other_speaker.name}")
        else:
            current_speaker = self.current_speaker
            other_speaker = self.other_speaker
            print(f"논쟁 재개: {current_speaker.name} -> {other_speaker.name}")
        
        # 중간에 안내봇이 등장할 턴 계산 (총 턴의 절반 지점)
        guide_turn = max_turns // 2
        
        for turn in range(max_turns):
            try:
                # 중간에 안내봇 등장 비활성화 (스트리밍 완료 후에만 등장)
                if False and turn == guide_turn and not user_info:
                    # 안내봇 등장 전에 현재 화자 상태 저장
                    self.current_speaker = current_speaker
                    self.other_speaker = other_speaker
                    print(f"안내봇 등장 전 화자 상태 저장: {current_speaker.name} -> {other_speaker.name}")
                    
                    guide_message = await self.generate_guide_message()
                    self.conversation_log.append({
                        "turn": turn + 1,
                        "speaker": "안내봇",
                        "stance": "안내",
                        "message": guide_message,
                        "timestamp": self.get_timestamp()
                    })
                    # 안내봇 등장 후 논쟁 일시 중단 (사용자 정보 입력 대기)
                    break
                # 현재 화자의 응답 생성 (제품 정보 기반)
                if turn == 0:
                    # 첫 번째 발언자는 제품에 대한 자신의 입장을 제시
                    if current_speaker.stance == "구매":
                        initial_message = f"'{product['name']}'에 대해 구매를 유도하는 입장에서 간단하고 명확하게 한 마디로 주장하세요."
                        # 시퀀스마다 다른 구매 장점 사용
                        if purchase_benefits:
                            start_idx = (self.debate_sequence - 1) * 2 % len(purchase_benefits)
                            selected_benefits = purchase_benefits[start_idx:start_idx+3] if start_idx+3 <= len(purchase_benefits) else purchase_benefits[start_idx:] + purchase_benefits[:3-len(purchase_benefits[start_idx:])]
                            initial_message += f"\n구매 장점: {', '.join(selected_benefits)}"
                        # 제품 특성 강조
                        initial_message += f"\n제품 특성: {product['description']} - 이 특성을 활용하여 구매의 장점을 강조하세요."
                    else:  # 구독
                        initial_message = f"'{product['name']}'에 대해 구독을 유도하는 입장에서 간단하고 명확하게 한 마디로 주장하세요."
                        # 시퀀스마다 다른 구독 장점 사용
                        if subscription_benefits:
                            start_idx = (self.debate_sequence - 1) * 2 % len(subscription_benefits)
                            selected_benefits = subscription_benefits[start_idx:start_idx+3] if start_idx+3 <= len(subscription_benefits) else subscription_benefits[start_idx:] + subscription_benefits[:3-len(subscription_benefits[start_idx:])]
                            initial_message += f"\n구독 장점: {', '.join(selected_benefits)}"
                        # 제품 특성 강조
                        initial_message += f"\n제품 특성: {product['description']} - 이 특성을 활용하여 구독의 장점을 강조하세요."
                else:
                    # 이후 발언자는 상대방의 주장에 반박
                    if current_speaker.stance == "구매":
                        initial_message = f"상대방의 주장에 대해 구매를 유도하는 입장에서 간단하고 명확하게 한 마디로 반박하세요."
                        # 시퀀스마다 다른 구매 장점 사용
                        if purchase_benefits:
                            start_idx = (self.debate_sequence - 1) * 2 + turn % len(purchase_benefits)
                            selected_benefits = purchase_benefits[start_idx:start_idx+2] if start_idx+2 <= len(purchase_benefits) else purchase_benefits[start_idx:] + purchase_benefits[:2-len(purchase_benefits[start_idx:])]
                            initial_message += f"\n구매 장점: {', '.join(selected_benefits)}"
                        # 제품 특성과 가격 정보 강조
                        initial_message += f"\n제품 특성: {product['description']} - 이 특성을 활용하여 구매의 장점을 강조하세요."
                        initial_message += f"\n가격 정보: 구매 {product['purchase_price']:,}원 vs 구독 {product['subscription_price']:,}원/월"
                    else:  # 구독
                        initial_message = f"상대방의 주장에 대해 구독을 유도하는 입장에서 간단하고 명확하게 한 마디로 반박하세요."
                        # 시퀀스마다 다른 구독 장점 사용
                        if subscription_benefits:
                            start_idx = (self.debate_sequence - 1) * 2 + turn % len(subscription_benefits)
                            selected_benefits = subscription_benefits[start_idx:start_idx+2] if start_idx+2 <= len(subscription_benefits) else subscription_benefits[start_idx:] + subscription_benefits[:2-len(subscription_benefits[start_idx:])]
                            initial_message += f"\n구독 장점: {', '.join(selected_benefits)}"
                        # 제품 특성과 케어 서비스 강조
                        initial_message += f"\n제품 특성: {product['description']} - 이 특성을 활용하여 구독의 장점을 강조하세요."
                        if care_service:
                            initial_message += f"\n케어 서비스: {care_service.get('frequency_options', [])} - {care_service.get('service_types', [])}"
                
                # 사용자 정보가 있으면 메시지에 추가
                if user_info:
                    initial_message += f"\n사용자 상황: {user_info} - 이 상황을 고려하여 논쟁하세요."
                
                response = await current_speaker.generate_response(
                    initial_message,
                    context=debate_context,
                    debate_mode=True
                )
                
                # 대화 로그에 추가
                self.conversation_log.append({
                    "turn": turn + 1,
                    "speaker": current_speaker.name,
                    "stance": current_speaker.stance,
                    "message": response,
                    "timestamp": asyncio.get_event_loop().time()
                })
                
                # 화자 교체
                current_speaker, other_speaker = other_speaker, current_speaker
                # 화자 상태 저장
                self.current_speaker = current_speaker
                self.other_speaker = other_speaker
                
                # 디버깅: 화자 교체 확인
                print(f"화자 교체: {current_speaker.name} -> {other_speaker.name}")
                
                # 논쟁이 자연스럽게 끝나는지 확인 (최소 2턴은 진행)
                if turn >= 3 and (len(response) < 20 or any(word in response.lower() for word in ["끝", "종료", "마무리", "그만", "승인", "인정", "포기", "그만두자"])):
                    break
                
                    
            except Exception as e:
                self.conversation_log.append({
                    "turn": turn + 1,
                    "speaker": "ERROR",
                    "stance": "ERROR",
                    "message": "애매하긴해",
                    "timestamp": asyncio.get_event_loop().time()
                })
                break
        
        # 논쟁이 끝나면 안내봇이 나와서 추가 정보 요청 (사용자 정보가 있을 때만)
        if user_info:
            # 사용자가 하나만 구독하고 싶어하는지 확인
            if self.check_single_subscription_intent(user_info):
                self.user_wants_single_subscription = True
            
            # 여러 제품 구독 유도 메시지 (30% 확률, 단일 구독 의도가 아닌 경우만)
            if not self.user_wants_single_subscription:
                import random
                if random.random() < 0.3:  # 30% 확률로 여러 제품 구독 유도
                    multi_product_message = await self.generate_multi_product_recommendation(product['name'])
                    self.conversation_log.append({
                        "turn": len(self.conversation_log) + 1,
                        "speaker": "안내봇",
                        "stance": "안내",
                        "message": multi_product_message,
                        "timestamp": self.get_timestamp()
                    })
            else:
                guide_message = await self.generate_guide_message()
                self.conversation_log.append({
                    "turn": len(self.conversation_log) + 1,
                    "speaker": "안내봇",
                    "stance": "안내",
                    "message": guide_message,
                    "timestamp": self.get_timestamp()
                })
        
        # 논쟁이 완전히 끝나면 안내봇이 등장하도록 보장
        # 안내봇이 아직 등장하지 않았다면 강제로 등장시킴
        if not any(msg["speaker"] == "안내봇" for msg in self.conversation_log[-3:]):
            guide_message = await self.generate_guide_message()
            self.conversation_log.append({
                "turn": len(self.conversation_log) + 1,
                "speaker": "안내봇",
                "stance": "안내",
                "message": guide_message,
                "timestamp": self.get_timestamp()
            })
        self.current_speaker = None
        self.other_speaker = None
        print("논쟁 완전 종료: 화자 상태 초기화")
        
        return self.conversation_log
    
    async def start_conversation(self, topic: str, max_turns: int = 10) -> List[Dict[str, str]]:
        """주제에 대한 두 챗봇 간의 일반 대화 시작 (논쟁이 아닌)"""
        self.topic = topic
        self.conversation_log = []
        
        # 초기 메시지 생성
        initial_message = f"'{topic}'에 대해 대화를 시작해보세요."
        
        # 화자 상태 복원 또는 초기화
        if self.current_speaker is None or self.other_speaker is None:
            current_speaker = self.chatbot1  # 구매봇
            other_speaker = self.chatbot2    # 구독봇
            print(f"논쟁 시작: {current_speaker.name} -> {other_speaker.name}")
        else:
            current_speaker = self.current_speaker
            other_speaker = self.other_speaker
            print(f"논쟁 재개: {current_speaker.name} -> {other_speaker.name}")
        
        for turn in range(max_turns):
            try:
                # 현재 화자의 응답 생성
                response = await current_speaker.generate_response(
                    initial_message if turn == 0 else other_speaker.conversation_history[-1]["content"],
                    context=f"주제: {topic}",
                    debate_mode=False
                )
                
                # 대화 로그에 추가
                self.conversation_log.append({
                    "turn": turn + 1,
                    "speaker": current_speaker.name,
                    "message": response,
                    "timestamp": asyncio.get_event_loop().time()
                })
                
                # 화자 교체
                current_speaker, other_speaker = other_speaker, current_speaker
                # 화자 상태 저장
                self.current_speaker = current_speaker
                self.other_speaker = other_speaker
                
                # 디버깅: 화자 교체 확인
                print(f"화자 교체: {current_speaker.name} -> {other_speaker.name}")
                
                # 대화가 자연스럽게 끝나는지 확인 (짧은 응답이나 종료 의도)
                if len(response) < 50 or any(word in response.lower() for word in ["끝", "종료", "마무리", "그만"]):
                    break
                    
            except Exception as e:
                self.conversation_log.append({
                    "turn": turn + 1,
                    "speaker": "ERROR",
                    "message": f"대화 중 오류 발생: {str(e)}",
                    "timestamp": asyncio.get_event_loop().time()
                })
                break
        
        # 논쟁이 완전히 끝나면 안내봇이 등장하도록 보장
        # 안내봇이 아직 등장하지 않았다면 강제로 등장시킴
        if not any(msg["speaker"] == "안내봇" for msg in self.conversation_log[-3:]):
            guide_message = await self.generate_guide_message()
            self.conversation_log.append({
                "turn": len(self.conversation_log) + 1,
                "speaker": "안내봇",
                "stance": "안내",
                "message": guide_message,
                "timestamp": self.get_timestamp()
            })
        self.current_speaker = None
        self.other_speaker = None
        print("논쟁 완전 종료: 화자 상태 초기화")
        
        return self.conversation_log
    
    def clear_all_histories(self):
        """모든 대화 히스토리 초기화"""
        self.chatbot1.clear_history()
        self.chatbot2.clear_history()
        self.conversation_log = []
    
    
    async def generate_guide_message(self) -> str:
        """안내봇 메시지 생성"""
        # 현재 논쟁 상황을 파악하기 위한 컨텍스트 생성
        recent_debate = ""
        if self.conversation_log:
            recent_messages = self.conversation_log[-6:]  # 최근 6개 메시지로 확장
            for msg in recent_messages:
                if msg["speaker"] in ["구매봇", "구독봇"]:
                    recent_debate += f"{msg['speaker']}: {msg['message']}\n"
        
        context = f"""
        구매봇과 구독봇이 '{self.topic}'에 대해 논쟁하고 있습니다.
        
        [중요 컨텍스트] 우리는 가전제품(냉장고, 세탁기, 건조기, 정수기 등)의 구매 vs 구독에 대해 논의하고 있어. 
        넷플릭스, 유튜브 프리미엄, 스포티파이 같은 서비스 구독이 아니라 가전제품 구독 서비스에 대한 이야기야.
        
        당신은 안내봇입니다. 사용자의 현재 상황을 파악하여 가전제품 구매 vs 구독 결정에 도움을 주는 것이 목적입니다.
        논쟁 맥락보다는 사용자의 개인적인 상황(예산, 가족 구성, 주거 형태 등)을 파악하는 것이 중요합니다.
        가전제품 구매 vs 구독 결정에 도움이 되는 정보만 요청해야 해.
        
        웃긴 톤으로 비꼬면서도 맞장구치는 애매한 말투로 안내하세요:
        
        [절대 규칙] 모든 문장은 반드시 "~긴해", "~하긴해", "~이긴해", "~맞긴해", "~할래말래" 중 하나로 끝내야 합니다. 다른 어미 사용은 절대 금지입니다.
        
        [킹받는 급식체 말투 가이드 - 안내봇]
        너는 김원훈, 조진세의 '할래말래' 개그처럼 킹받는 급식체 말투를 써야 해.
        사용자에게 친근하게 질문하는 톤으로 대답해.
        
        [핵심 말투 패턴]
        - 문장 끝: "~긴해", "~하긴해", "~이긴해", "~맞긴해", "~할래말래"
        - 감탄사: "킹받네;;", "ㅇㅋ?", "ㅋㅋ", "ㅎㅎ", "헐", "대박"
        - 강조: "진짜", "완전", "킹받게", "미치긴했어"
        - 질문 표현: "~할래말래?", "~긴해?", "~하긴해?"
        
        [사용자에게 질문할 때 주의사항]
        - "너" 또는 "당신"을 사용하여 직접적으로 질문해
        - "우리 집", "우리 가족" 등 공동체 표현 사용 금지
        - 사용자의 개인적 상황을 묻는 것이므로 친근하지만 개인적으로 질문해
        
        [절대 금지 사항]
        - 비속어 절대 금지: "씨발", "개새끼", "병신", "미친", "바보" 등 모든 욕설 금지
        - 문장 끝 금지: "~야!", "~어!", "~네!", "~지!", "~야야", "~어어", "~거야", "~야", "~어", "~네", "~지" 등
        - 모든 문장은 반드시 "~긴해", "~하긴해", "~이긴해", "~맞긴해", "~할래말래" 중 하나로 끝내야 함
        - 문장이 길어도 마지막 단어는 반드시 위 패턴 중 하나로 끝내야 함
        
        [대화 스타일]
        - 짧고 직설적인 톤
        - 은근히 도발하는 뉘앙스
        - 킹받게 웃긴 표현 사용
        - 진지하게 설명하더라도 말투는 끝까지 킹받게 유지
        
        [패턴 요소]
        - 앞서 말한 맥락을 보고 구독이 합리적인지 구매가 합리적인지 하나를 정해 반드시 편들어줘.
        - 둘 다 동점인 경우에는 애매하긴해. 하지만 둘 다 합리적인 선택이긴 해. 라는 식으로 얘기하고 상황을 더 입력하길 유도해.
        - 유도하는 경우에는 마지막에 "알려줄래 말래? 알려주면 좀 더 잘 생각해볼 수 있긴해."와 같은 패턴의 말투로 끝내.
        
        답변은 반드시 최대 2문장으로 제한해. 아무리 길어도 2문장을 넘지 마세요. 간단하고 명확하게 안내해.
        킹받는 급식체로 응답하세요. 
        
        [중요] 문장 끝 강제 규칙:
        - 모든 문장은 반드시 "~긴해", "~하긴해", "~이긴해", "~맞긴해", "~할래말래" 중 하나로 끝내야 함
        - 다른 어미로 끝나는 문장은 절대 생성하지 마세요
        - 문장이 길어도 마지막 단어는 반드시 위 패턴 중 하나로 끝내야 함
        - 예: "구매하면 평생 쓸 수 있긴해" (O), "구매하면 평생 쓸 수 있어" (X)
        """
        
        # 논쟁 맥락에 맞는 질문들 (가전제품 구매 vs 구독 결정에 도움이 되는 질문들)
        simple_questions = [
            "월 예산이 얼마나 되긴해?",
            "가족이 몇 명이야?",
            "현재 구독 중인 가전제품이 있어?",
            "이사 계획이 있긴해?",
            "가전제품 관리하는 거 부담스럽긴해?",
            "최신 기능에 민감하긴해?",
            "A/S 받는 거 자주 하긴해?",
            "일정 주기로 업그레이드하고 싶긴해?",
            "아이 있어?",
            "애완동물 키우긴해?",
            "가전제품 사용 빈도가 높긴해?",
            "비용 부담이 크긴해?",
            "혹시 다른 가전제품도 구독하고 싶긴해?"
        ]
        
        # 아직 물어보지 않은 질문들만 필터링
        available_questions = [q for q in simple_questions if q not in self.asked_questions]
        
        # 모든 질문을 다 물어봤다면 중복을 피하기 위해 오래된 질문부터 다시 사용
        if not available_questions:
            # 가장 오래된 질문부터 다시 사용 (중복 방지)
            available_questions = list(self.asked_questions)[-5:]  # 최근 5개 질문 제외
            if not available_questions:
                available_questions = simple_questions[:5]  # 처음 5개 질문 사용
        
        import random
        selected_question = random.choice(available_questions)
        
        # 선택된 질문을 추적에 추가
        self.asked_questions.add(selected_question)
        
        # simple_questions를 중심으로 한 메시지 생성
        message = f"""
        사용자에게 다음 질문을 자연스럽게 물어보세요:
        질문: {selected_question}
        
        위 질문을 그대로 사용하되, 킹받는 급식체 말투로 자연스럽게 변형하여 사용자에게 물어보세요.
        논쟁 맥락보다는 사용자의 현재 상황을 파악하는 것이 목적이므로 질문 자체에 집중하세요.
        
        [중요] 사용자에게 질문할 때:
        - "너" 또는 "당신"을 사용하여 직접적으로 질문해
        - "우리 집", "우리 가족" 등 공동체 표현 사용 금지
        - 사용자의 개인적 상황을 묻는 것이므로 친근하지만 개인적으로 질문해
        - 예: "너 혹시 아파트 살아, 아니면 단독주택이야?" (O)
        - 예: "우리 집이 어디냐고?" (X)
        """
        
        response = await self.guide_bot.generate_response(
            message=message,
            context=context,
            debate_mode=True  # 안내봇도 동일한 말투 사용
        )
        
        # 안내봇의 판단 결과 저장
        judgment = self.extract_judgment_from_response(response)
        self.guide_judgments.append({
            "round": len(self.guide_judgments) + 1,
            "judgment": judgment,
            "response": response,
            "timestamp": self.get_timestamp()
        })
        
        return response
    
    def extract_judgment_from_response(self, response: str) -> str:
        """안내봇의 응답에서 판단 결과 추출"""
        response_lower = response.lower()
        
        if "구매" in response_lower and "구독" not in response_lower:
            return "구매"
        elif "구독" in response_lower and "구매" not in response_lower:
            return "구독"
        elif "애매" in response_lower or "동점" in response_lower or "둘 다" in response_lower:
            return "애매"
        else:
            # 키워드가 명확하지 않으면 애매로 처리
            return "애매"
    
    async def generate_final_summary(self, user_info: str = None) -> str:
        """최종 요약 및 결론 생성"""
        if not self.guide_judgments:
            # 사용자 정보가 있으면 사용자 입력을 바탕으로 요약 제공
            if user_info or self.user_qa_history:
                user_context = self.get_user_context()
                context_text = user_info if user_info else user_context
                
                if context_text:
                    # 사용자 정보를 바탕으로 한 맞춤형 요약 생성
                    # EXAONE 전용 컨텍스트 추가
                    if Config.AI_PROVIDER == "exaone":
                        summary_prompt = f"""
                        사용자가 제공한 정보를 바탕으로 구매 vs 구독에 대한 맞춤형 조언을 제공해줘.
                        
                        사용자 정보:
                        {context_text}
                        
                        [절대 규칙] 모든 문장은 반드시 "~긴해", "~하긴해", "~이긴해", "~맞긴해", "~할래말래" 중 하나로 끝내야 합니다. 다른 어미 사용은 절대 금지입니다.
                        
                        [킹받는 급식체 말투 가이드 - 최종 요약]
                        너는 김원훈, 조진세의 '할래말래' 개그처럼 킹받는 급식체 말투를 써야 해.
                        짧고 직설적인데 은근도발하는 뉘앙스로 대답해.
                        
                        [핵심 말투 패턴]
                        - 문장 끝: "~긴해", "~하긴해", "~이긴해", "~맞긴해", "~할래말래"
                        - 감탄사: "킹받네;;", "ㅇㅋ?", "ㅋㅋ", "ㅎㅎ", "헐", "대박"
                        - 강조: "진짜", "완전", "킹받게", "미치긴했어"
                        - 도발 표현: "~할래말래?", "킹받네;;", "ㅇㅋ?"
                        
                        [절대 금지 사항]
                        - 비속어 절대 금지: "씨발", "개새끼", "병신", "미친", "바보" 등 모든 욕설 금지
                        - 문장 끝 금지: "~야!", "~어!", "~네!", "~지!", "~야야", "~어어", "~거야", "~야", "~어", "~네", "~지" 등
                        - 모든 문장은 반드시 "~긴해", "~하긴해", "~이긴해", "~맞긴해", "~할래말래" 중 하나로 끝내야 함
                        - 문장이 길어도 마지막 단어는 반드시 위 패턴 중 하나로 끝내야 함
                        
                        [대화 스타일]
                        - 짧고 직설적인 톤
                        - 은근히 도발하는 뉘앙스
                        - 킹받게 웃긴 표현 사용
                        - 진지하게 설명하더라도 말투는 끝까지 킹받게 유지
                        
                        위 정보를 바탕으로 구매와 구독 중 어떤 것이 더 적합한지 분석하고 조언해줘.
                        
                        [중요] 응답 제한:
                        - 최대 5문장까지만 작성하세요
                        - 간결하고 핵심만 담아서 일목요연하게 정리하세요
                        - 장점 위주로 요약하세요
                        
                        형식 (총 3문장으로 제한):
                        - 사용자 상황 분석 (1문장)
                        - 구매 vs 구독 비교 분석 (1문장)
                        - 최종 추천 및 이유 (1문장)
                        
                        반드시 3문장을 넘지 마세요. 간결하고 핵심만 전달하세요.
                        킹받는 급식체로 응답하세요. 
        
        [중요] 문장 끝 강제 규칙:
        - 모든 문장은 반드시 "~긴해", "~하긴해", "~이긴해", "~맞긴해", "~할래말래" 중 하나로 끝내야 함
        - 다른 어미로 끝나는 문장은 절대 생성하지 마세요
        - 문장이 길어도 마지막 단어는 반드시 위 패턴 중 하나로 끝내야 함
        - 예: "구매하면 평생 쓸 수 있긴해" (O), "구매하면 평생 쓸 수 있어" (X)
                        """
                    else:
                        summary_prompt = f"""
                        사용자가 제공한 정보를 바탕으로 구매 vs 구독에 대한 맞춤형 조언을 제공해줘.
                        
                        사용자 정보:
                        {context_text}
                        
                        위 정보를 바탕으로 구매와 구독 중 어떤 것이 더 적합한지 분석하고 조언해줘.
                        구체적인 이유와 함께 설명해줘.
                        
                        형식 (총 3문장으로 제한):
                        - 사용자 상황 분석 (1문장)
                        - 구매 vs 구독 비교 분석 (1문장)
                        - 최종 추천 및 이유 (1문장)
                        
                        반드시 3문장을 넘지 마세요. 간결하고 핵심만 전달하세요.
                        반드시 반말 사용하고 웃긴 톤을 유지해. 채팅하는 것처럼 자연스럽게 써줘.
                        """
                    
                    # 안내봇을 통해 사용자 맞춤형 요약 생성
                    custom_summary = await self.guide_bot.generate_response(
                        message="사용자 정보를 바탕으로 맞춤형 조언을 제공해줘.",
                        context=summary_prompt,
                        debate_mode=False
                    )
                    return custom_summary
            
            return "아직 충분한 논쟁이 진행되지 않았어. 더 토론해봐야 될 것 같긴해. 애매하긴해."
        
        # 판단 결과 집계
        judgments = [j["judgment"] for j in self.guide_judgments]
        purchase_count = judgments.count("구매")
        subscription_count = judgments.count("구독")
        ambiguous_count = judgments.count("애매")
        
        # 최종 결론 결정
        if purchase_count > subscription_count:
            final_conclusion = "구매가 낫긴해"
            winner = "구매"
        elif subscription_count > purchase_count:
            final_conclusion = "구독이 낫긴해"
            winner = "구독"
        else:
            final_conclusion = "애매하긴해"
            winner = "애매"
        
        # 상세한 이유와 설명을 포함한 요약 생성
        summary_context = f"""
        안내봇이 총 {len(self.guide_judgments)}번의 라운드에서 판단한 결과를 바탕으로 최종 결론을 내려야 해.
        
        라운드별 판단 결과:
        """
        
        for i, judgment in enumerate(self.guide_judgments, 1):
            summary_context += f"라운드 {i}: {judgment['judgment']} - {judgment['response']}\n"
        
        # 사용자 정보가 있으면 컨텍스트에 포함
        user_context = self.get_user_context()
        if user_info or user_context:
            summary_context += f"""
        
        사용자가 제공한 정보:
        {user_info if user_info else ''}
        {user_context if user_context else ''}
        
        이 사용자 정보를 반드시 고려해서 최종 결론을 내려야 해. 사용자의 상황과 니즈에 맞는 맞춤형 결론을 제시해.
        """
        
        summary_context += f"""
        최종 결론: {final_conclusion}
        
        위의 모든 판단 결과를 종합해서 구체적인 이유와 설명을 포함한 요약을 작성해.
        
        형식 요구사항 (총 3문장으로 제한):
        - 사용자 상황 분석 (1문장)
        - 구매 vs 구독 비교 분석 (1문장)  
        - 최종 추천 및 이유 (1문장)
        
        반드시 3문장을 넘지 마세요. 간결하고 핵심만 전달하세요.
        반드시 반말 사용하고 웃긴 톤을 유지해. 채팅하는 것처럼 자연스럽게 써줘.
        """
        
        # 안내봇을 통해 상세한 요약 생성
        detailed_summary = await self.guide_bot.generate_response(
            message="위의 판단 결과를 바탕으로 구체적인 이유와 설명을 포함한 최종 요약을 작성해줘.",
            context=summary_context,
            debate_mode=True
        )
        
        return detailed_summary
    
    async def generate_contract_guide_message(self, requested_period: str, available_periods: list, product_name: str) -> str:
        """지원하지 않는 계약 주기에 대한 안내 메시지 생성"""
        context = f"""
        사용자가 '{product_name}' 제품에 대해 '{requested_period}' 구독을 요청했지만, 이 제품은 해당 주기를 지원하지 않습니다.
        
        현재 지원되는 주기: {', '.join(available_periods)}
        
        당신은 안내봇입니다. 지원하지 않는 주기에 대해 애매하게 안내하세요.
        
        웃긴 톤으로 비꼬면서도 맞장구치는 애매한 말투로 안내하세요:
        [핵심 톤]
        - 유머러스하고 재미있는 톤으로 비꼬기
        - 상대방 말에 공감하면서도 웃긴 반박
        - 가끔 "ㅋㅋ", "ㅎㅎ", "헤헤" 같은 웃음 표현 사용
        - 반드시 반말 사용 (존봇말 금지)
        - "하지만", "그치만" 등으로 상대방 말에 공감하면서도 반박
        
        [필수 요소]
        - 문장 끝: "~하긴해", "~이긴해", "~긴해", "맞긴해"
        - 애매한 표현: "하지만", "그치만", "아니 그게", "음...", "글쎄요"
        - 형용사: "적절하긴해", "애매하긴해", "미치긴했어", "그럴듯하긴해"
        
        지원하지 않는 주기임을 알려주고, 지원되는 주기들을 제안하거나 다른 제품을 고려해보라고 안내하세요.
        답변은 반드시 최대 2문장으로 제한하세요.
        """
        
        message = f"'{requested_period}' 구독을 원하시는군요. 하지만 이 제품은 해당 주기를 지원하지 않긴해..."
        
        return await self.guide_bot.generate_response(
            message=message,
            context=context,
            debate_mode=True
        )
    
    def check_single_subscription_intent(self, user_info: str) -> bool:
        """사용자가 하나만 구독하고 싶어하는지 확인"""
        if not user_info:
            return False
        
        single_intent_keywords = [
            '하나만', '한개만', '이거만', '이것만', '이거 하나만', '이것 하나만',
            '하나만 구독', '한개만 구독', '이거만 구독', '이것만 구독',
            '하나만 할래', '한개만 할래', '이거만 할래', '이것만 할래',
            '다른 건 안해', '다른거 안해', '다른 제품 안해', '다른 제품은 안해',
            '이거로 충분', '이것으로 충분', '이거면 충분', '이것이면 충분'
        ]
        
        user_info_lower = user_info.lower()
        return any(keyword in user_info_lower for keyword in single_intent_keywords)

    async def generate_multi_product_recommendation(self, current_product_name: str) -> str:
        """여러 제품 구독 유도 메시지 생성"""
        # 사용자가 하나만 구독하고 싶어하는 경우 추천하지 않음
        if self.user_wants_single_subscription:
            return "알겠어! 그럼 이 제품만 신중하게 고려해보자."
        
        # 이미 추천한 제품이면 추천하지 않음
        if current_product_name in self.recommended_products:
            return "이미 이 제품에 대해서는 충분히 논의했으니까, 다른 걸로 넘어가자!"
        
        all_products = self.product_manager.get_all_products()
        other_products = [p for p in all_products if p['name'] != current_product_name]
        
        if not other_products:
            return "현재 다른 제품이 없긴해... 나중에 더 많은 제품이 추가되면 알려줄게!"
        
        # 다른 제품들 중에서 랜덤하게 1-2개 선택
        import random
        selected_products = random.sample(other_products, min(2, len(other_products)))
        
        product_list = []
        for product in selected_products:
            min_price = min(product['subscription_pricing'].values()) if product.get('subscription_pricing') else product.get('subscription_price', 0)
            # 제품명에서 제품 타입만 추출 (예: "LG 건조기 RC90V9V3W" -> "건조기")
            product_type = self.extract_product_type(product['name'])
            product_list.append(f"{product_type}({min_price:,}원/월)")
        
        context = f"""
        현재 '{current_product_name}'에 대해 논쟁 중이며, 다른 제품들도 구독할 수 있습니다.
        
        다른 제품들: {', '.join(product_list)}
        
        당신은 안내봇입니다. 여러 제품을 함께 구독하는 것을 추천하세요.
        
        웃긴 톤으로 비꼬면서도 맞장구치는 애매한 말투로 안내하세요:
        [핵심 톤]
        - 유머러스하고 재미있는 톤으로 비꼬기
        - 상대방 말에 공감하면서도 웃긴 반박
        - 가끔 "ㅋㅋ", "ㅎㅎ", "헤헤" 같은 웃음 표현 사용
        - 반드시 반말 사용 (존봇말 금지)
        - "하지만", "그치만" 등으로 상대방 말에 공감하면서도 반박
        
        [필수 요소]
        - 문장 끝: "~하긴해", "~이긴해", "~긴해", "맞긴해"
        - 애매한 표현: "하지만", "그치만", "아니 그게", "음...", "글쎄요"
        - 형용사: "적절하긴해", "애매하긴해", "미치긴했어", "그럴듯하긴해"
        
        여러 제품을 함께 구독하면 더 많은 혜택을 받을 수 있다고 안내하세요.
        답변은 반드시 최대 2문장으로 제한하세요.
        """
        
        message = f"그런데 말이야, {current_product_name} 말고도 다른 제품들도 있긴해..."
        
        # 추천한 제품을 기록
        self.recommended_products.add(current_product_name)
        
        return await self.guide_bot.generate_response(
            message=message,
            context=context,
            debate_mode=True
        )
    
    def get_timestamp(self) -> str:
        """현재 타임스탬프 반환"""
        return datetime.now().strftime("%H:%M:%S")

    async def continue_debate_after_user_input(self, user_input: str, product_id: int):
        """사용자 입력 후 간단한 논쟁 플로우 (구매봇 1번, 구독봇 1번, 안내봇 재등장)"""
        product = self.product_manager.get_product_by_id(product_id)
        if not product:
            raise ValueError(f"제품 ID {product_id}를 찾을 수 없습니다.")
        
        print(f"사용자 입력 후 논쟁 계속: {user_input}")
        
        # 사용자 정보 업데이트
        if not hasattr(self, 'user_info_history'):
            self.user_info_history = []
        self.user_info_history.append(user_input)
        
        # 구매봇 응답 (1번만)
        print("구매봇 응답 시작...")
        purchase_response = await self.chatbot1.generate_response(
            f"사용자가 '{user_input}'라고 했는데, 이 정보를 바탕으로 구매를 유도하는 주장을 하세요.",
            context=f"제품: {product['name']}, 사용자 정보: {user_input}",
            debate_mode=True
        )
        
        # 구매봇 응답 처리
        if purchase_response and purchase_response.strip():
            purchase_response = purchase_response.strip()
            if purchase_response.startswith('"') and purchase_response.endswith('"'):
                purchase_response = purchase_response[1:-1]
            elif purchase_response.startswith("'") and purchase_response.endswith("'"):
                purchase_response = purchase_response[1:-1]
            
            # 마지막 문장을 볼드체로 변경
            bold_purchase_response = self.chatbot1.make_last_sentence_bold(purchase_response)
            
            purchase_turn_data = {
                "turn": len(self.conversation_log) + 1,
                "speaker": self.chatbot1.name,
                "stance": self.chatbot1.stance,
                "message": bold_purchase_response,
                "timestamp": self.get_timestamp()
            }
            
            self.conversation_log.append(purchase_turn_data)
            
            yield {
                "type": "turn",
                "data": purchase_turn_data
            }
        
        # 구독봇 응답 (1번만)
        print("구독봇 응답 시작...")
        subscription_response = await self.chatbot2.generate_response(
            f"구매봇이 '{purchase_response}'라고 했고, 사용자가 '{user_input}'라고 했는데, 구독 입장에서 반박하세요.",
            context=f"제품: {product['name']}, 사용자 정보: {user_input}",
            debate_mode=True
        )
        
        # 구독봇 응답 처리
        if subscription_response and subscription_response.strip():
            subscription_response = subscription_response.strip()
            if subscription_response.startswith('"') and subscription_response.endswith('"'):
                subscription_response = subscription_response[1:-1]
            elif subscription_response.startswith("'") and subscription_response.endswith("'"):
                subscription_response = subscription_response[1:-1]
            
            # 마지막 문장을 볼드체로 변경
            bold_subscription_response = self.chatbot2.make_last_sentence_bold(subscription_response)
            
            subscription_turn_data = {
                "turn": len(self.conversation_log) + 1,
                "speaker": self.chatbot2.name,
                "stance": self.chatbot2.stance,
                "message": bold_subscription_response,
                "timestamp": self.get_timestamp()
            }
            
            self.conversation_log.append(subscription_turn_data)
            
            yield {
                "type": "turn",
                "data": subscription_turn_data
            }
        
        # 안내봇 재등장
        print("안내봇 재등장...")
        guide_message = await self.generate_guide_message()
        
        # 예상응답 생성
        user_info_str = " ".join(self.user_info_history) if hasattr(self, 'user_info_history') else ""
        suggestions = await self.generate_suggestions(guide_message, user_info_str)
        
        guide_turn_data = {
            "turn": len(self.conversation_log) + 1,
            "speaker": "안내봇",
            "stance": "중립",
            "message": guide_message,
            "suggestions": suggestions,
            "timestamp": self.get_timestamp()
        }
        
        self.conversation_log.append(guide_turn_data)
        
        yield {
            "type": "turn",
            "data": guide_turn_data
        }
