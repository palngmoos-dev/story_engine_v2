from typing import List, Dict, Any, Optional
from .state_model import WriterCard
import random

class WriterFactory:
    _POOL = [
        WriterCard(
            writer_id="standard_director",
            name="상업 영화 작가",
            domain="영화/드라마",
            genre="보편적 드라마",
            personality="균형감 있는 흥행 지향형",
            style_rules=["기승전결의 명확함", "보편적 공감대"],
            tension_curve="3단 구성",
            pacing="balanced"
        ),
        WriterCard(
            writer_id="noir_detective",
            name="하드보일드 작가",
            domain="장르 소설",
            genre="느와르/추리",
            personality="냉소적이고 간결한 필체",
            style_rules=["짧은 문장", "건조한 묘사", "비정한 분위기"],
            tension_curve="서서히 고조되는 긴장",
            pacing="slow",
            writer_effects={"pressure_boost": 1.5}
        ),
        WriterCard(
            writer_id="romantic_poet",
            name="로맨틱 서정시인",
            domain="순수 문학",
            genre="로맨스/드라마",
            personality="섬세하고 감성적인 표현",
            style_rules=["유려한 문장", "내면 심리 묘사", "서정적 비유"],
            tension_curve="감정적 파동",
            pacing="gentle"
        ),
        WriterCard(
            writer_id="thriller_master",
            name="서스펜스 마스터",
            domain="장르 소설",
            genre="스릴러/호러",
            personality="심박수를 높이는 긴박한 전개",
            style_rules=["빈번한 반전", "불안의 전염", "날카로운 대사"],
            tension_curve="급격한 변동",
            pacing="fast",
            writer_effects={"pressure_boost": 2.0}
        ),
        WriterCard(
            writer_id="fantasy_chronicler",
            name="판타지 기록술사",
            domain="하이 판타지",
            genre="판타지/모험",
            personality="방대한 세계관과 경이로운 묘사",
            style_rules=["신화적 어조", "풍부한 배경 설명", "장엄한 스케일"],
            tension_curve="대서사적 흐름",
            pacing="epic"
        )
    ]

    @staticmethod
    def get_random_pool(count: int = 3) -> List[WriterCard]:
        return random.sample(WriterFactory._POOL, min(count, len(WriterFactory._POOL)))

    @staticmethod
    def get_by_id(writer_id: str) -> WriterCard:
        writer = next((w for w in WriterFactory._POOL if w.writer_id == writer_id), None)
        if not writer:
            return WriterFactory._POOL[0] # Fallback to standard
        return writer.copy(deep=True)
