import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "motion/react";
import { GeneratedStory, Mode } from "../types";
import { Sparkles, ArrowRight, Video, FileText, Layout, Lightbulb, X, Bookmark, BookmarkCheck, Edit2, Check, Copy, Music, Star, Film, Stethoscope } from "lucide-react";

interface FusionResultProps {
  story: GeneratedStory | null;
  loading: boolean;
  onClose: () => void;
  mode: Mode;
  onSave?: (story: GeneratedStory) => Promise<void>;
  isSaved?: boolean;
}

type Tab = 'narrative' | 'conti' | 'bgm' | 'review';

function StarRating({ stars }: { stars: number }) {
  return (
    <div className="flex items-center gap-1">
      {[1, 2, 3, 4, 5].map(i => (
        <Star
          key={i}
          size={20}
          className={i <= stars ? 'text-amber-400' : 'text-slate-200'}
          fill={i <= stars ? 'currentColor' : 'none'}
        />
      ))}
      <span className="ml-2 text-sm font-bold text-slate-600">{stars}/5</span>
    </div>
  );
}

export default function FusionResult({ story, loading, onClose, mode, onSave, isSaved: initiallySaved }: FusionResultProps) {
  const [isSaved, setIsSaved] = useState(initiallySaved || false);
  const [saving, setSaving] = useState(false);
  const [copied, setCopied] = useState(false);
  const [activeTab, setActiveTab] = useState<Tab>('narrative');

  const [editedTitle, setEditedTitle] = useState("");
  const [tempTitle, setTempTitle] = useState("");
  const [isEditing, setIsEditing] = useState(false);

  const [editedLogline, setEditedLogline] = useState("");
  const [tempLogline, setTempLogline] = useState("");
  const [isEditingLogline, setIsEditingLogline] = useState(false);

  const [editedSynopsis, setEditedSynopsis] = useState("");
  const [tempSynopsis, setTempSynopsis] = useState("");
  const [isEditingSynopsis, setIsEditingSynopsis] = useState(false);

  useEffect(() => {
    if (story) {
      setEditedTitle(story.title);
      setTempTitle(story.title);
      setEditedLogline(story.logline);
      setTempLogline(story.logline);
      setEditedSynopsis(story.synopsis);
      setTempSynopsis(story.synopsis);
      setIsSaved(initiallySaved || false);
      setActiveTab('narrative');
    }
  }, [story, initiallySaved]);

  if (!loading && !story) return null;

  const handleSave = async () => {
    if (!story || !onSave) return;
    setSaving(true);
    try {
      await onSave({ ...story, title: editedTitle, logline: editedLogline, synopsis: editedSynopsis });
      setIsSaved(true);
    } catch { alert("저장에 실패했습니다."); }
    finally { setSaving(false); }
  };

  const handleCopy = () => {
    if (!story) return;
    const text = [
      `제목: ${editedTitle}`,
      `로그라인: ${editedLogline}`,
      `시놉시스:\n${editedSynopsis}`,
      `주요 씬:\n${story.scenes.map((s, i) => `장면 ${i+1}: ${s.title}\n${s.description}`).join('\n\n')}`,
      story.bgmRecommendation ? `BGM 추천:\n${story.bgmRecommendation}` : '',
      story.directorReview ? `디렉터 리뷰 (★${story.directorReview.stars}/5):\n${story.directorReview.critique}\n처방: ${story.directorReview.diagnosis}` : '',
    ].filter(Boolean).join('\n\n');
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const hasChanges = story && (editedTitle !== story.title || editedLogline !== story.logline || editedSynopsis !== story.synopsis);
  const canSave = !loading && onSave && (!isSaved || hasChanges);

  const tabs: { id: Tab; label: string; icon: React.ReactNode }[] = [
    { id: 'narrative', label: '서사', icon: <FileText size={14} /> },
    { id: 'conti',     label: '콘티', icon: <Film size={14} /> },
    { id: 'bgm',       label: 'BGM',  icon: <Music size={14} /> },
    { id: 'review',    label: '리뷰', icon: <Stethoscope size={14} /> },
  ];

  const headerBg = mode === 'beginner' ? 'bg-primary text-white' : 'bg-slate-900 text-white';

  return (
    <AnimatePresence>
      {(loading || story) && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-[100] flex items-center justify-center p-4 md:p-8 bg-primary/20 backdrop-blur-md"
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0, y: 40 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.9, opacity: 0, y: 40 }}
            className="w-full max-w-4xl max-h-[90vh] bg-background rounded-[40px] shadow-2xl overflow-hidden flex flex-col relative"
          >
            {/* Header */}
            <div className={`p-6 ${headerBg} flex justify-between items-start`}>
              <div className="flex items-center gap-3 flex-grow mr-4">
                <div className="p-2.5 bg-white/20 rounded-2xl shrink-0">
                  <Sparkles className="animate-pulse" size={20} />
                </div>
                <div className="flex-grow min-w-0">
                  <span className="text-[10px] font-bold uppercase tracking-[0.2em] opacity-70">
                    {mode === 'beginner' ? "선생님의 스토리보드" : "수석 디렉터 시나리오"}
                  </span>
                  <div className="flex items-center gap-2 group">
                    {isEditing ? (
                      <div className="flex items-center gap-2 w-full max-w-xl">
                        <input
                          autoFocus type="text" value={tempTitle}
                          onChange={e => setTempTitle(e.target.value)}
                          onKeyDown={e => { if (e.key === 'Enter') { setEditedTitle(tempTitle); setIsEditing(false); } if (e.key === 'Escape') setIsEditing(false); }}
                          className="bg-white/10 border-b-2 border-white/50 outline-none font-serif text-2xl font-bold tracking-tight w-full px-1"
                        />
                        <button onClick={() => { setEditedTitle(tempTitle); setIsEditing(false); }} className="p-1.5 bg-white/20 hover:bg-white/40 rounded-full"><Check size={16} /></button>
                        <button onClick={() => setIsEditing(false)} className="p-1.5 hover:bg-white/20 rounded-full"><X size={16} /></button>
                      </div>
                    ) : (
                      <>
                        <h2 onClick={() => !loading && setIsEditing(true)} className="font-serif text-2xl font-bold tracking-tight truncate cursor-pointer hover:opacity-80">
                          {loading ? "이야기를 조각하는 중..." : editedTitle}
                        </h2>
                        {!loading && <button onClick={() => setIsEditing(true)} className="opacity-0 group-hover:opacity-100 p-1 hover:bg-white/20 rounded-full transition-all"><Edit2 size={14} /></button>}
                      </>
                    )}
                  </div>
                  {/* Aggregate Stats */}
                  {story?.aggregateStats && (
                    <div className="flex items-center gap-3 mt-1 opacity-70">
                      <span className="text-[10px]">👁 {story.aggregateStats.suspicion}</span>
                      <span className="text-[10px]">🛡 {story.aggregateStats.pressure}</span>
                      <span className="text-[10px]">🌊 {story.aggregateStats.echo}</span>
                    </div>
                  )}
                </div>
              </div>
              <div className="flex gap-2 shrink-0">
                {onSave && !loading && (
                  <button onClick={handleSave} disabled={saving || !canSave}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full font-bold text-xs transition-all ${isSaved && !hasChanges ? 'bg-secondary text-white' : 'bg-white/20 hover:bg-white/40 text-white'}`}>
                    {isSaved && !hasChanges ? <BookmarkCheck size={14} /> : <Bookmark size={14} />}
                    {isSaved && !hasChanges ? "저장됨" : hasChanges ? "수정 저장" : "저장"}
                  </button>
                )}
                {!loading && (
                  <button onClick={handleCopy} className="flex items-center gap-1.5 px-3 py-1.5 bg-white/20 hover:bg-white/40 text-white rounded-full font-bold text-xs transition-all">
                    {copied ? <Check size={14} /> : <Copy size={14} />}
                    {copied ? "복사됨" : "복사"}
                  </button>
                )}
                <button onClick={onClose} className="p-1.5 hover:bg-white/20 rounded-full transition-colors"><X size={20} /></button>
              </div>
            </div>

            {/* Tabs */}
            {!loading && story && (
              <div className="flex items-center gap-1 px-6 pt-4 pb-0 border-b border-slate-100 bg-background">
                {tabs.map(tab => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex items-center gap-1.5 px-4 py-2 rounded-t-xl text-xs font-bold transition-all ${
                      activeTab === tab.id
                        ? 'bg-primary/10 text-primary border-b-2 border-primary'
                        : 'text-slate-400 hover:text-slate-600'
                    }`}
                  >
                    {tab.icon}{tab.label}
                  </button>
                ))}
              </div>
            )}

            {/* Content */}
            <div className="flex-grow overflow-y-auto p-6 md:p-10 workshop-grain">
              {loading ? (
                <div className="flex flex-col items-center justify-center h-64 gap-4">
                  <div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin" />
                  <div className="text-center">
                    <p className="font-serif text-xl font-bold text-primary italic">"잠시만요, 이야기꾼이 구상 중입니다..."</p>
                    <p className="text-sm text-on-surface-variant mt-2">카드들의 에너지를 융합하여 걸작을 빚고 있습니다.</p>
                  </div>
                </div>
              ) : story && (
                <AnimatePresence mode="wait">
                  {/* ── NARRATIVE TAB ── */}
                  {activeTab === 'narrative' && (
                    <motion.div key="narrative" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="space-y-12 max-w-3xl mx-auto">
                      {/* Logline */}
                      <section className="text-center space-y-4">
                        <div className="inline-flex items-center gap-2 px-4 py-1.5 bg-secondary/5 text-secondary border border-secondary/10 rounded-full text-[10px] font-bold uppercase tracking-[0.3em]">
                          <Layout size={12} /><span>로그라인 (Logline)</span>
                        </div>
                        <div className="relative px-6">
                          <span className="absolute -top-4 -left-2 text-5xl text-primary/10 font-serif">"</span>
                          {isEditingLogline ? (
                            <div className="flex flex-col items-center gap-3">
                              <textarea autoFocus value={tempLogline} onChange={e => setTempLogline(e.target.value)}
                                className="w-full bg-white/40 border-2 border-primary/20 rounded-2xl p-4 font-serif text-xl font-bold text-center italic text-slate-800 focus:border-primary/50 outline-none resize-none" rows={3} />
                              <div className="flex gap-2">
                                <button onClick={() => { setEditedLogline(tempLogline); setIsEditingLogline(false); }} className="flex items-center gap-1.5 px-4 py-2 bg-primary text-white rounded-full font-bold text-xs"><Check size={14} /> 적용</button>
                                <button onClick={() => setIsEditingLogline(false)} className="px-4 py-2 bg-slate-100 text-slate-600 rounded-full font-bold text-xs"><X size={14} /></button>
                              </div>
                            </div>
                          ) : (
                            <div className="relative group/edit">
                              <p className="font-serif text-2xl font-bold text-slate-800 leading-tight italic cursor-pointer hover:text-primary transition-colors" onClick={() => setIsEditingLogline(true)}>{editedLogline}</p>
                              <button onClick={() => setIsEditingLogline(true)} className="absolute -right-6 top-1/2 -translate-y-1/2 opacity-0 group-hover/edit:opacity-100 p-1.5 bg-primary/5 text-primary rounded-full hover:bg-primary/10 transition-all"><Edit2 size={14} /></button>
                            </div>
                          )}
                          <span className="absolute -bottom-8 -right-2 text-5xl text-primary/10 font-serif">"</span>
                        </div>
                      </section>

                      {/* Synopsis */}
                      <section className="space-y-4">
                        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                          <div className="flex items-center gap-2"><div className="p-1.5 bg-primary/5 rounded-xl text-primary"><FileText size={18} /></div><h3 className="font-serif text-xl font-bold text-slate-800">핵심 시놉시스</h3></div>
                          {!isEditingSynopsis && <button onClick={() => { setTempSynopsis(editedSynopsis); setIsEditingSynopsis(true); }} className="p-2 text-slate-400 hover:text-primary"><Edit2 size={16} /></button>}
                        </div>
                        <div className="bg-white/40 p-8 rounded-[32px] border border-white/60 shadow-sm">
                          {isEditingSynopsis ? (
                            <div className="space-y-3">
                              <textarea autoFocus value={tempSynopsis} onChange={e => setTempSynopsis(e.target.value)}
                                className="w-full bg-white/60 border-2 border-primary/20 rounded-2xl p-6 font-sans text-base italic font-medium leading-relaxed focus:border-primary/50 outline-none min-h-[200px]" />
                              <div className="flex justify-end gap-2">
                                <button onClick={() => setIsEditingSynopsis(false)} className="px-4 py-2 bg-slate-100 text-slate-600 rounded-full text-xs font-bold">취소</button>
                                <button onClick={() => { setEditedSynopsis(tempSynopsis); setIsEditingSynopsis(false); }} className="flex items-center gap-1.5 px-6 py-2 bg-primary text-white rounded-full text-xs font-bold"><Check size={14} /> 완료</button>
                              </div>
                            </div>
                          ) : (
                            <div className="text-on-surface-variant leading-relaxed text-base italic font-medium cursor-pointer hover:bg-primary/5 p-2 rounded-2xl transition-colors" onClick={() => { setTempSynopsis(editedSynopsis); setIsEditingSynopsis(true); }}>
                              {editedSynopsis.split('\n').map((p, i) => <p key={i} className="mb-3 last:mb-0">{p}</p>)}
                            </div>
                          )}
                        </div>
                      </section>

                      {/* Scenes */}
                      <section className="space-y-6">
                        <div className="flex items-center gap-2 pb-3 border-b border-slate-100">
                          <div className="p-1.5 bg-primary/5 rounded-xl text-primary"><Video size={18} /></div>
                          <h3 className="font-serif text-xl font-bold text-slate-800">주요 씬 스케치</h3>
                        </div>
                        <div className="relative space-y-8 pl-8 before:absolute before:left-[15px] before:top-2 before:bottom-2 before:w-[2px] before:bg-gradient-to-b before:from-primary/40 before:via-primary/10 before:to-transparent">
                          {story.scenes.map((scene, i) => (
                            <motion.div key={i} initial={{ opacity: 0, x: -16 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.1 + i * 0.08 }} className="group relative">
                              <div className="absolute left-[-25px] top-1.5 w-4 h-4 rounded-full bg-white border-4 border-primary ring-4 ring-primary/5 shadow-sm group-hover:scale-125 transition-transform" />
                              <div className="bg-white/80 p-5 rounded-2xl border border-slate-100 shadow-sm group-hover:shadow-md group-hover:border-primary/20 transition-all">
                                <div className="flex items-center gap-3 mb-2">
                                  <span className="text-[9px] font-bold text-primary uppercase tracking-widest bg-primary/5 px-2 py-0.5 rounded">장면 {i+1}</span>
                                  <h4 className="font-serif text-base font-bold text-slate-800">{scene.title}</h4>
                                </div>
                                <p className="text-on-surface-variant text-sm leading-relaxed">{scene.description}</p>
                              </div>
                            </motion.div>
                          ))}
                        </div>
                      </section>

                      {/* Next Steps */}
                      <motion.section initial={{ opacity: 0, scale: 0.97 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.6 }} className="relative">
                        <div className="absolute inset-0 bg-primary/5 rounded-[40px] blur-3xl opacity-60" />
                        <div className="relative p-8 bg-white/70 border border-white rounded-[40px] shadow-sm backdrop-blur-md">
                          <div className="flex flex-col md:flex-row items-center md:items-start gap-6">
                            <div className="p-4 bg-primary/10 rounded-[28px] text-primary shrink-0 ring-8 ring-primary/5"><Lightbulb size={28} /></div>
                            <div className="text-center md:text-left flex-grow">
                              <h4 className="font-serif text-xl font-bold text-primary mb-2">AI 디렉터의 최종 제언</h4>
                              <p className="text-on-surface-variant text-base leading-relaxed italic font-serif opacity-90">"{story.nextSteps}"</p>
                              <button onClick={onClose} className="mt-6 flex items-center gap-2 px-8 py-3 bg-primary text-white rounded-full font-bold text-sm shadow-xl hover:-translate-y-1 transition-all mx-auto md:mx-0">
                                스튜디오로 돌아가기 <ArrowRight size={16} />
                              </button>
                            </div>
                          </div>
                        </div>
                      </motion.section>
                    </motion.div>
                  )}

                  {/* ── CONTI TAB ── */}
                  {activeTab === 'conti' && (
                    <motion.div key="conti" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="max-w-3xl mx-auto space-y-6">
                      <div className="flex items-center gap-3 pb-4 border-b border-slate-100">
                        <div className="p-2 bg-primary/5 rounded-xl text-primary"><Film size={20} /></div>
                        <h3 className="font-serif text-2xl font-bold text-slate-800">영상 콘티 (Video Conti)</h3>
                      </div>
                      {story.videoConti?.length > 0 ? story.videoConti.map((shot, i) => (
                        <motion.div key={i} initial={{ opacity: 0, x: -12 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.1 }}
                          className="bg-white/80 border border-slate-100 rounded-3xl p-6 shadow-sm hover:shadow-md transition-all hover:border-primary/20">
                          <div className="flex items-center gap-2 mb-3">
                            <span className="text-[9px] font-bold text-primary bg-primary/5 px-2 py-0.5 rounded uppercase tracking-widest">CUT {i+1}</span>
                            <span className="text-xs font-bold text-slate-600 bg-slate-100 px-2 py-0.5 rounded">{shot.shot}</span>
                          </div>
                          <p className="text-slate-700 text-sm leading-relaxed mb-3"><strong className="text-primary">Visual:</strong> {shot.visual}</p>
                          <p className="text-slate-500 text-sm italic"><strong>Sound/Mood:</strong> {shot.soundMood}</p>
                        </motion.div>
                      )) : (
                        <div className="text-center py-16 text-slate-400">
                          <Film size={40} className="mx-auto mb-4 opacity-30" />
                          <p>콘티 데이터가 없습니다. 다시 융합을 시도해보세요.</p>
                        </div>
                      )}
                    </motion.div>
                  )}

                  {/* ── BGM TAB ── */}
                  {activeTab === 'bgm' && (
                    <motion.div key="bgm" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="max-w-3xl mx-auto">
                      <div className="flex items-center gap-3 pb-4 border-b border-slate-100 mb-8">
                        <div className="p-2 bg-primary/5 rounded-xl text-primary"><Music size={20} /></div>
                        <h3 className="font-serif text-2xl font-bold text-slate-800">BGM / OST 추천</h3>
                      </div>
                      <div className="relative">
                        <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-secondary/5 rounded-[40px] blur-3xl" />
                        <div className="relative p-10 bg-white/70 border border-white/80 rounded-[40px] shadow-md backdrop-blur-md">
                          <div className="flex items-start gap-6">
                            <div className="p-5 bg-primary/10 rounded-[28px] text-primary shrink-0 ring-8 ring-primary/5">
                              <Music size={36} />
                            </div>
                            <div>
                              <p className="text-[10px] font-bold text-primary uppercase tracking-widest mb-3">Director's Sound Palette</p>
                              <p className="font-serif text-lg text-slate-800 leading-relaxed italic">
                                {story.bgmRecommendation || "BGM 추천 정보가 없습니다."}
                              </p>
                            </div>
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  )}

                  {/* ── REVIEW TAB ── */}
                  {activeTab === 'review' && story.directorReview && (
                    <motion.div key="review" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="max-w-3xl mx-auto space-y-8">
                      <div className="flex items-center gap-3 pb-4 border-b border-slate-100">
                        <div className="p-2 bg-primary/5 rounded-xl text-primary"><Stethoscope size={20} /></div>
                        <h3 className="font-serif text-2xl font-bold text-slate-800">디렉터의 리뷰 & 처방</h3>
                      </div>

                      {/* Stars */}
                      <div className="bg-white/80 border border-slate-100 rounded-3xl p-8 shadow-sm text-center">
                        <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-4">별점 평가</p>
                        <div className="flex justify-center mb-4">
                          <StarRating stars={story.directorReview.stars} />
                        </div>
                      </div>

                      {/* Critique */}
                      <div className="bg-white/80 border border-slate-100 rounded-3xl p-8 shadow-sm">
                        <p className="text-[10px] font-bold text-primary uppercase tracking-widest mb-3">한 줄 평론 (Critique)</p>
                        <p className="font-serif text-xl font-bold text-slate-800 italic leading-relaxed">
                          "{story.directorReview.critique}"
                        </p>
                      </div>

                      {/* Diagnosis */}
                      <div className="relative">
                        <div className="absolute inset-0 bg-secondary/5 rounded-[32px] blur-2xl" />
                        <div className="relative bg-white/70 border border-secondary/10 rounded-[32px] p-8 backdrop-blur-md shadow-sm">
                          <p className="text-[10px] font-bold text-secondary uppercase tracking-widest mb-3">진단 & 다음 씬 처방 (Diagnosis)</p>
                          <p className="text-on-surface-variant text-base leading-relaxed">
                            {story.directorReview.diagnosis}
                          </p>
                        </div>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              )}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
