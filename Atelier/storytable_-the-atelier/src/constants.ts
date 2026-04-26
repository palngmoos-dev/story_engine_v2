import {
  CardData, CardType, CharacterCard, RelationshipCard, SpaceCard, TimelineCard,
  ElementCard, CinematicCard, MoodCard, SenseCard, AudioCard,
  PropCard, ConceptCard, GuideCard, NarrativeStats, CharacterRole
} from './types';

// ── Utilities ──
export const getRandomItem = <T>(arr: T[]): T => arr[Math.floor(Math.random() * arr.length)];
const uid = () => Math.random().toString(36).substr(2, 9);
const ri = (): NarrativeStats => ({ suspicion: Math.floor(Math.random() * 3), pressure: Math.floor(Math.random() * 3), echo: Math.floor(Math.random() * 3) });

// ══════════════════════════════════════════════
//  1. CHARACTER (캐릭터 - 육하원칙 상세 설정)
// ══════════════════════════════════════════════
const CHAR = {
  names: ['엘리아스','아리스 박사','민소라','재스퍼','이사벨라','준','민지','아서','박현우','최서윤','김도윤','비밀 요원','수상한 이웃','강철 로봇','숨어있는 목격자'],
  jobs: ['은퇴한 탐정','유전 공학자','보안 해커','프리랜서 건축가','고전 수리공','특수 경호원','초등학교 교사','박물관 큐레이터','기억 청소부','심해 잠수부','차원 여행가','심야 배달부'],
  personalities: ['냉철하고 분석적','꼼꼼하고 계획적','사교적이고 유머러스','조용하고 사색적','씩씩하고 도전적','실용주의적','낙천적이고 긍정적','신비롭고 내성적','계산적이고 똑똑함','착하고 이타적','장난기 많고 활발','엄격한 정의로움'],
  weaknesses: ['높은 곳을 극도로 무서워함','심각한 카페인 중독','자신만의 세계에 갇힌 고집','반짝이는 것에 대한 탐욕','거절을 못 하는 성격','만성적인 수면 부족','과거의 실수에 대한 죄책감','치명적인 호기심','자주 깜빡하는 건망증','거짓말을 하면 몸이 떨림'],
  skills: ['전문적인 자물쇠 따기','복잡한 암호 해석','프로급 격투 기술','심리를 꿰뚫는 설득력','1분에 수십 페이지를 읽는 속독','완벽한 변장과 연기','식물과 대화하는 능력','기계 장치 즉석 수리','5개 국어 구사'],
  hobbies: ['태권도','민물 낚시','고전 소설 수집','LP 판 감상','암벽 등반','정원 가꾸기','오토바이 수리','천체 관측','길고양이 밥 주기','십자말풀이'],
  upbringings: ['엄격한 교육자 집안','폐허가 된 연구소','바닷가 근처 작은 마을','몰락한 귀족 가문','익명의 복지 시설','기계가 지배하는 지하 공장','평범하지만 따뜻한 중산층 가정'],
  relationships: ['전직 경찰 반장의 외아들','잊혀진 영웅의 제자','재벌가의 숨겨진 자녀','유명 과학자의 연구 파트너','전쟁터에서 만난 생사고락 동료','우연히 사건을 목격한 목격자'],
  cars: ['낡은 90년대 빈티지 세단','최신형 전기 스포츠카','먼지 쌓인 캠핑카','빠른 속도의 오토바이','튼튼한 4륜 구동 SUV','심플한 소형 해치백','클래식한 클래식 카'],
  bloods: ['A형','B형','O형','AB형'],
  mbtis: ['INTJ','ENFP','ISTP','INFJ','ENTJ','ISFP','ENTP','ISTJ'] as const,
  flaws: ['물 공포증','폐쇄 공포증','소음에 민감','자기파괴적 충동','타인에 대한 깊은 불신','완벽주의','감정 표현 불능','극단적 자기희생','참견 강박'],
  secrets: ['사실 히어로의 후예','기계 심장을 가짐','큰 사건의 유일한 목격자','사실은 로봇임','미래에서 온 사람','지워진 기억을 찾음','비밀 보물을 지키는 중'],
  speechStyles: ['무뚝뚝하지만 핵심을 찌름','부드럽고 설득력 있음','기계처럼 정확하고 건조함','혼잣말이 섞인 중얼거림','단호하고 위엄 있는 말투','시적이고 은유적인 표현','논리적이고 데이터 중심적'],
  backgrounds: ['유일한 생존자','실험실에서 탄생','기억을 잃은 방랑자','몰락한 가문의 자녀','예언의 아이','인간의 마음을 가진 안드로이드'],
};

export const generateCharacterCard = (): CharacterCard => ({
  type: 'character', id: uid(),
  name: getRandomItem(CHAR.names), age: (Math.floor(Math.random() * 40) + 20).toString(),
  job: getRandomItem(CHAR.jobs), personality: getRandomItem(CHAR.personalities),
  weakness: getRandomItem(CHAR.weaknesses), skill: getRandomItem(CHAR.skills),
  role: getRandomItem(['Lead','Support'] as CharacterRole[]),
  level: Math.floor(Math.random() * 30) + 70,
  mbti: getRandomItem([...CHAR.mbtis]), 
  gender: getRandomItem(['male', 'female'] as const),
  bloodType: getRandomItem(CHAR.bloods),
  upbringing: getRandomItem(CHAR.upbringings),
  relationshipDesc: getRandomItem(CHAR.relationships),
  hobbies: getRandomItem(CHAR.hobbies),
  car: getRandomItem(CHAR.cars),
  flaw: getRandomItem(CHAR.flaws),
  secret: getRandomItem(CHAR.secrets), speechStyle: getRandomItem(CHAR.speechStyles),
  background: getRandomItem(CHAR.backgrounds), baseImpact: ri(),
});

// ══════════════════════════════════════════════
//  2. RELATIONSHIP (관계 - 감성적 역학)
// ══════════════════════════════════════════════
const RELS = [
  { name: '깊은 유대감', description: '말로 설명할 수 없는 강력한 믿음의 연결' },
  { name: '아름다운 이별', description: '서로를 위해 눈물을 머금고 돌아서는 순간' },
  { name: '영혼의 단짝', description: '서로의 생각을 눈빛만으로 읽어내는 사이' },
  { name: '안타까운 오해', description: '진심이 전달되지 않아 생기는 서글픈 거리감' },
  { name: '운명적 라이벌', description: '서로를 성장시키는 가장 치열하고 뜨거운 경쟁' },
  { name: '침묵의 복종', description: '거부할 수 없는 힘에 이끌려 따르는 헌신' },
  { name: '절대적 공생', description: '한쪽이 무너지면 같이 무너지는 운명 공동체' },
];
export const generateRelationshipCard = (): RelationshipCard => {
  const r = getRandomItem(RELS);
  return { type: 'relationship', id: uid(), name: r.name, description: r.description, baseImpact: ri() };
};

// ══════════════════════════════════════════════
//  3. SPACE (장소 - 시각적/감각적 느낌)
// ══════════════════════════════════════════════
const SPACES = [
  { name: '시간이 멈춘 다락방', description: '먼지 섞인 햇살이 틈새로 스며드는 정적의 공간', modifiers: '기억×2.5, 정적×1.8', impact: { suspicion: 1, pressure: 1, echo: 3 } },
  { name: '비 오는 밤의 기차역', description: '차가운 빗줄기와 멀어지는 기적 소리가 주는 쓸쓸한 해방감', modifiers: '고립×1.5, 그리움×2.0', impact: { suspicion: 0, pressure: 2, echo: 2 } },
  { name: '꿈꾸는 식물원', description: '이름 모를 꽃들이 내뱉는 향기가 몽환적인 분위기를 만드는 유리방', modifiers: '환각×1.2, 치유×1.8', impact: { suspicion: 0, pressure: 0, echo: 5 } },
  { name: '비밀스러운 지하실', description: '누군가의 숨소리가 벽 너머에서 들릴 것 같은 서늘한 긴장감', modifiers: '추적×2.0, 은폐×1.5', impact: { suspicion: 4, pressure: 2, echo: 0 } },
  { name: '노을 지는 옥상', description: '도시의 소음이 아득하게 들리고 하늘이 붉게 물드는 평화로운 경계', modifiers: '회상×2.0, 고백×1.5', impact: { suspicion: -1, pressure: -2, echo: 2 } },
];
export const generateSpaceCard = (): SpaceCard => {
  const s = getRandomItem(SPACES);
  return { type: 'space', id: uid(), name: s.name, description: s.description, modifiers: s.modifiers, baseImpact: s.impact };
};

// ══════════════════════════════════════════════
//  4. TIMELINE (시간 - 미학적 무드)
// ══════════════════════════════════════════════
const CHRONOS = [
  { mode: 'PAST' as const, color: '🔴', aesthetic: '빛바랜 사진처럼 아련하고 무거운 질감' },
  { mode: 'PRESENT' as const, color: '🟡', aesthetic: '날카롭고 현실적이며 숨 가쁘게 흘러가는 공기' },
  { mode: 'FUTURE' as const, color: '🔵', aesthetic: '차가운 금속광과 네온빛이 섞인 이질적이고 몽환적인 감각' },
];
export const generateTimelineCard = (): TimelineCard => {
  const c = getRandomItem(CHRONOS);
  const eras = ['낭만이 넘치던 시대','기술이 지배하는 미래','가장 평범한 오늘','꿈속의 어느 날'];
  const vibes = ['애틋한','서늘한','찬란한','위태로운','정적인'];
  return { type: 'timeline', id: uid(), era: getRandomItem(eras), vibe: getRandomItem(vibes), chronosMode: c.mode, chronosColor: c.color, chronosAesthetic: c.aesthetic, baseImpact: ri() };
};

// ══════════════════════════════════════════════
//  5. ELEMENT (에너지 - 장면의 기운)
// ══════════════════════════════════════════════
const ELEMENTS = [
  { name: '타오르는 불꽃', theme: '모든 것을 집어삼킬 듯한 파괴적이고 뜨거운 열기' },
  { name: '고요한 흐름', theme: '차갑고 깊은 곳으로 끌어당기는 유연한 물의 기운' },
  { name: '묵직한 대지', theme: '단단하게 뿌리 내린 결코 흔들리지 않는 무게감' },
  { name: '보이지 않는 바람', theme: '어디로 튈지 모르는 빠르고 종잡을 수 없는 변화무쌍함' },
  { name: '찰나의 빛', theme: '어둠을 찢고 나타나는 강렬하고 짜릿한 충격' },
];
export const generateElementCard = (): ElementCard => {
  const e = getRandomItem(ELEMENTS);
  return { type: 'element', id: uid(), name: e.name, theme: e.theme, baseImpact: ri() };
};

// ══════════════════════════════════════════════
//  6. CINEMATIC (카메라 - 시각적 느낌 위주)
// ══════════════════════════════════════════════
const CINEMATICS = [
  { name: '밀착된 시선', description: '인물의 숨소리와 눈빛의 떨림까지 느껴지는 아주 가까운 거리감' },
  { name: '고독한 거리', description: '주변 풍경 속에 인물이 아주 작게 느껴지는 광활한 고립감' },
  { name: '압도적인 시야', description: '위에서 아래로 굽어보며 느끼는 권위적이고 냉소적인 시각' },
  { name: '불안한 흔들림', description: '심장이 뛰는 속도에 맞춰 화면이 불규칙하게 요동치는 긴장감' },
  { name: '포근한 오렌지빛 조명', description: '오후의 햇살이 창가에 내려앉아 모든 것을 부드럽게 감싸는 따뜻함' },
  { name: '서늘한 푸른 그림자', description: '깊은 밤의 차가운 공기가 느껴지는 푸른색 위주의 가라앉은 분위기' },
  { name: '왜곡된 세상', description: '화면이 기우뚱하게 기울어져 뭔가 잘못되었다는 것을 암시하는 불안감' },
];
export const generateCinematicCard = (): CinematicCard => {
  const c = getRandomItem(CINEMATICS);
  return { type: 'cinematic', id: uid(), name: c.name, description: c.description, baseImpact: ri() };
};

// ══════════════════════════════════════════════
//  7. MOOD (기분 - 정서적 힘)
// ══════════════════════════════════════════════
const MOODS = [
  { name: '가슴 뭉클한 감동', impact: { suspicion: 0, pressure: -2, echo: 5 } },
  { name: '벅차오르는 기쁨', impact: { suspicion: 0, pressure: -4, echo: 3 } },
  { name: '용기 있는 도전', impact: { suspicion: -1, pressure: -1, echo: 4 } },
  { name: '절절한 사랑', impact: { suspicion: 0, pressure: 1, echo: 6 } },
  { name: '서글픈 그리움', impact: { suspicion: 0, pressure: 2, echo: 2 } },
  { name: '소름 돋는 소외감', impact: { suspicion: 3, pressure: 3, echo: 0 } },
  { name: '완벽한 평화', impact: { suspicion: -2, pressure: -3, echo: 1 } },
];
export const generateMoodCard = (): MoodCard => {
  const m = getRandomItem(MOODS);
  return { type: 'mood', id: uid(), name: m.name, baseImpact: m.impact };
};

// ══════════════════════════════════════════════
//  8. SENSE (느낌 - 감각적 강조)
// ══════════════════════════════════════════════
const SENSES = [
  { name: '강렬한 색채', focus: '세상의 모든 빛이 색으로 폭발하는 시각적 풍요로움' },
  { name: '속삭이는 소음', focus: '작은 부스럭거림조차 크게 들리는 예민한 청각적 긴장' },
  { name: '자극적인 냄새', focus: '과거의 기억을 단번에 불러오는 강렬한 후각적 체험' },
  { name: '거친 질감', focus: '피부에 닿는 금속의 차가움이나 나무의 거친 감촉' },
];
export const generateSenseCard = (): SenseCard => {
  const s = getRandomItem(SENSES);
  return { type: 'sense', id: uid(), name: s.name, focus: s.focus, baseImpact: ri() };
};

// ══════════════════════════════════════════════
//  9. AUDIO (소리 - 청각적 무드)
// ══════════════════════════════════════════════
const AUDIOS = [
  { name: '맥박 소리', description: '긴박하게 뛰는 심장 소리가 점점 커지는 긴장감', category: 'ambient' as const },
  { name: '비와 음악', description: '창밖의 빗소리와 나른한 피아노 선율의 조화', category: 'music' as const },
  { name: '날카로운 금속음', description: '기계 장치가 맞물리며 내는 서늘하고 차가운 소음', category: 'ambient' as const },
  { name: '몽환적인 웅얼거림', description: '꿈속을 걷는 듯한 신비롭고 아득한 배경음', category: 'music' as const },
];
export const generateAudioCard = (): AudioCard => {
  const a = getRandomItem(AUDIOS);
  return { type: 'audio', id: uid(), name: a.name, description: a.description, category: a.category, baseImpact: ri() };
};

// ══════════════════════════════════════════════
//  10. PROP (물건 - 서사적 매개체)
// ══════════════════════════════════════════════
const PROPS = [
  { name: '약속의 반지', description: '영원한 사랑을 맹세하며 나누었던 차가운 증표', impact: { suspicion: 0, pressure: 1, echo: 4 } },
  { name: '정성 담긴 선물', description: '누군가에게 전해지지 못한 서글픈 마음의 상자', impact: { suspicion: 0, pressure: -1, echo: 3 } },
  { name: '낡은 회중시계', description: '멈춰버린 시간이 담긴 과거로의 연결 고리', impact: { suspicion: 1, pressure: 0, echo: 2 } },
  { name: '반짝이는 황금 열쇠', description: '금지된 진실을 열 수 있는 유일하고 위험한 도구', impact: { suspicion: 3, pressure: 1, echo: 1 } },
  { name: '도난당한 지도', description: '누군가의 야망이 그려진 복잡한 선들의 기록', impact: { suspicion: 4, pressure: 2, echo: 0 } },
];
export const generatePropCard = (): PropCard => {
  const p = getRandomItem(PROPS);
  return { type: 'prop', id: uid(), name: p.name, description: p.description, baseImpact: p.impact };
};

// ══════════════════════════════════════════════
//  11. CONCEPT (마음 - 보이지 않는 에너지)
// ══════════════════════════════════════════════
const CONCEPTS = [
  { name: '용기', theme: '두려움을 뚫고 나가는 강렬한 의지의 에너지', impact: { suspicion: -1, pressure: -3, echo: 4 } },
  { name: '행복', theme: '모두가 미소 짓게 만드는 따뜻하고 찬란한 빛', impact: { suspicion: -2, pressure: -4, echo: 3 } },
  { name: '사랑', theme: '조건 없이 아끼고 돌보는 세상에서 가장 깊은 마음', impact: { suspicion: 0, pressure: 0, echo: 6 } },
  { name: '희망', theme: '절망의 끝에서 피어나는 작은 꽃 한 송이 같은 기운', impact: { suspicion: 0, pressure: -2, echo: 3 } },
  { name: '믿음', theme: '결코 흔들리지 않는 단단한 마음의 뿌리', impact: { suspicion: -3, pressure: -1, echo: 2 } },
];
export const generateConceptCard = (): ConceptCard => {
  const c = getRandomItem(CONCEPTS);
  return { type: 'concept', id: uid(), name: c.name, theme: c.theme, baseImpact: c.impact };
};

// ══════════════════════════════════════════════
//  12. GUIDE (도움말 - 시나리오 영감)
// ══════════════════════════════════════════════
const ADVICES = [
  "캐릭터가 평소에 하지 않을 의외의 행동을 시켜보세요",
  "침묵 속에서 오고 가는 눈빛의 대화에 집중하세요",
  "감정을 말로 설명하기보다 사소한 행동으로 보여주세요",
  "가장 믿음직한 사람을 의심스럽게 표현해 보세요",
];
const TWISTS = [
  "사실 모든 것은 누군가의 연극이었습니다",
  "캐릭터가 로봇이라는 사실을 본인만 모르고 있습니다",
  "사건의 범인은 이미 죽은 줄 알았던 사람입니다",
  "미래의 자신이 보내온 메시지를 발견합니다",
];
export const generateGuideCard = (): GuideCard => ({
  type: 'guide', id: uid(),
  advice: getRandomItem(ADVICES), twist: getRandomItem(TWISTS), baseImpact: ri(),
});

// ── Table Stats Aggregator ──
export function aggregateTableStats(cards: CardData[]): NarrativeStats {
  return cards.reduce(
    (acc, card) => ({
      suspicion: acc.suspicion + card.baseImpact.suspicion,
      pressure: acc.pressure + card.baseImpact.pressure,
      echo: acc.echo + card.baseImpact.echo,
    }),
    { suspicion: 0, pressure: 0, echo: 0 }
  );
}

// ── Card Type Metadata ──
export interface DeckMeta {
  type: CardType;
  label: string;
  group: string;
  color: string;
}

export const DECK_META: DeckMeta[] = [
  { type: 'character',     label: '캐릭터',   group: '인물',  color: 'bg-purple-600' },
  { type: 'relationship',  label: '관계',     group: '인물',  color: 'bg-pink-500' },
  { type: 'space',         label: '장소',     group: '세계',  color: 'bg-emerald-600' },
  { type: 'timeline',      label: '시간', group: '세계',  color: 'bg-slate-700' },
  { type: 'element',       label: '에너지',     group: '세계',  color: 'bg-orange-500' },
  { type: 'cinematic',     label: '카메라', group: '연출',  color: 'bg-sky-600' },
  { type: 'mood',          label: '기분',   group: '연출',  color: 'bg-indigo-500' },
  { type: 'sense',         label: '느낌',     group: '연출',  color: 'bg-teal-500' },
  { type: 'audio',         label: '소리',     group: '연출',  color: 'bg-violet-500' },
  { type: 'prop',          label: '물건',     group: '서사',  color: 'bg-amber-600' },
  { type: 'concept',       label: '마음',     group: '서사',  color: 'bg-rose-600' },
  { type: 'guide',         label: '도움말',   group: '서사',  color: 'bg-yellow-600' },
];

export function generateCard(type: CardType): CardData {
  switch (type) {
    case 'character': return generateCharacterCard();
    case 'relationship': return generateRelationshipCard();
    case 'space': return generateSpaceCard();
    case 'timeline': return generateTimelineCard();
    case 'element': return generateElementCard();
    case 'cinematic': return generateCinematicCard();
    case 'mood': return generateMoodCard();
    case 'sense': return generateSenseCard();
    case 'audio': return generateAudioCard();
    case 'prop': return generatePropCard();
    case 'concept': return generateConceptCard();
    case 'guide': return generateGuideCard();
  }
}
