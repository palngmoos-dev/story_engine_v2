import { motion, AnimatePresence } from "motion/react";
import { AlertCircle, X } from "lucide-react";

interface ConfirmModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  variant?: 'danger' | 'primary';
}

export default function ConfirmModal({ 
  isOpen, 
  onClose, 
  onConfirm, 
  title, 
  message, 
  confirmText = "확인", 
  cancelText = "취소",
  variant = 'danger'
}: ConfirmModalProps) {
  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-[110] flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm"
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0, y: 20 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.9, opacity: 0, y: 20 }}
            className="w-full max-w-md bg-white rounded-[32px] overflow-hidden shadow-2xl flex flex-col"
          >
            <div className="p-8 pb-6 flex items-start gap-4">
              <div className={`p-3 rounded-2xl ${variant === 'danger' ? 'bg-red-50 text-red-500' : 'bg-primary/5 text-primary'}`}>
                <AlertCircle size={24} />
              </div>
              <div className="flex-grow">
                <h3 className="font-serif text-2xl font-bold text-slate-800 mb-2">{title}</h3>
                <p className="text-on-surface-variant leading-relaxed">
                  {message}
                </p>
              </div>
              <button 
                onClick={onClose}
                className="p-1 text-slate-300 hover:text-slate-500 rounded-full transition-colors"
              >
                <X size={20} />
              </button>
            </div>
            
            <div className="p-8 pt-2 flex gap-3">
              <button
                onClick={onClose}
                className="flex-grow px-6 py-3 bg-slate-100 hover:bg-slate-200 text-slate-600 rounded-2xl font-bold text-sm transition-colors"
              >
                {cancelText}
              </button>
              <button
                onClick={() => {
                  onConfirm();
                  onClose();
                }}
                className={`flex-grow px-6 py-3 text-white rounded-2xl font-bold text-sm transition-all shadow-lg ${
                  variant === 'danger' 
                    ? 'bg-red-500 hover:bg-red-600 shadow-red-200' 
                    : 'bg-primary hover:bg-primary/90 shadow-primary/20'
                }`}
              >
                {confirmText}
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
