import { useState, useEffect } from 'react';
import { MessageCircle, X, Minimize2, Sparkles, Maximize2 } from 'lucide-react';
import { AssistantChat } from './AssistantChat';
import { motion, AnimatePresence } from 'framer-motion';

export function FloatingAssistant() {
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [conversationId, setConversationId] = useState<number | undefined>();

  // Keyboard shortcut: Cmd/Ctrl + Shift + A
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key === 'a') {
        e.preventDefault();
        setIsOpen(prev => !prev);
      }
      // ESC to close
      if (e.key === 'Escape' && isOpen) {
        setIsOpen(false);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen]);

  return (
    <>
      {/* Floating Button */}
      <AnimatePresence>
        {!isOpen && (
          <motion.div
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0, opacity: 0 }}
            className="fixed bottom-6 right-6 z-50"
          >
            <motion.button
              whileHover={{ scale: 1.05, rotate: [0, -10, 10, -10, 0] }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setIsOpen(true)}
              className="group relative w-16 h-16 bg-gradient-to-br from-primary-600 to-primary-700 hover:from-primary-700 hover:to-primary-800 text-white rounded-full shadow-xl hover:shadow-2xl transition-all flex items-center justify-center overflow-hidden"
              aria-label="Open AI Assistant (⌘⇧A)"
            >
              {/* Animated background gradient */}
              <motion.div
                className="absolute inset-0 bg-gradient-to-r from-primary-400 via-primary-600 to-primary-800 opacity-75"
                animate={{
                  scale: [1, 1.2, 1],
                  rotate: [0, 180, 360],
                }}
                transition={{
                  duration: 8,
                  repeat: Infinity,
                  ease: "linear",
                }}
                style={{ filter: 'blur(20px)' }}
              />
              
              {/* Icon with subtle animation */}
              <motion.div
                className="relative z-10"
                animate={{ y: [0, -2, 0] }}
                transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
              >
                <MessageCircle className="w-7 h-7" />
              </motion.div>
              
              {/* Sparkle indicator */}
              <motion.div
                className="absolute -top-1 -right-1"
                animate={{ scale: [1, 1.2, 1], rotate: [0, 180, 360] }}
                transition={{ duration: 3, repeat: Infinity }}
              >
                <Sparkles className="w-5 h-5 text-yellow-300 drop-shadow-lg" />
              </motion.div>
              
              {/* Tooltip */}
              <div className="absolute bottom-full right-0 mb-2 px-3 py-2 bg-slate-900 text-white text-xs rounded-lg shadow-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
                Ask AI Assistant
                <kbd className="ml-2 px-1.5 py-0.5 bg-slate-800 rounded text-[10px]">⌘⇧A</kbd>
                <div className="absolute top-full right-4 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-slate-900" />
              </div>
            </motion.button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Desktop Chat Window */}
      <AnimatePresence>
        {isOpen && !isMinimized && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.9 }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            className="hidden lg:flex fixed bottom-6 right-6 z-50 w-[440px] h-[680px] rounded-2xl shadow-2xl flex-col overflow-hidden backdrop-blur-xl"
            style={{
              background: 'linear-gradient(135deg, rgba(255,255,255,0.95) 0%, rgba(248,250,252,0.98) 100%)',
            }}
          >
            {/* Glassmorphism border */}
            <div className="absolute inset-0 rounded-2xl border border-white/20 pointer-events-none" />
            
            {/* Header */}
            <motion.div
              initial={{ y: -20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.1 }}
              className="flex items-center justify-between px-5 py-4 border-b border-slate-200/50 dark:border-slate-700/50 bg-gradient-to-r from-primary-50/80 to-primary-100/80 dark:from-slate-800/80 dark:to-slate-800/80 backdrop-blur-sm"
            >
              <div className="flex items-center gap-3">
                <motion.div
                  className="relative"
                  animate={{ rotate: [0, 10, -10, 0] }}
                  transition={{ duration: 5, repeat: Infinity }}
                >
                  <div className="w-10 h-10 bg-gradient-to-br from-primary-600 to-primary-700 rounded-xl flex items-center justify-center shadow-lg">
                    <Sparkles className="w-5 h-5 text-white" />
                  </div>
                  <motion.div
                    className="absolute -bottom-0.5 -right-0.5 w-3.5 h-3.5 bg-green-500 rounded-full border-2 border-white dark:border-slate-900"
                    animate={{ scale: [1, 1.2, 1] }}
                    transition={{ duration: 2, repeat: Infinity }}
                  />
                </motion.div>
                <div>
                  <h3 className="font-semibold text-sm text-slate-900 dark:text-white">
                    AI Financial Assistant
                  </h3>
                  <p className="text-xs text-slate-600 dark:text-slate-400 flex items-center gap-1.5">
                    <motion.span
                      className="inline-block w-1.5 h-1.5 bg-green-500 rounded-full"
                      animate={{ opacity: [1, 0.5, 1] }}
                      transition={{ duration: 2, repeat: Infinity }}
                    />
                    Online • Ready to help
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-1">
                <motion.button
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                  onClick={() => setIsMinimized(true)}
                  className="p-2 hover:bg-slate-200/50 dark:hover:bg-slate-700/50 rounded-lg transition-colors"
                  aria-label="Minimize"
                >
                  <Minimize2 className="w-4 h-4 text-slate-600 dark:text-slate-400" />
                </motion.button>
                <motion.button
                  whileHover={{ scale: 1.1, rotate: 90 }}
                  whileTap={{ scale: 0.9 }}
                  onClick={() => setIsOpen(false)}
                  className="p-2 hover:bg-slate-200/50 dark:hover:bg-slate-700/50 rounded-lg transition-colors"
                  aria-label="Close (ESC)"
                >
                  <X className="w-4 h-4 text-slate-600 dark:text-slate-400" />
                </motion.button>
              </div>
            </motion.div>

            {/* Chat Content */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.2 }}
              className="flex-1 overflow-hidden"
            >
              <AssistantChat
                conversationId={conversationId}
                onConversationStart={setConversationId}
              />
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Minimized State */}
      <AnimatePresence>
        {isOpen && isMinimized && (
          <motion.button
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0, opacity: 0 }}
            whileHover={{ scale: 1.05 }}
            onClick={() => setIsMinimized(false)}
            className="hidden lg:flex fixed bottom-6 right-6 z-50 items-center gap-3 px-4 py-3 bg-white dark:bg-slate-900 rounded-full shadow-xl border border-slate-200 dark:border-slate-700 hover:shadow-2xl transition-all"
          >
            <div className="w-8 h-8 bg-gradient-to-br from-primary-600 to-primary-700 rounded-full flex items-center justify-center">
              <MessageCircle className="w-4 h-4 text-white" />
            </div>
            <span className="text-sm font-medium text-slate-900 dark:text-white">
              AI Assistant
            </span>
            <Maximize2 className="w-4 h-4 text-slate-400" />
          </motion.button>
        )}
      </AnimatePresence>

      {/* Mobile - Full Screen */}
      <AnimatePresence>
        {isOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsOpen(false)}
              className="lg:hidden fixed inset-0 bg-black/40 backdrop-blur-sm z-40"
            />
            
            <motion.div
              initial={{ y: '100%' }}
              animate={{ y: 0 }}
              exit={{ y: '100%' }}
              transition={{ type: 'spring', damping: 30, stiffness: 300 }}
              className="lg:hidden fixed inset-x-0 bottom-0 top-0 z-50 bg-white dark:bg-slate-900 flex flex-col shadow-2xl"
            >
              {/* Mobile Header */}
              <div className="flex items-center justify-between px-4 py-4 border-b border-slate-200 dark:border-slate-700 bg-gradient-to-r from-primary-50 to-primary-100 dark:from-slate-800 dark:to-slate-800">
                <div className="flex items-center gap-3">
                  <div className="relative">
                    <div className="w-10 h-10 bg-gradient-to-br from-primary-600 to-primary-700 rounded-xl flex items-center justify-center shadow-lg">
                      <Sparkles className="w-5 h-5 text-white" />
                    </div>
                    <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-green-500 rounded-full border-2 border-white dark:border-slate-900" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-slate-900 dark:text-white">
                      AI Financial Assistant
                    </h3>
                    <p className="text-xs text-slate-600 dark:text-slate-400 flex items-center gap-1">
                      <span className="inline-block w-1.5 h-1.5 bg-green-500 rounded-full" />
                      Online
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => setIsOpen(false)}
                  className="p-2 hover:bg-slate-200 dark:hover:bg-slate-700 rounded-full transition-colors"
                  aria-label="Close"
                >
                  <X className="w-6 h-6 text-slate-600 dark:text-slate-400" />
                </button>
              </div>

              <div className="flex-1 overflow-hidden">
                <AssistantChat
                  conversationId={conversationId}
                  onConversationStart={setConversationId}
                />
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
