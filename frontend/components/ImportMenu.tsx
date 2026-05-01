import { useState, useRef, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { Upload, UploadCloud, FileSpreadsheet, Wallet, ChevronDown } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '@/utils/cn';

interface ImportOption {
  name: string;
  href: string;
  icon: typeof Upload;
  description: string;
  badge?: string;
}

const IMPORT_OPTIONS: ImportOption[] = [
  {
    name: 'Wealthsimple',
    href: '/portfolio/wealthsimple-import',
    icon: Wallet,
    description: 'Import monthly statements',
    badge: 'Recommended',
  },
  {
    name: 'Monarch Money',
    href: '/portfolio/monarch-import',
    icon: UploadCloud,
    description: 'Transactions & balances CSV',
  },
  {
    name: 'Bank CSV',
    href: '/import',
    icon: FileSpreadsheet,
    description: 'Generic CSV import',
  },
  {
    name: 'Portfolio Snapshot',
    href: '/portfolio/import',
    icon: Upload,
    description: 'Holdings snapshot',
  },
];

export function ImportMenu({ className }: { className?: string }) {
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  // Close on click outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen]);

  // Close on route change
  useEffect(() => {
    setIsOpen(false);
  }, [router.pathname]);

  const isImportActive = IMPORT_OPTIONS.some(opt => router.pathname === opt.href);

  return (
    <div ref={menuRef} className={cn('relative', className)}>
      {/* Trigger Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          'w-full flex items-center justify-between gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-all',
          isImportActive
            ? 'bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300'
            : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
        )}
      >
        <div className="flex items-center gap-3">
          <UploadCloud className="w-5 h-5" />
          <span>Import</span>
        </div>
        <motion.div
          animate={{ rotate: isOpen ? 180 : 0 }}
          transition={{ duration: 0.2 }}
        >
          <ChevronDown className="w-4 h-4" />
        </motion.div>
      </button>

      {/* Dropdown Menu */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
            className="absolute left-0 right-0 mt-2 bg-white dark:bg-slate-800 rounded-xl shadow-2xl border border-slate-200 dark:border-slate-700 overflow-hidden z-50"
          >
            <div className="p-2 space-y-1">
              {IMPORT_OPTIONS.map((option) => {
                const Icon = option.icon;
                const isActive = router.pathname === option.href;

                return (
                  <Link
                    key={option.href}
                    href={option.href}
                    className={cn(
                      'flex items-start gap-3 p-3 rounded-lg transition-all group',
                      isActive
                        ? 'bg-primary-50 dark:bg-primary-900/20'
                        : 'hover:bg-slate-50 dark:hover:bg-slate-700/50'
                    )}
                  >
                    <div className={cn(
                      'flex-shrink-0 w-10 h-10 rounded-lg flex items-center justify-center transition-colors',
                      isActive
                        ? 'bg-primary-600 text-white'
                        : 'bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-400 group-hover:bg-primary-100 dark:group-hover:bg-primary-900/30 group-hover:text-primary-600 dark:group-hover:text-primary-400'
                    )}>
                      <Icon className="w-5 h-5" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <p className={cn(
                          'font-medium text-sm',
                          isActive
                            ? 'text-primary-700 dark:text-primary-300'
                            : 'text-slate-900 dark:text-white'
                        )}>
                          {option.name}
                        </p>
                        {option.badge && (
                          <span className="px-1.5 py-0.5 bg-primary-100 dark:bg-primary-900/50 text-primary-700 dark:text-primary-300 text-[10px] font-medium rounded">
                            {option.badge}
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                        {option.description}
                      </p>
                    </div>
                  </Link>
                );
              })}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// Mobile version - shows all options in a bottom sheet
export function ImportMenuMobile({ onClose }: { onClose?: () => void }) {
  const router = useRouter();

  const handleClick = () => {
    onClose?.();
  };

  return (
    <div className="p-4 space-y-2">
      <h3 className="text-sm font-semibold text-slate-900 dark:text-white px-3 mb-3">
        Import Data
      </h3>
      {IMPORT_OPTIONS.map((option) => {
        const Icon = option.icon;
        const isActive = router.pathname === option.href;

        return (
          <Link
            key={option.href}
            href={option.href}
            onClick={handleClick}
            className={cn(
              'flex items-center gap-3 p-3 rounded-xl transition-all',
              isActive
                ? 'bg-primary-100 dark:bg-primary-900/30'
                : 'hover:bg-slate-100 dark:hover:bg-slate-800'
            )}
          >
            <div className={cn(
              'flex-shrink-0 w-12 h-12 rounded-xl flex items-center justify-center',
              isActive
                ? 'bg-primary-600 text-white'
                : 'bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-400'
            )}>
              <Icon className="w-6 h-6" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <p className={cn(
                  'font-medium',
                  isActive
                    ? 'text-primary-700 dark:text-primary-300'
                    : 'text-slate-900 dark:text-white'
                )}>
                  {option.name}
                </p>
                {option.badge && (
                  <span className="px-2 py-0.5 bg-primary-100 dark:bg-primary-900/50 text-primary-700 dark:text-primary-300 text-xs font-medium rounded">
                    {option.badge}
                  </span>
                )}
              </div>
              <p className="text-sm text-slate-500 dark:text-slate-400">
                {option.description}
              </p>
            </div>
          </Link>
        );
      })}
    </div>
  );
}
