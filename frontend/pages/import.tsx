import { useState } from 'react';
import PageLayout, { PageHeader } from '../components/layout/PageLayout';
import { Card, CardContent } from '../components/ui/Card';
import { Upload, UploadCloud, FileSpreadsheet, Wallet, Sparkles, ArrowRight, CheckCircle2 } from 'lucide-react';
import { motion } from 'framer-motion';
import { useRouter } from 'next/router';

interface ImportOption {
  id: string;
  name: string;
  description: string;
  icon: typeof Upload;
  color: string;
  gradient: string;
  badge?: string;
  features: string[];
  path: string;
}

const IMPORT_OPTIONS: ImportOption[] = [
  {
    id: 'wealthsimple',
    name: 'Wealthsimple',
    description: 'Import monthly statements with transactions, holdings, and balances',
    icon: Wallet,
    color: 'from-purple-500 to-pink-500',
    gradient: 'bg-gradient-to-br from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20',
    badge: 'Recommended',
    features: ['Monthly statements', 'Transactions & holdings', 'Auto-create accounts', 'Full history'],
    path: '/portfolio/wealthsimple-import',
  },
  {
    id: 'monarch',
    name: 'Monarch Money',
    description: 'Import transactions and account balances from Monarch Money CSV exports',
    icon: UploadCloud,
    color: 'from-blue-500 to-cyan-500',
    gradient: 'bg-gradient-to-br from-blue-50 to-cyan-50 dark:from-blue-900/20 dark:to-cyan-900/20',
    features: ['Transactions CSV', 'Balances CSV', 'Category mapping', 'Multi-account'],
    path: '/portfolio/monarch-import',
  },
  {
    id: 'csv',
    name: 'Bank CSV',
    description: 'Import transactions from any bank CSV file with flexible column mapping',
    icon: FileSpreadsheet,
    color: 'from-green-500 to-emerald-500',
    gradient: 'bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20',
    features: ['Generic CSV', 'Column mapping', 'Multiple formats', 'Date parsing'],
    path: '/import/csv',
  },
  {
    id: 'snapshot',
    name: 'Portfolio Snapshot',
    description: 'Import a point-in-time snapshot of your holdings and account balances',
    icon: Upload,
    color: 'from-orange-500 to-red-500',
    gradient: 'bg-gradient-to-br from-orange-50 to-red-50 dark:from-orange-900/20 dark:to-red-900/20',
    features: ['Holdings snapshot', 'Current balances', 'Net worth tracking', 'Historical data'],
    path: '/portfolio/import',
  },
];

export default function ImportHub() {
  const router = useRouter();
  const [hoveredCard, setHoveredCard] = useState<string | null>(null);

  const handleImport = (path: string) => {
    router.push(path);
  };

  return (
    <PageLayout title="Import Data">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <motion.div
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.5 }}
            className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-primary-500 to-primary-600 rounded-2xl shadow-xl mb-6"
          >
            <Sparkles className="w-10 h-10 text-white" />
          </motion.div>
          <h1 className="text-4xl font-bold text-slate-900 dark:text-white mb-4">
            Import Your Financial Data
          </h1>
          <p className="text-lg text-slate-600 dark:text-slate-400 max-w-2xl mx-auto">
            Choose how you'd like to import your data. We support multiple formats to make it easy.
          </p>
        </div>

        {/* Import Options Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-12">
          {IMPORT_OPTIONS.map((option, index) => {
            const Icon = option.icon;
            const isHovered = hoveredCard === option.id;

            return (
              <motion.div
                key={option.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                onHoverStart={() => setHoveredCard(option.id)}
                onHoverEnd={() => setHoveredCard(null)}
              >
                <Card
                  className={`relative overflow-hidden cursor-pointer transition-all duration-300 hover:shadow-2xl hover:scale-[1.02] ${
                    isHovered ? 'ring-2 ring-primary-500' : ''
                  }`}
                  onClick={() => handleImport(option.path)}
                >
                  <CardContent className="p-6">
                    {/* Badge */}
                    {option.badge && (
                      <div className="absolute top-4 right-4">
                        <span className="px-3 py-1 bg-primary-100 dark:bg-primary-900/50 text-primary-700 dark:text-primary-300 text-xs font-semibold rounded-full">
                          {option.badge}
                        </span>
                      </div>
                    )}

                    {/* Icon */}
                    <div className={`inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br ${option.color} mb-4 shadow-lg`}>
                      <Icon className="w-8 h-8 text-white" />
                    </div>

                    {/* Title & Description */}
                    <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-2">
                      {option.name}
                    </h3>
                    <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">
                      {option.description}
                    </p>

                    {/* Features */}
                    <ul className="space-y-2 mb-4">
                      {option.features.map((feature, idx) => (
                        <li key={idx} className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
                          <CheckCircle2 className="w-4 h-4 text-green-600 dark:text-green-400 flex-shrink-0" />
                          <span>{feature}</span>
                        </li>
                      ))}
                    </ul>

                    {/* Action Button */}
                    <motion.button
                      whileHover={{ x: 5 }}
                      className="flex items-center gap-2 text-primary-600 dark:text-primary-400 font-medium text-sm group"
                    >
                      <span>Start importing</span>
                      <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
                    </motion.button>

                    {/* Gradient Overlay on Hover */}
                    <motion.div
                      className={`absolute inset-0 ${option.gradient} opacity-0 transition-opacity duration-300 pointer-events-none`}
                      animate={{ opacity: isHovered ? 0.1 : 0 }}
                    />
                  </CardContent>
                </Card>
              </motion.div>
            );
          })}
        </div>

        {/* Help Section */}
        <Card className="bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-800 dark:to-slate-900 border-slate-200 dark:border-slate-700">
          <CardContent className="p-8 text-center">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">
              Need help choosing?
            </h3>
            <p className="text-slate-600 dark:text-slate-400 mb-4">
              Start with <strong>Wealthsimple</strong> if you have monthly statements. Use <strong>Bank CSV</strong> for custom imports.
            </p>
            <p className="text-sm text-slate-500 dark:text-slate-500">
              All imports are processed locally and stored securely in your database.
            </p>
          </CardContent>
        </Card>
      </div>
    </PageLayout>
  );
}
