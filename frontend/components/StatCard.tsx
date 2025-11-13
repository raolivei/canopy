import { LucideIcon, TrendingUp, TrendingDown } from 'lucide-react'

interface StatCardProps {
  title: string
  value: string
  change?: string
  changeType?: 'positive' | 'negative' | 'neutral'
  icon: LucideIcon
  gradient: string
}

export default function StatCard({
  title,
  value,
  change,
  changeType = 'neutral',
  icon: Icon,
  gradient,
}: StatCardProps) {
  const isPositive = changeType === 'positive'
  const isNegative = changeType === 'negative'
  
  return (
    <div className="card card-hover p-6 relative overflow-hidden group">
      <div className={`absolute top-0 right-0 w-32 h-32 ${gradient} opacity-10 dark:opacity-5 rounded-full -mr-16 -mt-16 transition-opacity group-hover:opacity-15 dark:group-hover:opacity-10`} />
      <div className="relative">
        <div className="flex items-center justify-between mb-4">
          <div className={`p-3 rounded-xl ${gradient} bg-opacity-10 dark:bg-opacity-20 transition-transform group-hover:scale-110`}>
            <Icon className="w-6 h-6 text-gray-700 dark:text-gray-300" />
          </div>
          {change && (
            <div className={`flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1.5 rounded-lg ${
              isPositive
                ? 'text-green-700 dark:text-green-400 bg-green-50 dark:bg-green-900/30'
                : isNegative
                ? 'text-red-700 dark:text-red-400 bg-red-50 dark:bg-red-900/30'
                : 'text-gray-700 dark:text-gray-300 bg-gray-50 dark:bg-gray-700'
            }`}>
              {isPositive && <TrendingUp className="w-3.5 h-3.5" />}
              {isNegative && <TrendingDown className="w-3.5 h-3.5" />}
              <span>{change}</span>
            </div>
          )}
        </div>
        <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">{title}</h3>
        <p className="text-3xl font-bold text-gray-900 dark:text-white tracking-tight">{value}</p>
        {change && (
          <p className={`text-xs font-medium mt-2 ${
            isPositive
              ? 'text-green-600 dark:text-green-400'
              : isNegative
              ? 'text-red-600 dark:text-red-400'
              : 'text-gray-500 dark:text-gray-400'
          }`}>
            {isPositive ? 'Increased' : isNegative ? 'Decreased' : 'No change'} from previous period
          </p>
        )}
      </div>
    </div>
  )
}

