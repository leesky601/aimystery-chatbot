from openai import AzureOpenAI, OpenAI
from typing import List, Dict, Optional, Any
import asyncio
from config import Config
from product_manager import ProductManager
from datetime import datetime
import json
import random

class ChatBot:
    def __init__(self, name: str, model: str, personality: str, stance: str):
        self.name = name
        self.model = model
        self.personality = personality
        self.stance = stance  # 논쟁에서의 입장 (찬성/반대)
        self.product_manager = ProductManager()  # 데이터 매니저 추가
        self.current_product_id = None  # 현재 논의 중인 제품 ID
        self.turn_count = 0  # 현재 턴 수 추적
        
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
    
    def set_current_product(self, product_id: int):
        """현재 논의할 제품 설정"""
        self.current_product_id = product_id
        self.turn_count = 0
    
    def build_data_driven_prompt(self, message: str, context: str = "") -> str:
        """데이터 기반 프롬프트 생성"""
        if not self.current_product_id:
            return context
        
        product = self.product_manager.get_product_by_id(self.current_product_id)
        if not product:
            return context
        
        # 턴 수 증가
        self.turn_count += 1
        
        # 제품 정보 추출
        product_name = product.get('name', '제품')
        purchase_price = product.get('purchase_price', 0)
        subscription_prices = product.get('subscription_price', {})
        
        # 구체적인 데이터 컨텍스트 생성
        data_context = f"\n\n[필수 참조 데이터 - 반드시 이 데이터를 기반으로 응답하세요]\n"
        data_context += f"제품명: {product_name}\n"
        data_context += f"구매가격: {purchase_price:,}원\n"
        
        if subscription_prices:
            data_context += "구독가격:\n"
            for period, price in subscription_prices.items():
                months = int(period.replace('년', '')) * 12
                total = price * months
                data_context += f"  - {period}: 월 {price:,}원 (총 {total:,}원)\n"
        
        # 입장별 구체적인 데이터 추가
        if self.stance == "구매":
            # 구매 관련 구체적 데이터
            purchase_benefits = product.get('purchase_benefits', [])
            if purchase_benefits:
                # 턴에 따라 다른 혜택 선택
                selected_benefit = purchase_benefits[min(self.turn_count - 1, len(purchase_benefits) - 1)]
                data_context += f"\n[이번 턴에 강조할 구매 혜택]: {selected_benefit}\n"
            
            # 구독과의 비교 데이터
            if subscription_prices:
                best_period = '6년' if '6년' in subscription_prices else list(subscription_prices.keys())[-1]
                months = int(best_period.replace('년', '')) * 12
                sub_total = subscription_prices[best_period] * months
                savings = sub_total - purchase_price
                if savings > 0:
                    data_context += f"\n[비교 포인트]: {best_period} 구독 시 총 {sub_total:,}원으로 구매보다 {savings:,}원 더 비쌈!\n"
            
            # 중고 판매 가치
            if purchase_price > 1000000:
                resale_value = int(purchase_price * 0.6)
                data_context += f"[중고 판매]: 나중에 팔면 약 {resale_value:,}원 회수 가능\n"
            
            # 위약금 정보
            penalty_info = self.product_manager.get_penalty_info()
            if penalty_info:
                early_termination = penalty_info.get('early_termination_fee', {})
                if early_termination:
                    data_context += f"[구독 위약금]: 1년 내 해지 시 잔여기간 요금의 30% 위약금!\n"
        
        else:  # 구독
            # 구독 관련 구체적 데이터
            subscription_benefits = product.get('subscription_benefits', [])
            if subscription_benefits:
                # 턴에 따라 다른 혜택 선택
                selected_benefit = subscription_benefits[min(self.turn_count - 1, len(subscription_benefits) - 1)]
                data_context += f"\n[이번 턴에 강조할 구독 혜택]: {selected_benefit}\n"
            
            # 초기 비용 부담
            data_context += f"\n[비교 포인트]: 구매는 한 번에 {purchase_price:,}원 목돈 필요! 부담스럽지?\n"
            
            # 케어서비스 정보
            care_service = product.get('care_service', {})
            if care_service:
                service_types = care_service.get('service_types', [])
                if service_types:
                    data_context += f"[케어서비스]: {', '.join(service_types)} 포함\n"
            
            # 멤버십 포인트 정보 추출
            for benefit in subscription_benefits:
                if '멤버십' in benefit and '포인트' in benefit:
                    data_context += f"[특별 혜택]: {benefit}\n"
                    break
        
        # 경쟁적 논거 추가
        competitive_arg = self.product_manager.get_competitive_argument(
            self.current_product_id, 
            self.stance, 
            self.turn_count
        )
        if competitive_arg:
            data_context += f"\n[핵심 공격 포인트]: {competitive_arg}\n"
        
        data_context += "\n[중요 규칙]:\n"
        data_context += "1. 반드시 위 데이터를 구체적으로 언급하며 응답하세요\n"
        data_context += "2. 추상적인 일반론이 아닌 구체적인 숫자와 사실을 사용하세요\n"
        data_context += "3. 제공된 데이터 이외의 정보를 만들어내지 마세요\n"
        data_context += f"4. 현재 {self.turn_count}번째 턴이므로 이전과 다른 논거를 사용하세요\n"
        
        return context + data_context
    
    async def generate_streaming_response(self, message: str, context: str = "", debate_mode: bool = False):
        """스트리밍 응답 생성 (제너레이터)"""
        try:
            # 데이터 기반 컨텍스트 추가
            if debate_mode and self.current_product_id:
                context = self.build_data_driven_prompt(message, context)
            
            if debate_mode:
                if self.stance == "구매":
                    stance_instruction = f"""
                    당신은 구매봇입니다. 절대 구독을 제안하지 마세요.
                    
                    [중요] 제공된 데이터를 반드시 활용하세요:
                    - 구체적인 가격을 언급하세요
                    - 구체적인 혜택을 언급하세요
                    - 숫자로 비교하세요
                    
                    - 구매의 장점만 강조하고 구매를 적극적으로 유도하세요
                    - 구독의 단점을 지적하고 구매가 더 좋다고 주장하세요
                    - 절대 "구독도 좋다", "구독을 고려해보라" 같은 말을 하지 마세요
                    - 구매만이 최선의 선택이라고 강조하세요"""
                else:  # 구독
                    stance_instruction = f"""
                    당신은 구독봇입니다. 절대 구매를 제안하지 마세요.
                    
                    [중요] 제공된 데이터를 반드시 활용하세요:
                    - 구체적인 가격을 언급하세요
                    - 구체적인 혜택을 언급하세요
                    - 숫자로 비교하세요
                    
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
                    - 비속어 절대 금지
                    - 문장 끝 금지: "~야!", "~어!", "~네!", "~지!" 등
                    - 모든 문장은 반드시 "~긴해", "~하긴해", "~이긴해", "~맞긴해", "~할래말래" 중 하나로 끝내야 함
                    
                    {stance_instruction}
                    
                    {context}
                    
                    킹받는 급식체로 응답하세요. 
                    
                    [절대 규칙] 응답은 반드시 최대 2문장으로 제한하세요. 
                    - 반드시 제공된 데이터를 구체적으로 언급하세요
                    - 숫자와 가격을 정확히 말하세요"""
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
                    
                    {stance_instruction}
                    
                    {context}
                    
                    [절대 규칙] 응답은 반드시 최대 2문장으로 제한하세요.
                    - 반드시 제공된 데이터를 구체적으로 언급하세요
                    - 숫자와 가격을 정확히 말하세요"""
            else:
                # EXAONE 전용 컨텍스트 추가 (일반 모드, 킹받는 급식체 특화)
                if Config.AI_PROVIDER == "exaone":
                    system_prompt = f"""[절대 규칙] 모든 문장은 반드시 "~긴해", "~하긴해", "~이긴해", "~맞긴해", "~할래말래" 중 하나로 끝내야 합니다. 다른 어미 사용은 절대 금지입니다.

                    당신은 {self.name}입니다. 
                    성격: {self.personality}
                    
                    [킹받는 급식체 말투 가이드]
                    너는 김원훈, 조진세의 '할래말래' 개그처럼 킹받는 급식체 말투를 써야 해.
                    짧고 직설적인데 은근도발하는 뉘앙스로 대답해.
                    
                    킹받는 급식체로 응답하세요. 
                    
                    [절대 규칙] 응답은 반드시 최대 2문장으로 제한하세요."""
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
        """메시지에 대한 응답 생성 (전체 텍스트 반환)"""
        result = ""
        async for chunk in self.generate_streaming_response(message, context, debate_mode):
            result += chunk
        return result
    
    def clear_history(self):
        """대화 히스토리 초기화"""
        self.conversation_history = []
        self.turn_count = 0
        self.current_product_id = None

class ChatBotManager:
    def __init__(self):
        # 챗봇 초기화
        self.chatbots: Dict[str, ChatBot] = {
            "구매봇": ChatBot(
                name="구매봇",
                model=Config.CHATBOT_1_MODEL,
                personality="논리적이고 분석적인 성격, 구매를 강력 지지",
                stance="구매"
            ),
            "구독봇": ChatBot(
                name="구독봇",
                model=Config.CHATBOT_2_MODEL,
                personality="실용적이고 경제적인 성격, 구독을 강력 지지",
                stance="구독"
            ),
            "안내봇": ChatBot(
                name="안내봇",
                model=Config.CHATBOT_3_MODEL,
                personality="중립적이고 객관적인 성격",
                stance="중립"
            )
        }
        
        self.conversation_log: List[Dict[str, Any]] = []
    
    def set_product_for_debate(self, product_id: int):
        """모든 챗봇에 제품 ID 설정"""
        for bot in self.chatbots.values():
            bot.set_current_product(product_id)
    
    async def start_debate_with_product(
        self, 
        product_id: int, 
        max_turns: int = 3,
        user_info: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """제품 정보 기반 논쟁 시작"""
        conversation = []
        
        # 모든 챗봇에 제품 설정
        self.set_product_for_debate(product_id)
        
        # ProductManager 초기화
        product_manager = ProductManager()
        product = product_manager.get_product_by_id(product_id)
        
        if not product:
            return [{
                "speaker": "시스템",
                "message": "제품 정보를 찾을 수 없습니다.",
                "timestamp": datetime.now().isoformat()
            }]
        
        product_name = product.get('name', '제품')
        
        # 안내봇 시작 멘트
        guide_bot = self.chatbots["안내봇"]
        intro_message = f"안녕하세요! 오늘은 '{product_name}'의 구매와 구독에 대해 논의해보겠습니다."
        
        if user_info:
            intro_message += f"\n고객님의 상황: {user_info}"
        
        intro_message += f"\n\n구매가격: {product.get('purchase_price', 0):,}원"
        if product.get('subscription_price'):
            intro_message += "\n구독가격:"
            for period, price in product['subscription_price'].items():
                intro_message += f"\n- {period}: 월 {price:,}원"
        
        conversation.append({
            "speaker": "안내봇",
            "message": intro_message,
            "timestamp": datetime.now().isoformat()
        })
        
        purchase_bot = self.chatbots["구매봇"]
        subscription_bot = self.chatbots["구독봇"]
        
        # 첫 번째 발언
        first_message = f"{product_name}에 대한 구매/구독 선택"
        
        # 구매봇 첫 발언
        purchase_response = await purchase_bot.generate_response(
            first_message,
            f"제품: {product_name}\n고객정보: {user_info if user_info else '일반 고객'}",
            debate_mode=True
        )
        
        conversation.append({
            "speaker": "구매봇",
            "message": purchase_response,
            "timestamp": datetime.now().isoformat()
        })
        
        # 구독봇 첫 발언
        subscription_response = await subscription_bot.generate_response(
            first_message,
            f"제품: {product_name}\n고객정보: {user_info if user_info else '일반 고객'}",
            debate_mode=True
        )
        
        conversation.append({
            "speaker": "구독봇",
            "message": subscription_response,
            "timestamp": datetime.now().isoformat()
        })
        
        # 나머지 턴 진행
        for turn in range(1, max_turns):
            # 구매봇 차례
            purchase_response = await purchase_bot.generate_response(
                f"구독봇이 '{subscription_response}'라고 했는데 어떻게 생각해?",
                f"턴 {turn + 1}/{max_turns}",
                debate_mode=True
            )
            
            conversation.append({
                "speaker": "구매봇",
                "message": purchase_response,
                "timestamp": datetime.now().isoformat()
            })
            
            # 구독봇 차례
            subscription_response = await subscription_bot.generate_response(
                f"구매봇이 '{purchase_response}'라고 했는데 어떻게 생각해?",
                f"턴 {turn + 1}/{max_turns}",
                debate_mode=True
            )
            
            conversation.append({
                "speaker": "구독봇",
                "message": subscription_response,
                "timestamp": datetime.now().isoformat()
            })
        
        # 안내봇 최종 정리
        summary_context = f"제품: {product_name}\n\n논쟁 요약:\n"
        for msg in conversation[-6:]:  # 최근 6개 메시지 참조
            if msg["speaker"] in ["구매봇", "구독봇"]:
                summary_context += f"- {msg['speaker']}: {msg['message']}\n"
        
        final_summary = await guide_bot.generate_response(
            "이번 논쟁을 정리하고 고객에게 선택에 도움이 되는 조언을 해줘",
            summary_context,
            debate_mode=False
        )
        
        conversation.append({
            "speaker": "안내봇",
            "message": final_summary,
            "timestamp": datetime.now().isoformat()
        })
        
        # 대화 로그에 추가
        self.conversation_log.extend(conversation)
        
        return conversation
    
    async def generate_single_response(self, chatbot_name: str, message: str) -> str:
        """특정 챗봇의 단일 응답 생성"""
        if chatbot_name not in self.chatbots:
            raise ValueError(f"챗봇 '{chatbot_name}'을 찾을 수 없습니다")
        
        chatbot = self.chatbots[chatbot_name]
        response = await chatbot.generate_response(message)
        
        # 로그에 추가
        self.conversation_log.append({
            "speaker": chatbot_name,
            "message": response,
            "timestamp": datetime.now().isoformat()
        })
        
        return response
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """전체 대화 히스토리 반환"""
        return self.conversation_log
    
    def clear_all_history(self):
        """모든 대화 히스토리 초기화"""
        self.conversation_log = []
        for chatbot in self.chatbots.values():
            chatbot.clear_history()