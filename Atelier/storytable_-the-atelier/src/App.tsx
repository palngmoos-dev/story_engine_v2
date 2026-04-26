import { useState, useEffect, useMemo, useRef } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Sparkles, Trash2, BookOpen, BrainCircuit, Info, LogIn, LogOut, User as UserIcon, Library, Eye, Shield, Waves } from 'lucide-react';
import { CardData, Mode, GeneratedStory, CardType } from './types';
import { generateCard, aggregateTableStats, DECK_META } from './constants';
import { fuseStory } from './lib/gemini';
import { auth, signInWithGoogle, logOut, saveStory, getUserStories, deleteStory } from './lib/firebase';
import { onAuthStateChanged, User } from 'firebase/auth';
import CardItem from './components/CardItem';
import DeckPile from './components/DeckPile';
import FusionResult from './components/FusionResult';
import LibraryView from './components/LibraryView';
import ConfirmModal from './components/ConfirmModal';
import CardEditor from './components/CardEditor';

type View = 'studio' | 'library';

export default function App() {
  const [cards, setCards] = useState<CardData[]>([]);
  const [mode, setMode] = useState<Mode>('beginner');
  const [story, setStory] = useState<GeneratedStory | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  const [view, setView] = useState<View>('studio');
  const [library, setLibrary] = useState<GeneratedStory[]>([]);
  const [libraryLoading, setLibraryLoading] = useState(false);
  const [localLibrary, setLocalLibrary] = useState<GeneratedStory[]>([]);
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);
  const [editingCardId, setEditingCardId] = useState<string | null>(null);
  const [isClearing, setIsClearing] = useState(false);
  const [showIntro, setShowIntro] = useState(true);
  const constraintsRef = useRef(null);

  const editingCard = useMemo(() => cards.find(c => c.id === editingCardId) || null, [cards, editingCardId]);

  const tableStats = useMemo(() => aggregateTableStats(cards), [cards]);

  useEffect(() => {
    const savedLocal = localStorage.getItem('storytable_local_library');
    if (savedLocal) {
      setLocalLibrary(JSON.parse(savedLocal));
    }

    const unsubscribe = onAuthStateChanged(auth, (u) => {
      setUser(u);
    });

    const timer = setTimeout(() => setShowIntro(false), 2500);
    return () => {
      unsubscribe();
      clearTimeout(timer);
    };
  }, []);

  useEffect(() => {
    if (view === 'library') {
      if (user) {
        fetchLibrary();
      } else {
        setLibrary(localLibrary);
      }
    }
  }, [view, user, localLibrary]);

  const fetchLibrary = async () => {
    if (!user) return;
    setLibraryLoading(true);
    try {
      const stories = await getUserStories(user.uid);
      // Combine with local if needed, or just show cloud
      setLibrary(stories);
    } catch (e) {
      console.error(e);
    } finally {
      setLibraryLoading(false);
    }
  };

  const drawCard = (type: CardType) => {
    if (cards.length >= 12) return;
    setCards([...cards, generateCard(type)]);
  };

  const removeCard = (id: string) => {
    setCards(cards.filter(c => c.id !== id));
  };

  const updateCard = (id: string, updates: Partial<CardData>) => {
    setCards(cards.map(c => c.id === id ? { ...c, ...updates } as CardData : c));
  };

  const clearTable = async () => {
    if (cards.length === 0) return;
    setIsClearing(true);
    // Let the animation play a bit
    await new Promise(resolve => setTimeout(resolve, 500));
    setCards([]);
    setStory(null);
    setIsClearing(false);
  };

  const handleFuse = async () => {
    if (cards.length < 1) {
      alert("최소 한 장 이상의 카드가 필요합니다.");
      return;
    }
    setIsLoading(true);
    try {
      const result = await fuseStory(cards, mode);
      setStory(result);
    } catch (error: any) {
      console.error(error);
      const errorMsg = error?.message || "알 수 없는 오류가 발생했습니다.";
      alert(`스토리 생성 실패: ${errorMsg}\n\n도움말: 인터넷 연결이나 API 키 설정을 확인해 주세요.`);
    } finally {
      setIsLoading(false);
    }
  };

  const loadingMessages = [
    "이야기꾼이 영감을 모으는 중...",
    "캐릭터의 숨겨진 비밀을 분석하고 있습니다...",
    "장소의 분위기에 색을 입히는 중...",
    "시네마틱한 카메라 앵글을 고민하고 있어요...",
    "가장 완벽한 엔딩을 조각하는 중..."
  ];
  const [currentMsgIdx, setCurrentMsgIdx] = useState(0);

  useEffect(() => {
    if (isLoading) {
      const interval = setInterval(() => {
        setCurrentMsgIdx(prev => (prev + 1) % loadingMessages.length);
      }, 2500);
      return () => clearInterval(interval);
    }
  }, [isLoading]);

  const handleSave = async (s: GeneratedStory) => {
    if (!user) {
      // Save to local storage
      const newLocalStory = { 
        ...s, 
        id: s.id || `local_${Date.now()}`,
        createdAt: { toDate: () => new Date() }, // Mock Firestore timestamp for UI
        mode 
      };
      
      const updatedLocal = [newLocalStory, ...localLibrary.filter(item => item.id !== newLocalStory.id)];
      setLocalLibrary(updatedLocal);
      localStorage.setItem('storytable_local_library', JSON.stringify(updatedLocal));
      
      // Update current displayed library if not in cloud mode
      setLibrary(updatedLocal);
      return;
    }
    
    await saveStory(user.uid, s, mode);
    if (view === 'library') fetchLibrary();
  };

  const handleDelete = (storyId: string) => {
    setDeleteConfirmId(storyId);
  };

  const executeDelete = async () => {
    const storyId = deleteConfirmId;
    if (!storyId) return;
    
    if (storyId.startsWith('local_')) {
      const updatedLocal = localLibrary.filter(s => s.id !== storyId);
      setLocalLibrary(updatedLocal);
      localStorage.setItem('storytable_local_library', JSON.stringify(updatedLocal));
      setLibrary(updatedLocal);
      setDeleteConfirmId(null);
      return;
    }

    if (!user) return;
    try {
      await deleteStory(user.uid, storyId);
      setLibrary(library.filter(s => s.id !== storyId));
      setDeleteConfirmId(null);
    } catch (e) {
      alert("삭제 실패");
    }
  };

  const syncLocalToCloud = async () => {
    if (!user || localLibrary.length === 0) return;
    if (!window.confirm(`${localLibrary.length}개의 로컬 스토리를 계정으로 동기화하시겠습니까?`)) return;
    
    setLibraryLoading(true);
    try {
      for (const s of localLibrary) {
        await saveStory(user.uid, s, s.mode || mode);
      }
      setLocalLibrary([]);
      localStorage.removeItem('storytable_local_library');
      await fetchLibrary();
      alert("동기화가 완료되었습니다.");
    } catch (e) {
      alert("동기화 중 오류가 발생했습니다.");
    } finally {
      setLibraryLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col overflow-hidden">
      <AnimatePresence>
        {showIntro && (
          <motion.div 
            initial={{ opacity: 1 }}
            exit={{ opacity: 0, y: -20 }}
            className="fixed inset-0 z-[200] bg-primary flex flex-col items-center justify-center text-white"
          >
             <motion.div
               initial={{ scale: 0.8, opacity: 0 }}
               animate={{ scale: 1, opacity: 1 }}
               transition={{ duration: 0.8, ease: "easeOut" }}
               className="flex flex-col items-center"
             >
                <div className="w-20 h-20 bg-white/20 rounded-[40px] flex items-center justify-center mb-8 backdrop-blur-xl">
                   <Sparkles size={48} className="animate-pulse" />
                </div>
                <h1 className="font-serif text-5xl font-bold tracking-tight mb-2">StoryTable</h1>
                <p className="text-xs uppercase font-bold tracking-[0.4em] opacity-60">The Atelier</p>
             </motion.div>
             <div className="absolute bottom-12">
                <div className="w-48 h-1 bg-white/10 rounded-full overflow-hidden">
                   <motion.div 
                     initial={{ x: '-100%' }}
                     animate={{ x: '100%' }}
                     transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
                     className="w-1/2 h-full bg-white/40"
                   />
                </div>
             </div>
          </motion.div>
        )}
      </AnimatePresence>
      {/* Top App Bar */}
      <header className="fixed top-0 w-full z-100 glass-morphism flex items-center justify-between px-8 py-4">
        <div className="flex items-center gap-4">
          <div onClick={() => setView('studio')} className="w-10 h-10 bg-primary rounded-2xl flex items-center justify-center text-white shadow-lg cursor-pointer">
            <Sparkles size={24} />
          </div>
          <div onClick={() => setView('studio')} className="cursor-pointer">
            <h1 className="font-serif font-bold text-2xl tracking-tight text-primary">StoryTable</h1>
            <p className="text-[10px] uppercase font-bold text-slate-400 tracking-widest leading-none">The Atelier</p>
          </div>
        </div>

        {/* View Switcher/Navigation */}
        <div className="hidden lg:flex items-center gap-6">
           <button 
             onClick={() => setView('studio')}
             className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-bold transition-all ${view === 'studio' ? 'text-primary' : 'text-slate-400 hover:text-slate-600'}`}
           >
             <Sparkles size={18} /> 스튜디오
           </button>
           <button 
             onClick={() => setView('library')}
             className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-bold transition-all ${view === 'library' ? 'text-primary' : 'text-slate-400 hover:text-slate-600'}`}
           >
             <Library size={18} /> 라이브러리
           </button>
        </div>

        {/* Mode Switcher & Profile */}
        <div className="flex items-center gap-6">
          <div className="hidden md:flex bg-slate-100 p-1 rounded-2xl border border-slate-200">
            <button
              onClick={() => setMode('beginner')}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all ${
                mode === 'beginner' 
                  ? 'bg-white shadow-sm text-primary' 
                  : 'text-slate-400 hover:text-slate-600'
              }`}
            >
              <BookOpen size={14} />
              초보자 선생님
            </button>
            <button
              onClick={() => setMode('expert')}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all ${
                mode === 'expert' 
                  ? 'bg-slate-900 shadow-sm text-white' 
                  : 'text-slate-400 hover:text-slate-600'
              }`}
            >
              <BrainCircuit size={14} />
              전문가 파트너
            </button>
          </div>

          <div className="flex items-center gap-3 pl-6 border-l border-slate-200">
            {!user ? (
              <button 
                onClick={signInWithGoogle}
                className="flex items-center gap-2 px-5 py-2 bg-primary text-white rounded-2xl text-xs font-bold shadow-md hover:bg-primary-container transition-all"
              >
                <LogIn size={16} /> 구글 로그인
              </button>
            ) : (
              <div className="group relative">
                <button className="w-10 h-10 rounded-full bg-slate-200 overflow-hidden border-2 border-primary/20 hover:border-primary transition-all">
                  {user.photoURL ? (
                    <img src={user.photoURL} alt={user.displayName || ""} referrerPolicy="no-referrer" className="w-full h-full object-cover" />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-slate-500">
                      <UserIcon size={20} />
                    </div>
                  )}
                </button>
                <div className="absolute top-full right-0 mt-2 w-48 bg-white rounded-2xl shadow-xl border border-slate-100 py-2 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all pointer-events-none group-hover:pointer-events-auto">
                   <div className="px-4 py-2 border-bottom border-slate-50 mb-1">
                      <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Logged in as</p>
                      <p className="text-sm font-bold text-slate-800 line-clamp-1">{user.displayName || user.email}</p>
                   </div>
                   <button 
                     onClick={logOut}
                     className="w-full flex items-center gap-2 px-4 py-2 text-sm text-red-500 hover:bg-red-50 transition-colors"
                   >
                     <LogOut size={16} /> 로그아웃
                   </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main Area */}
      <main className="flex-grow pt-24 pb-32 px-8 flex flex-col relative overflow-hidden">
        {/* Background Workshop Effects */}
        <div className="absolute inset-x-8 top-32 bottom-32 workshop-grain rounded-[60px] opacity-20 pointer-events-none" />
        
        <AnimatePresence mode="wait">
          {view === 'studio' ? (
            <motion.div 
              key="studio-view"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              className="flex flex-col flex-grow"
            >
              <div className="relative z-10 max-w-4xl mx-auto text-center mt-8 mb-12">
                <h2 className="font-serif text-4xl md:text-5xl font-bold text-slate-800 tracking-tight">
                  {mode === 'beginner' ? "오늘의 이야기를 조각해 볼까요?" : "새로운 시나리오 기획을 시작합니다."}
                </h2>
                <p className="mt-4 text-on-surface-variant max-w-2xl mx-auto">
                  {mode === 'beginner' 
                    ? "아래의 덱에서 여러분의 주인공과 배경, 그리고 소중한 조언 카드를 뽑아 테이블 위로 올려주세요. 모든 준비가 되면 '융합하기' 버튼을 눌러보세요!"
                    : "캐릭터의 결함, 미장센의 충돌, 그리고 타임라인의 불연속성을 조합하십시오. 감각적인 연출 포인트와 로그라인을 도출하기 위해 카드를 하이브리드하세요."}
                </p>
              </div>

              <div className="relative flex-grow flex items-start justify-center min-h-[700px] w-full mt-4 pb-40 overflow-visible">
                <AnimatePresence mode="popLayout">
                  {cards.length === 0 ? (
                    <motion.div
                      key="empty-state"
                      className="mt-32 flex flex-col items-center gap-6 text-slate-300"
                    >
                      <div className="w-32 h-32 border-4 border-dashed border-slate-200 rounded-[40px] flex items-center justify-center animate-pulse">
                        <Sparkles size={48} className="opacity-20" />
                      </div>
                      <p className="font-bold uppercase tracking-widest text-xs opacity-40">테이블이 비어 있습니다. 덱에서 카드를 뽑아 시작하세요.</p>
                    </motion.div>
                  ) : (
                    <div ref={constraintsRef} className="relative w-full flex flex-wrap justify-center gap-x-12 gap-y-16 p-8 overflow-visible min-h-[600px]">
                      {cards.map((card, idx) => (
                        <motion.div
                          key={card.id}
                          layoutId={card.id}
                          initial={{ scale: 0, opacity: 0, y: 50, rotate: -5 }}
                          animate={{ 
                            scale: 1, 
                            opacity: 1,
                            y: isClearing ? 500 : 0,
                            rotate: isClearing ? (idx % 2 === 0 ? 45 : -45) : (idx % 2 === 0 ? -1 : 1),
                            zIndex: 10 + idx
                          }}
                          exit={{ scale: 0, opacity: 0, y: 100, rotate: 5 }}
                          transition={{ 
                            type: "spring", 
                            stiffness: isClearing ? 100 : 260, 
                            damping: 20,
                            delay: isClearing ? (cards.length - idx) * 0.05 : idx * 0.05 
                          }}
                          style={{ margin: '-30px' }} // 겹침 효과 강화
                        >
                          <CardItem 
                            card={card} 
                            onRemove={() => removeCard(card.id)} 
                            onUpdate={updateCard}
                            onEdit={(c) => setEditingCardId(c.id)}
                            dragConstraints={constraintsRef}
                          />
                        </motion.div>
                      ))}
                    </div>
                  )}
                </AnimatePresence>
              </div>

              {cards.length > 0 && (
                <div className="fixed bottom-40 left-0 right-0 flex justify-center z-[80] pointer-events-none">
                  <motion.div 
                    initial={{ y: 100, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    className="pointer-events-auto"
                  >
                    <button
                      onClick={handleFuse}
                      disabled={isLoading}
                      className="group relative flex items-center gap-4 px-16 py-6 bg-gradient-to-r from-primary to-purple-600 text-white rounded-full font-serif text-2xl font-bold shadow-[0_20px_50px_rgba(109,40,217,0.3)] hover:shadow-[0_25px_60px_rgba(109,40,217,0.5)] transition-all hover:scale-105 active:scale-95 disabled:opacity-50 border-2 border-white/20"
                    >
                      <div className="absolute inset-0 bg-white/10 rounded-full blur-xl animate-pulse" />
                      <Sparkles className={`relative z-10 ${isLoading ? 'animate-spin' : 'group-hover:rotate-12'} transition-transform`} />
                      <span className="relative z-10">
                        {isLoading ? "융합 에너지를 모으는 중..." : "스토리 융합하기"}
                      </span>
                      
                      {/* Floating Particles Effect */}
                      <div className="absolute -top-12 left-1/2 -translate-x-1/2 w-48 h-12 pointer-events-none overflow-hidden">
                         <div className="flex justify-center gap-2 animate-bounce">
                            <div className="w-1 h-1 bg-white rounded-full opacity-50" />
                            <div className="w-1.5 h-1.5 bg-white rounded-full opacity-30" />
                         </div>
                      </div>
                    </button>
                  </motion.div>
                </div>
              )}
            </motion.div>
          ) : (
            <motion.div 
              key="library-view"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="flex flex-col flex-grow max-w-[1400px] mx-auto w-full"
            >
               <div className="mt-8 mb-12 flex flex-col md:flex-row md:items-end justify-between gap-6">
                  <div>
                    <h2 className="font-serif text-4xl font-bold text-slate-800 mb-2">나만의 라이브러리</h2>
                    <p className="text-on-surface-variant">
                      {user ? "당신의 클라우드 계정에 보관된 기획안들입니다." : "브라우저에 임시로 저장된 기획안들입니다."}
                    </p>
                  </div>
                  
                  {user && localLibrary.length > 0 && (
                    <motion.div 
                      initial={{ opacity: 0, scale: 0.9 }}
                      animate={{ opacity: 1, scale: 1 }}
                      className="bg-amber-50 border border-amber-200 p-4 rounded-3xl flex items-center gap-4 shadow-sm"
                    >
                      <div className="flex-grow">
                         <p className="text-xs font-bold text-amber-800">로그인 전 작성한 {localLibrary.length}개의 스토리가 발견되었습니다.</p>
                         <p className="text-[10px] text-amber-600">안전한 보관을 위해 계정으로 동기화하세요.</p>
                      </div>
                      <button 
                        onClick={syncLocalToCloud}
                        className="px-4 py-2 bg-amber-500 text-white rounded-xl text-xs font-bold hover:bg-amber-600 transition-all"
                      >
                        계정으로 이동
                      </button>
                    </motion.div>
                  )}
               </div>
               
               {/* Loading Overlay */}
               <AnimatePresence>
                 {isLoading && (
                   <motion.div 
                     initial={{ opacity: 0 }}
                     animate={{ opacity: 1 }}
                     exit={{ opacity: 0 }}
                     className="fixed inset-0 bg-slate-900/60 backdrop-blur-md z-[200] flex items-center justify-center p-6"
                   >
                     <motion.div 
                       initial={{ scale: 0.9, y: 20 }}
                       animate={{ scale: 1, y: 0 }}
                       className="bg-white rounded-[40px] p-12 max-w-lg w-full shadow-2xl text-center relative overflow-hidden"
                     >
                        {/* Animated Background Rings */}
                        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] border border-slate-100 rounded-full animate-ping opacity-20" />
                        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[400px] h-[400px] border border-slate-100 rounded-full animate-pulse opacity-20" />

                        <div className="relative z-10 flex flex-col items-center">
                           <div className="mb-8 relative">
                             <div className="w-24 h-24 border-4 border-primary border-t-transparent rounded-full animate-spin" />
                             <BrainCircuit className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-10 h-10 text-primary animate-pulse" />
                           </div>
                           <h3 className="font-serif text-3xl font-bold text-slate-800 mb-4 italic">"{loadingMessages[currentMsgIdx]}"</h3>
                           <p className="text-slate-400 text-sm font-medium tracking-wide">카드들의 에너지를 융합하여 걸작을 빚고 있습니다.</p>
                           
                           <div className="mt-8 flex gap-1 justify-center">
                             {[0, 1, 2, 3].map(i => (
                               <motion.div 
                                 key={i}
                                 animate={{ opacity: [0.3, 1, 0.3] }}
                                 transition={{ repeat: Infinity, duration: 1, delay: i * 0.2 }}
                                 className="w-2 h-2 bg-primary rounded-full"
                               />
                             ))}
                           </div>
                        </div>
                     </motion.div>
                   </motion.div>
                 )}
               </AnimatePresence>

               {library.length === 0 && !user && (
                 <div className="flex flex-col items-center justify-center py-24 text-center bg-white/50 rounded-[40px] border-2 border-dashed border-slate-200">
                    <BookOpen className="w-16 h-16 text-slate-300 mb-6" />
                    <h3 className="font-serif text-2xl font-bold text-slate-800 mb-2">저장된 스토리가 없습니다</h3>
                    <p className="text-on-surface-variant mb-8 max-w-sm">로그인 없이도 브라우저에 저장할 수 있지만, 영구적인 보관을 위해 구글 로그인을 추천합니다.</p>
                    <button 
                      onClick={signInWithGoogle}
                      className="px-10 py-4 bg-primary text-white rounded-full font-bold shadow-xl hover:bg-primary-container transition-all"
                    >
                      구글로 로그인하고 시작하기
                    </button>
                 </div>
               ) || (
                 <LibraryView 
                    stories={library} 
                    loading={libraryLoading} 
                    onDelete={handleDelete}
                    onView={(s) => setStory(s)}
                 />
               )}
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      {/* Bottom Deck/Nav Area */}
      <footer className="fixed bottom-0 w-full z-50 glass-morphism pt-4 pb-8 flex flex-col items-center gap-4">
        {view === 'studio' ? (
          <div className="flex items-center gap-2 overflow-x-auto px-4 max-w-full scrollbar-thin">
            {DECK_META.map(deck => (
              <DeckPile key={deck.type} type={deck.type} label={deck.label} color={deck.color} onDraw={() => drawCard(deck.type)} disabled={cards.length >= 12} />
            ))}
          </div>
        ) : (
          <button 
            onClick={() => setView('studio')}
            className="flex items-center gap-3 px-10 py-5 bg-slate-900 text-white rounded-full font-serif text-xl font-bold shadow-xl hover:bg-black transition-all hover:scale-105 active:scale-95"
          >
             <Sparkles /> 새 스토리 만들러 가기
          </button>
        )}
        
        <div className="flex items-center gap-4 text-slate-400">
           {view === 'studio' ? (
             <>
                <div className="flex items-center gap-1">
                  <Info size={12} />
                  <span className="text-[10px] font-bold uppercase tracking-wider">테이블: {cards.length}/12 카드</span>
                </div>
                <div className="w-1 h-1 rounded-full bg-slate-300" />
                {cards.length > 0 ? (
                  <div className="flex items-center gap-3">
                    <div className="flex items-center gap-1" title="의심 (Suspicion)">
                      <Eye size={11} className="text-amber-400" />
                      <span className="text-[10px] font-bold text-amber-500">{tableStats.suspicion}</span>
                    </div>
                    <div className="flex items-center gap-1" title="압박 (Pressure)">
                      <Shield size={11} className="text-red-400" />
                      <span className="text-[10px] font-bold text-red-500">{tableStats.pressure}</span>
                    </div>
                    <div className="flex items-center gap-1" title="공명 (Echo)">
                      <Waves size={11} className="text-blue-400" />
                      <span className="text-[10px] font-bold text-blue-500">{tableStats.echo}</span>
                    </div>
                  </div>
                ) : (
                  <span className="text-[10px] font-bold uppercase tracking-wider">덱에서 카드를 뽑아 이야기를 조각하세요</span>
                )}
             </>
           ) : (
             <p className="text-[10px] font-bold uppercase tracking-wider">Created with StoryTable AI Atelier</p>
           )}
        </div>
      </footer>

      {/* App Bar Clear Button (only in studio) */}
      {view === 'studio' && (
        <div className="fixed top-6 right-48 flex items-center gap-3">
           <button 
             onClick={clearTable}
             className="p-3 text-slate-400 hover:text-red-500 transition-colors"
             title="테이블 비우기"
           >
             <Trash2 size={20} />
           </button>
        </div>
      )}

      {/* Result Overlay */}
      <FusionResult 
        story={story} 
        loading={isLoading} 
        onClose={() => setStory(null)} 
        mode={mode}
        onSave={handleSave}
        isSaved={!!story?.id}
      />

      {/* Global Modals */}
      <CardEditor 
        card={editingCard}
        isOpen={!!editingCardId}
        onClose={() => setEditingCardId(null)}
        onUpdate={updateCard}
        onRemove={removeCard}
      />

      <ConfirmModal 
        isOpen={deleteConfirmId !== null}
        onClose={() => setDeleteConfirmId(null)}
        onConfirm={executeDelete}
        title="스토리 삭제"
        message="이 시나리오 기획안을 라이브러리에서 정말로 삭제하시겠습니까? 삭제된 데이터는 복구할 수 없습니다."
        confirmText="삭제하기"
        cancelText="취소"
        variant="danger"
      />
    </div>
  );
}

function PlusSymbol() {
  return (
    <svg width="40" height="40" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M20 5V35M5 20H35" stroke="currentColor" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
}
