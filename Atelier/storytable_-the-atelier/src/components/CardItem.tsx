import React from "react";
import { motion } from "motion/react";
import { CardData, NarrativeStats, CharacterCard } from "../types";
import { User, Heart, MapPin, Clock, Flame, Film, CloudRain, Eye as EyeIcon, Music, Package, Lightbulb, HelpCircle, X, Edit2, Shield, Waves } from "lucide-react";

interface CardItemProps {
  card: CardData;
  onRemove?: () => void;
  onUpdate?: (id: string, updates: Partial<CardData>) => void;
  onEdit?: (card: CardData) => void;
}

function StatsBar({ stats }: { stats: NarrativeStats }) {
  const max = 5;
  const items = [
    { key: 'S', value: stats.suspicion, color: 'bg-amber-400', icon: <EyeIcon size={10} /> },
    { key: 'P', value: stats.pressure, color: 'bg-red-400', icon: <Shield size={10} /> },
    { key: 'E', value: stats.echo, color: 'bg-blue-400', icon: <Waves size={10} /> },
  ];
  return (
    <div className="flex items-center gap-2 mt-2 pt-2 border-t border-slate-100">
      {items.map(item => (
        <div key={item.key} className="flex items-center gap-1" title={`${item.key}: ${item.value}`}>
          <span className="text-slate-400">{item.icon}</span>
          <div className="w-8 h-1 bg-slate-200 rounded-full overflow-hidden">
            <div className={`h-full ${item.color} rounded-full`} style={{ width: `${Math.min((item.value / max) * 100, 100)}%` }} />
          </div>
        </div>
      ))}
    </div>
  );
}

const CARD_CONFIG: Record<string, { icon: React.ReactNode; label: string; headerColor: string; glowColor: string }> = {
  character:    { icon: <User size={18} />,        label: '캐릭터',   headerColor: 'bg-purple-600',  glowColor: 'shadow-[0_0_20px_rgba(147,51,234,0.1)] hover:shadow-[0_0_30px_rgba(147,51,234,0.25)]' },
  relationship: { icon: <Heart size={18} />,       label: '관계',     headerColor: 'bg-pink-500',    glowColor: 'shadow-[0_0_20px_rgba(236,72,153,0.1)] hover:shadow-[0_0_30px_rgba(236,72,153,0.25)]' },
  space:        { icon: <MapPin size={18} />,      label: '장소',     headerColor: 'bg-emerald-600', glowColor: 'shadow-[0_0_20px_rgba(5,150,105,0.1)] hover:shadow-[0_0_30px_rgba(5,150,105,0.25)]' },
  timeline:     { icon: <Clock size={18} />,       label: '시간',     headerColor: 'bg-slate-700',   glowColor: 'shadow-[0_0_20px_rgba(51,65,85,0.1)] hover:shadow-[0_0_30px_rgba(51,65,85,0.25)]' },
  element:      { icon: <Flame size={18} />,       label: '에너지',   headerColor: 'bg-orange-500',  glowColor: 'shadow-[0_0_20px_rgba(249,115,22,0.1)] hover:shadow-[0_0_30px_rgba(249,115,22,0.25)]' },
  cinematic:    { icon: <Film size={18} />,        label: '카메라',   headerColor: 'bg-sky-600',     glowColor: 'shadow-[0_0_20px_rgba(2,132,199,0.1)] hover:shadow-[0_0_30px_rgba(2,132,199,0.25)]' },
  mood:         { icon: <CloudRain size={18} />,   label: '기분',     headerColor: 'bg-indigo-500',  glowColor: 'shadow-[0_0_20px_rgba(99,102,241,0.1)] hover:shadow-[0_0_30px_rgba(99,102,241,0.25)]' },
  sense:        { icon: <EyeIcon size={18} />,     label: '느낌',     headerColor: 'bg-teal-500',    glowColor: 'shadow-[0_0_20px_rgba(20,184,166,0.1)] hover:shadow-[0_0_30px_rgba(20,184,166,0.25)]' },
  audio:        { icon: <Music size={18} />,       label: '소리',     headerColor: 'bg-violet-500',  glowColor: 'shadow-[0_0_20px_rgba(139,92,246,0.1)] hover:shadow-[0_0_30px_rgba(139,92,246,0.25)]' },
  prop:         { icon: <Package size={18} />,     label: '물건',     headerColor: 'bg-amber-600',   glowColor: 'shadow-[0_0_20px_rgba(217,119,6,0.1)] hover:shadow-[0_0_30px_rgba(217,119,6,0.25)]' },
  concept:      { icon: <Lightbulb size={18} />,   label: '마음',     headerColor: 'bg-rose-600',    glowColor: 'shadow-[0_0_20px_rgba(225,29,72,0.1)] hover:shadow-[0_0_30px_rgba(225,29,72,0.25)]' },
  guide:        { icon: <HelpCircle size={18} />,  label: '도움말',   headerColor: 'bg-yellow-600',  glowColor: 'shadow-[0_0_20px_rgba(202,138,4,0.1)] hover:shadow-[0_0_30px_rgba(202,138,4,0.25)]' },
};

function CardBody({ card }: { card: CardData }) {
  switch (card.type) {
    case 'character': {
      const c = card as CharacterCard;
      const themeColor = c.gender === 'female' ? 'text-pink-600' : 'text-purple-600';
      return (
        <div className="space-y-3 text-[11px] text-on-surface-variant leading-relaxed">
          <div className="flex items-start justify-between border-b border-slate-100 pb-2">
            <div className="flex flex-col">
              <h3 className="font-serif text-lg font-black text-slate-900 leading-none">{c.name}</h3>
              <span className={`text-[10px] font-bold mt-1 uppercase tracking-wider ${themeColor}`}>{c.job}</span>
            </div>
            <div className="flex flex-col items-end">
              <span className="text-[14px] font-serif font-black text-slate-400 leading-none">{c.age}세</span>
              <span className="text-[9px] font-bold text-slate-300 mt-0.5">{c.bloodType} / {c.mbti}</span>
            </div>
          </div>
          <div className="grid grid-cols-1 gap-1">
            <div className="flex gap-2"><span className="min-w-[45px] text-[8px] font-black text-slate-400">UPBRING</span><span className="font-bold text-slate-700">{c.upbringing}</span></div>
            <div className="flex gap-2"><span className="min-w-[45px] text-[8px] font-black text-slate-400">RELATIONS</span><span className="font-bold text-slate-700">{c.relationshipDesc}</span></div>
            <div className="flex gap-2"><span className="min-w-[45px] text-[8px] font-black text-slate-400">HOBBIES</span><span className="font-bold text-blue-600">{c.hobbies}</span></div>
          </div>
          <p className="text-[10px] italic text-slate-400 border-l-2 border-slate-100 pl-2">"{c.secret}"</p>
          <div className="flex items-center justify-between">
             <span className={`text-[9px] font-black px-2 py-0.5 rounded-full border ${c.gender === 'female' ? 'bg-pink-50 text-pink-600 border-pink-100' : 'bg-purple-50 text-purple-600 border-purple-100'}`}>LV.{c.level}</span>
             <StatsBar stats={card.baseImpact} />
          </div>
        </div>
      );
    }
    case 'relationship': return (
      <div className="space-y-2 text-[12px]">
        <h3 className="font-serif text-lg font-bold text-pink-600">{(card as any).name}</h3>
        <p className="text-on-surface-variant leading-relaxed italic border-l-2 border-pink-200 pl-2">{(card as any).description}</p>
        <StatsBar stats={card.baseImpact} />
      </div>
    );
    case 'space': return (
      <div className="space-y-2 text-[12px]">
        <h3 className="font-serif text-base font-bold text-emerald-700">{(card as any).name}</h3>
        <p className="text-on-surface-variant leading-relaxed text-[11px]">{(card as any).description}</p>
        <StatsBar stats={card.baseImpact} />
      </div>
    );
    default: return (
      <div className="space-y-2 text-[12px]">
        <h3 className="font-serif text-base font-bold text-slate-800">{(card as any).name || (card as any).era}</h3>
        <p className="text-on-surface-variant italic text-[11px]">{(card as any).description || (card as any).theme || (card as any).focus || (card as any).aesthetic}</p>
        <StatsBar stats={card.baseImpact} />
      </div>
    );
  }
}

export const CardItem: React.FC<CardItemProps & { dragConstraints?: React.RefObject<any> }> = ({ card, onRemove, onEdit, dragConstraints }) => {
  const config = CARD_CONFIG[card.type] || CARD_CONFIG.guide;
  const isChar = card.type === 'character';
  const char = card as CharacterCard;
  
  const headerColor = isChar && char.gender === 'female' ? 'bg-pink-500' : config.headerColor;
  const glowColor = isChar && char.gender === 'female' 
    ? 'shadow-[0_0_20px_rgba(236,72,153,0.1)] hover:shadow-[0_0_30px_rgba(236,72,153,0.25)]' 
    : config.glowColor;

  return (
    <motion.div
      drag
      dragConstraints={dragConstraints}
      dragMomentum={false}
      dragElastic={0.1}
      whileDrag={{ scale: 1.05, zIndex: 100, cursor: 'grabbing' }}
      initial={{ opacity: 0, y: 20, scale: 0.9 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, scale: 0.8 }}
      className={`relative w-64 bg-surface rounded-2xl overflow-hidden border border-outline-variant transition-shadow duration-300 cursor-grab ${glowColor}`}
    >
      {/* Card Header */}
      <div className={`p-3 text-on-primary flex items-center justify-between ${headerColor}`}>
        <div className="flex items-center gap-2">
          {config.icon}
          <span className="font-serif text-sm font-bold tracking-tight">{config.label}</span>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={(e) => { e.stopPropagation(); onEdit?.(card); }}
            className="p-1.5 bg-white/10 hover:bg-white/30 text-amber-300 rounded-full transition-all shadow-sm"
            title="편집하기"
          >
            <Edit2 size={16} fill="currentColor" />
          </button>
          <button
            onClick={(e) => { e.stopPropagation(); onRemove?.(); }}
            className="p-1.5 bg-white/10 hover:bg-white/30 text-white rounded-full transition-all shadow-sm"
          >
            <X size={16} />
          </button>
        </div>
      </div>

      {/* Card Content */}
      <div className="p-4 bg-white/40 backdrop-blur-sm min-h-[160px]">
        <CardBody card={card} />
      </div>

      {/* ID Badge */}
      <div className="px-3 py-1 bg-slate-50/50 border-t border-outline-variant flex justify-center">
        <span className="font-mono text-[8px] text-slate-300 uppercase tracking-widest">ID: {card.id}</span>
      </div>
    </motion.div>
  );
};

export default CardItem;
