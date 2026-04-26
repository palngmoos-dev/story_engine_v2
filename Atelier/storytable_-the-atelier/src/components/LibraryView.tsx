import { motion, AnimatePresence } from "motion/react";
import { GeneratedStory } from "../types";
import { Trash2, Calendar, BookOpen, BrainCircuit, ExternalLink } from "lucide-react";

interface LibraryViewProps {
  stories: GeneratedStory[];
  onDelete: (id: string) => void;
  onView: (story: GeneratedStory) => void;
  loading: boolean;
}

export default function LibraryView({ stories, onDelete, onView, loading }: LibraryViewProps) {
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-32 gap-4">
        <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin" />
        <p className="font-serif text-xl font-bold text-primary italic">라이브러리를 불러오는 중...</p>
      </div>
    );
  }

  if (stories.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-32 text-center">
        <div className="w-24 h-24 bg-slate-100 rounded-[40px] flex items-center justify-center text-slate-300 mb-6">
          <BookOpen size={48} />
        </div>
        <h3 className="font-serif text-2xl font-bold text-slate-800 mb-2">아직 저장된 스토리가 없습니다.</h3>
        <p className="text-on-surface-variant max-w-md mx-auto">
          스튜디오에서 새로운 시나리오를 융합하고 라이브러리에 소장해 보세요.
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
      <AnimatePresence mode="popLayout">
        {stories.map((story) => (
          <motion.div
            key={story.id}
            layout
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9 }}
            className="group relative bg-surface rounded-[32px] overflow-hidden card-shadow border border-slate-100 hover:border-primary/20 transition-all flex flex-col"
          >
            <div className={`h-2 text-white ${story.mode === 'expert' ? 'bg-slate-900' : 'bg-primary'}`} />
            
            <div className="p-8 flex flex-col flex-grow">
              <div className="flex justify-between items-start mb-4">
                <div className="flex items-center gap-2 px-3 py-1 bg-slate-100 rounded-full text-[10px] font-bold uppercase tracking-widest text-slate-500">
                  {story.mode === 'expert' ? <BrainCircuit size={12} /> : <BookOpen size={12} />}
                  <span>{story.mode === 'expert' ? '전문가' : '초보자'}</span>
                </div>
                <div className="flex items-center gap-1 text-[10px] text-slate-400 font-bold">
                  <Calendar size={12} />
                  <span>{story.createdAt?.toDate ? new Intl.DateTimeFormat('ko-KR').format(story.createdAt.toDate()) : '오늘'}</span>
                </div>
              </div>

              <h3 className="font-serif text-2xl font-bold text-slate-800 mb-3 group-hover:text-primary transition-colors">
                {story.title}
              </h3>
              <p className="text-sm text-on-surface-variant line-clamp-3 mb-6 italic">
                "{story.logline}"
              </p>

              <div className="mt-auto flex items-center justify-between">
                <button
                  onClick={() => onView(story)}
                  className="flex items-center gap-2 text-primary font-bold text-sm hover:underline"
                >
                  상세 보기 <ExternalLink size={14} />
                </button>
                <button
                  onClick={() => story.id && onDelete(story.id)}
                  className="p-2 text-slate-300 hover:text-red-500 hover:bg-red-50 rounded-full transition-all"
                  title="삭제하기"
                >
                  <Trash2 size={18} />
                </button>
              </div>
            </div>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}
