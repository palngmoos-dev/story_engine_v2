import React from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { X, Check, Trash2, User, Heart, MapPin, Clock, Flame, Film, CloudRain, Eye, Music, Package, Lightbulb, HelpCircle } from 'lucide-react';
import { CardData, CharacterCard, RelationshipCard, SpaceCard, TimelineCard, ElementCard, CinematicCard, MoodCard, SenseCard, AudioCard, PropCard, ConceptCard, GuideCard } from '../types';

interface CardEditorProps {
  card: CardData | null;
  isOpen: boolean;
  onClose: () => void;
  onUpdate: (id: string, updates: Partial<CardData>) => void;
  onRemove: (id: string) => void;
}

export default function CardEditor({ card, isOpen, onClose, onUpdate, onRemove }: CardEditorProps) {
  if (!card) return null;

  const handleChange = (field: string, value: any) => {
    onUpdate(card.id, { [field]: value });
  };

  const renderFields = () => {
    switch (card.type) {
      case 'character': {
        const c = card as CharacterCard;
        return (
          <div className="space-y-4">
             <div className="grid grid-cols-2 gap-4">
                <Field label="성함" value={c.name} onChange={v => handleChange('name', v)} />
                <Field label="직업" value={c.job} onChange={v => handleChange('job', v)} />
                <Field label="나이" value={c.age} onChange={v => handleChange('age', v)} />
                <Field label="성별" value={c.gender} type="select" options={['male', 'female']} onChange={v => handleChange('gender', v)} />
                <Field label="혈액형" value={c.bloodType} onChange={v => handleChange('bloodType', v)} />
                <Field label="MBTI" value={c.mbti} onChange={v => handleChange('mbti', v)} />
             </div>
             <Field label="성장 배경" value={c.upbringing} type="textarea" onChange={v => handleChange('upbringing', v)} />
             <Field label="인간 관계" value={c.relationshipDesc} type="textarea" onChange={v => handleChange('relationshipDesc', v)} />
             <Field label="취미" value={c.hobbies} onChange={v => handleChange('hobbies', v)} />
             <Field label="특기" value={c.skill} onChange={v => handleChange('skill', v)} />
             <Field label="소유 차량" value={c.car} onChange={v => handleChange('car', v)} />
             <Field label="치명적 결함" value={c.flaw} onChange={v => handleChange('flaw', v)} />
             <Field label="숨겨진 비밀" value={c.secret} type="textarea" onChange={v => handleChange('secret', v)} />
          </div>
        );
      }
      case 'relationship': {
        const r = card as RelationshipCard;
        return (
          <div className="space-y-4">
            <Field label="관계 명칭" value={r.name} onChange={v => handleChange('name', v)} />
            <Field label="상세 설명" value={r.description} type="textarea" onChange={v => handleChange('description', v)} />
          </div>
        );
      }
      case 'space': {
        const s = card as SpaceCard;
        return (
          <div className="space-y-4">
            <Field label="장소 이름" value={s.name} onChange={v => handleChange('name', v)} />
            <Field label="시각적 묘사" value={s.description} type="textarea" onChange={v => handleChange('description', v)} />
            <Field label="보정 효과" value={s.modifiers} onChange={v => handleChange('modifiers', v)} />
          </div>
        );
      }
      case 'timeline': {
        const t = card as TimelineCard;
        return (
          <div className="space-y-4">
            <Field label="시대적 배경" value={t.era} onChange={v => handleChange('era', v)} />
            <Field label="분위기/무드" value={t.vibe} onChange={v => handleChange('vibe', v)} />
            <Field label="미학적 특징" value={t.chronosAesthetic} type="textarea" onChange={v => handleChange('chronosAesthetic', v)} />
          </div>
        );
      }
      case 'cinematic': {
        const ci = card as CinematicCard;
        return (
          <div className="space-y-4">
            <Field label="연출 기법" value={ci.name} onChange={v => handleChange('name', v)} />
            <Field label="시각적 느낌" value={ci.description} type="textarea" onChange={v => handleChange('description', v)} />
          </div>
        );
      }
      default:
        return (
          <div className="space-y-4">
            <Field label="명칭" value={(card as any).name || (card as any).era || ""} onChange={v => handleChange('name', v)} />
            <Field label="설명/테마" value={(card as any).description || (card as any).theme || (card as any).focus || ""} type="textarea" onChange={v => handleChange('description', v)} />
          </div>
        );
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/20 backdrop-blur-sm z-[100]"
          />
          
          {/* Side Panel */}
          <motion.div
            initial={{ x: '-100%' }}
            animate={{ x: 0 }}
            exit={{ x: '-100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            className="fixed left-0 top-0 bottom-0 w-[450px] bg-white shadow-2xl z-[101] flex flex-col border-r border-slate-200"
          >
            {/* Header */}
            <div className="p-6 border-b border-slate-100 flex items-center justify-between bg-slate-50">
              <div className="flex items-center gap-3">
                 <div className="p-2 bg-purple-100 text-purple-600 rounded-xl">
                    <EditIcon type={card.type} />
                 </div>
                 <div>
                    <h2 className="font-serif text-xl font-bold text-slate-800">카드 조각하기</h2>
                    <p className="text-[10px] text-slate-400 font-bold uppercase tracking-widest">Editor — ID: {card.id}</p>
                 </div>
              </div>
              <button onClick={onClose} className="p-2 hover:bg-slate-200 rounded-full transition-colors">
                <X size={20} className="text-slate-400" />
              </button>
            </div>

            {/* Content Area */}
            <div className="flex-grow overflow-y-auto p-8 custom-scrollbar">
               {renderFields()}
               
               {/* Impact Stats Editor */}
               <div className="mt-10 pt-6 border-t border-slate-100">
                  <h3 className="text-xs font-black text-slate-400 uppercase tracking-widest mb-4">서사적 영향력 (Stats)</h3>
                  <div className="grid grid-cols-3 gap-4">
                     <StatField label="의심" value={card.baseImpact.suspicion} onChange={v => onUpdate(card.id, { baseImpact: { ...card.baseImpact, suspicion: v } })} color="text-amber-500" />
                     <StatField label="압박" value={card.baseImpact.pressure} onChange={v => onUpdate(card.id, { baseImpact: { ...card.baseImpact, pressure: v } })} color="text-red-500" />
                     <StatField label="공명" value={card.baseImpact.echo} onChange={v => onUpdate(card.id, { baseImpact: { ...card.baseImpact, echo: v } })} color="text-blue-500" />
                  </div>
               </div>
            </div>

            {/* Footer */}
            <div className="p-6 border-t border-slate-100 bg-slate-50 flex items-center justify-between">
               <button 
                 onClick={() => { onRemove(card.id); onClose(); }}
                 className="flex items-center gap-2 px-4 py-2 text-red-500 hover:bg-red-50 rounded-xl transition-all text-sm font-bold"
               >
                 <Trash2 size={16} /> 카드 파기
               </button>
               <button 
                 onClick={onClose}
                 className="flex items-center gap-2 px-8 py-2 bg-slate-800 text-white rounded-xl hover:bg-slate-900 transition-all text-sm font-bold shadow-lg"
               >
                 <Check size={16} /> 조각 완료
               </button>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

function Field({ label, value, onChange, type = 'text', options = [] }: { label: string, value: any, onChange: (v: any) => void, type?: 'text' | 'textarea' | 'select', options?: string[] }) {
  // 입력창 자체의 로컬 상태 관리 (연속 지우기 시 에러 방지)
  const [localValue, setLocalValue] = React.useState(value);

  // 외부(카드 데이터)가 바뀌면 로컬 값도 동기화
  React.useEffect(() => {
    setLocalValue(value);
  }, [value]);

  const handleBlur = () => {
    if (localValue !== value) {
      onChange(localValue);
    }
  };

  return (
    <div className="flex flex-col gap-1.5">
      <label className="text-[10px] font-black text-slate-400 uppercase tracking-wider ml-1">{label}</label>
      {type === 'textarea' ? (
        <textarea 
          className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-700 outline-none focus:border-purple-300 transition-all min-h-[80px] resize-none"
          value={localValue || ""}
          onChange={e => setLocalValue(e.target.value)}
          onBlur={handleBlur}
        />
      ) : type === 'select' ? (
        <select 
          className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-700 outline-none focus:border-purple-300 transition-all appearance-none cursor-pointer"
          value={localValue}
          onChange={e => {
            setLocalValue(e.target.value);
            onChange(e.target.value); // Select는 즉시 반영이 자연스러움
          }}
        >
          {options.map(opt => <option key={opt} value={opt}>{opt === 'male' ? '남성' : opt === 'female' ? '여성' : opt}</option>)}
        </select>
      ) : (
        <input 
          className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-700 outline-none focus:border-purple-300 transition-all"
          value={localValue || ""}
          onChange={e => setLocalValue(e.target.value)}
          onBlur={handleBlur}
          onKeyDown={e => {
            if (e.key === 'Enter') handleBlur();
          }}
        />
      )}
    </div>
  );
}

function StatField({ label, value, onChange, color }: { label: string, value: number, onChange: (v: number) => void, color: string }) {
  return (
    <div className="flex flex-col items-center gap-2 p-3 bg-white border border-slate-100 rounded-2xl shadow-sm">
       <span className={`text-[10px] font-black ${color}`}>{label}</span>
       <input 
         type="number" 
         min="-5" max="10"
         className="w-12 text-center text-lg font-serif font-black text-slate-800 outline-none"
         value={value}
         onChange={e => onChange(parseInt(e.target.value) || 0)}
       />
    </div>
  );
}

function EditIcon({ type }: { type: string }) {
  const size = 20;
  switch (type) {
    case 'character': return <User size={size} />;
    case 'relationship': return <Heart size={size} />;
    case 'space': return <MapPin size={size} />;
    case 'timeline': return <Clock size={size} />;
    case 'element': return <Flame size={size} />;
    case 'cinematic': return <Film size={size} />;
    case 'mood': return <CloudRain size={size} />;
    case 'sense': return <Eye size={size} />;
    case 'audio': return <Music size={size} />;
    case 'prop': return <Package size={size} />;
    case 'concept': return <Lightbulb size={size} />;
    case 'guide': return <HelpCircle size={size} />;
    default: return <Package size={size} />;
  }
}
