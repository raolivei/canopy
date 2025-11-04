import { LucideIcon } from 'lucide-react'

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
  return (
    <div className="card card-hover p-6 relative overflow-hidden">
      <div className={`absolute top-0 right-0 w-32 h-32 ${gradient} opacity-10 dark:opacity-5 rounded-full -mr-16 -mt-16`} />
      <div className="relative">
        <div className="flex items-center justify-between mb-4">
          <div className={`p-3 rounded-xl ${gradient} bg-opacity-10 dark:bg-opacity-20`}>
            <Icon className="w-6 h-6 text-gray-700 dark:text-gray-300" />
          </div>
          {change && (
            <span
              className={`text-sm font-medium px-2 py-1 rounded-lg ${
                changeType === 'positive'
                  ? 'text-green-700 dark:text-green-400 bg-green-50 dark:bg-green-900/30'
                  : changeType === 'negative'
                  ? 'text-red-700 dark:text-red-400 bg-red-50 dark:bg-red-900/30'
                  : 'text-gray-700 dark:text-gray-300 bg-gray-50 dark:bg-gray-700'
              }`}
            >
              {change}
            </span>
          )}
        </div>
        <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">{title}</h3>
        <p className="text-3xl font-bold text-gray-900 dark:text-white">{value}</p>
      </div>
    </div>
  )
}

