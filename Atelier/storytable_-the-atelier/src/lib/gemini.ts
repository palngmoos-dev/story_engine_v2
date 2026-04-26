import { CardData, Mode, GeneratedStory, NarrativeStats } from "../types";
import { aggregateTableStats } from "../constants";
import { GoogleGenAI } from "@google/genai";

const apiKey = import.meta.env.VITE_GEMINI_API_KEY;
const ai = new GoogleGenAI({ apiKey: apiKey || "" });

const OLLAMA_URL = "/api/ollama";
const GEMMA_MODEL = "gemma4:e2b";

function describeCard(card: CardData): string {
  switch (card.type) {
    case 'character':
      return `[캐릭터] 성명:${card.name}, 직업:${card.job}, 나이:${card.age}, 비밀:${card.secret}`;
    default:
      return `[${card.type}] ${(card as any).name || (card as any).era || "정보없음"}`;
  }
}

async function fuseWithGemma(prompt: string, systemPrompt: string, stats: NarrativeStats): Promise<GeneratedStory> {
  const response = await fetch(OLLAMA_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model: GEMMA_MODEL,
      system: systemPrompt,
      prompt: prompt,
      stream: false
    })
  });
  if (!response.ok) throw new Error(`Ollama Error: ${response.status}`);
  const data = await response.json();
  const text = data.response;
  const jsonMatch = text.match(/\{[\s\S]*\}/);
  if (!jsonMatch) throw new Error("Gemma 응답 파싱 실패");
  const parsed = JSON.parse(jsonMatch[0]) as GeneratedStory;
  parsed.aggregateStats = stats;
  return parsed;
}

async function fuseWithGemini(prompt: string, stats: NarrativeStats, modelNames: string[]): Promise<GeneratedStory> {
  const currentModel = modelNames[0];
  if (!currentModel) throw new Error("모든 AI 모델의 사용량이 초과되었습니다. 잠시 후 다시 시도해 주세요.");

  try {
    const response = await ai.models.generateContent({
      model: currentModel,
      contents: [{ role: "user", parts: [{ text: prompt }] }]
    });
    
    const text = response.text;
    const jsonMatch = text.match(/\{[\s\S]*\}/);
    if (!jsonMatch) throw new Error(`${currentModel} 응답 파싱 실패`);
    
    const parsed = JSON.parse(jsonMatch[0]) as GeneratedStory;
    parsed.aggregateStats = stats;
    return parsed;
  } catch (error: any) {
    // 429(할당량 초과) 또는 404(모델 없음) 시 다음 모델로 전환
    if (error?.message?.includes("429") || error?.message?.includes("404")) {
      console.warn(`${currentModel} failed, trying next fallback...`);
      return await fuseWithGemini(prompt, stats, modelNames.slice(1));
    }
    throw error;
  }
}

export async function fuseStory(cards: CardData[], mode: Mode): Promise<GeneratedStory> {
  const stats = aggregateTableStats(cards);
  const cardText = cards.map(describeCard).join('\n');
  const systemPrompt = `시네마틱 작가로서 한국어 JSON 스토리보드를 작성하세요.`;
  const fullPrompt = `${systemPrompt}\n\n카드:\n${cardText}\n\nJSON 형식으로만 답하세요.`;

  try {
    // 1. Gemma 우선 시도
    return await fuseWithGemma(fullPrompt, systemPrompt, stats);
  } catch (gemmaError) {
    // 2. Gemini 폴백 체인 (2.0 -> 2.0 Lite -> 1.5 Flash)
    const geminiModels = ["gemini-2.0-flash-001", "gemini-2.0-flash-lite-001", "gemini-1.5-flash"];
    return await fuseWithGemini(fullPrompt, stats, geminiModels);
  }
}
