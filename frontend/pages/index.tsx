import { useEffect, useState } from 'react'
import Head from 'next/head'
import Link from 'next/link'
import Sidebar from '@/components/Sidebar'
import StatCard from '@/components/StatCard'
import CurrencySelector from '@/components/CurrencySelector'
import DarkModeToggle from '@/components/DarkModeToggle'
import { DollarSign, TrendingUp, TrendingDown, ArrowUpRight } from 'lucide-react'
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { format, subDays } from 'date-fns'
import { formatCurrency, convertCurrency } from '@/utils/currency'

interface Transaction {
  id: number
  description: string
  amount: number
  currency: string
  type: 'income' | 'expense' | 'transfer'
  category?: string
  date: string
}

export default function Home() {
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [loading, setLoading] = useState(true)
  const [displayCurrency, setDisplayCurrency] = useState('USD')
  const [showConverted, setShowConverted] = useState(true)
  const [convertedAmounts, setConvertedAmounts] = useState<Record<number, number>>({})
  const [isDarkMode, setIsDarkMode] = useState(false)

  useEffect(() => {
    fetchTransactions()
    // Check dark mode status
    const checkDarkMode = () => {
      if (typeof window !== 'undefined') {
        setIsDarkMode(document.documentElement.classList.contains('dark'))
      }
    }
    checkDarkMode()
    // Watch for dark mode changes
    const observer = new MutationObserver(checkDarkMode)
    if (typeof window !== 'undefined') {
      observer.observe(document.documentElement, {
        attributes: true,
        attributeFilter: ['class']
      })
    }
    return () => observer.disconnect()
  }, [])

  useEffect(() => {
    if (transactions.length > 0 && showConverted) {
      convertAllAmounts()
    }
  }, [transactions, displayCurrency, showConverted])

  const fetchTransactions = async () => {
    try {
      const res = await fetch('http://localhost:8000/v1/transactions/')
      const data = await res.json()
      setTransactions(data)
      setLoading(false)
    } catch (err) {
      console.error('Failed to fetch transactions:', err)
      setLoading(false)
    }
  }

  const convertAllAmounts = async () => {
    const converted: Record<number, number> = {}
    await Promise.all(
      transactions.map(async (tx) => {
        if (tx.currency === displayCurrency) {
          converted[tx.id] = tx.amount
        } else {
          const convertedAmount = await convertCurrency(tx.amount, tx.currency, displayCurrency)
          converted[tx.id] = convertedAmount
        }
      })
    )
    setConvertedAmounts(converted)
  }

  const getConvertedAmount = (tx: Transaction): number | null => {
    if (!showConverted || tx.currency === displayCurrency) return null
    return convertedAmounts[tx.id] || null
  }

  // Calculate totals - convert all to display currency for summary
  const totalIncome = transactions
    .filter(t => t.type === 'income')
    .reduce((sum, t) => {
      const amount = t.currency === displayCurrency ? t.amount : (convertedAmounts[t.id] || 0)
      return sum + amount
    }, 0)
  
  const totalExpenses = transactions
    .filter(t => t.type === 'expense')
    .reduce((sum, t) => {
      const amount = t.currency === displayCurrency ? t.amount : (convertedAmounts[t.id] || 0)
      return sum + amount
    }, 0)
  
  const net = totalIncome - totalExpenses

  // Generate chart data for last 7 days (using converted amounts)
  const last7Days = Array.from({ length: 7 }, (_, i) => {
    const date = subDays(new Date(), 6 - i)
    const dayTransactions = transactions.filter(
      t => format(new Date(t.date), 'yyyy-MM-dd') === format(date, 'yyyy-MM-dd')
    )
    const income = dayTransactions
      .filter(t => t.type === 'income')
      .reduce((sum, t) => {
        const amount = t.currency === displayCurrency ? t.amount : (convertedAmounts[t.id] || 0)
        return sum + amount
      }, 0)
    const expenses = dayTransactions
      .filter(t => t.type === 'expense')
      .reduce((sum, t) => {
        const amount = t.currency === displayCurrency ? t.amount : (convertedAmounts[t.id] || 0)
        return sum + amount
      }, 0)
    return {
      date: format(date, 'MMM dd'),
      income,
      expenses,
      net: income - expenses,
    }
  })

  // Category breakdown (using converted amounts)
  const categoryData = transactions
    .filter(t => t.type === 'expense' && t.category)
    .reduce((acc, t) => {
      const amount = t.currency === displayCurrency ? t.amount : (convertedAmounts[t.id] || 0)
      acc[t.category!] = (acc[t.category!] || 0) + amount
      return acc
    }, {} as Record<string, number>)

  // Group small categories into "Others" (categories less than 5% of total)
  const totalExpensesForChart = Object.values(categoryData).reduce((sum, val) => sum + val, 0)
  const threshold = totalExpensesForChart * 0.05 // 5% threshold
  
  const pieData = Object.entries(categoryData)
    .sort(([, a], [, b]) => b - a) // Sort by value descending
    .reduce((acc, [name, value]) => {
      if (value >= threshold) {
        acc.push({ name, value })
      } else {
        // Add to "Others" category
        const othersIndex = acc.findIndex(item => item.name === 'Others')
        if (othersIndex >= 0) {
          acc[othersIndex].value += value
        } else {
          acc.push({ name: 'Others', value })
        }
      }
      return acc
    }, [] as Array<{ name: string; value: number }>)

  const COLORS = ['#0ea5e9', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#ef4444', '#6b7280']


  return (
    <>
      <Head>
        <title>Dashboard - LedgerLight</title>
        <meta name="description" content="Privacy-first personal finance dashboard" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </Head>
      <div className="flex min-h-screen bg-gray-50 dark:bg-gray-900">
        <Sidebar />
        <main className="flex-1 ml-64 p-8">
          <div className="max-w-7xl mx-auto">
            {/* Header */}
            <div className="mb-8 flex items-center justify-between">
              <div>
                <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">Dashboard</h1>
                <p className="text-gray-600 dark:text-gray-400">Welcome back! Here's your financial overview.</p>
              </div>
              <div className="flex items-center gap-4">
                <DarkModeToggle />
                <div className="flex items-center gap-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl px-4 py-2">
                  <input
                    type="checkbox"
                    id="showConvertedDashboard"
                    checked={showConverted}
                    onChange={(e) => setShowConverted(e.target.checked)}
                    className="w-4 h-4 text-primary-600 rounded focus:ring-primary-500 dark:focus:ring-primary-400"
                  />
                  <label htmlFor="showConvertedDashboard" className="text-sm font-medium text-gray-700 dark:text-gray-300 cursor-pointer">
                    Show converted
                  </label>
                </div>
                {showConverted && (
                  <CurrencySelector
                    selectedCurrency={displayCurrency}
                    onCurrencyChange={setDisplayCurrency}
                    showLabel={false}
                  />
                )}
              </div>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              <StatCard
                title="Net Worth"
                value={formatCurrency(net, displayCurrency)}
                change={net >= 0 ? `+${formatCurrency(net, displayCurrency)}` : formatCurrency(net, displayCurrency)}
                changeType={net >= 0 ? 'positive' : 'negative'}
                icon={TrendingUp}
                gradient="bg-gradient-to-br from-green-400 to-emerald-500"
              />
              <StatCard
                title="Total Income"
                value={formatCurrency(totalIncome, displayCurrency)}
                icon={DollarSign}
                gradient="bg-gradient-to-br from-blue-400 to-cyan-500"
              />
              <StatCard
                title="Total Expenses"
                value={formatCurrency(totalExpenses, displayCurrency)}
                icon={TrendingDown}
                gradient="bg-gradient-to-br from-red-400 to-rose-500"
              />
            </div>

            {/* Charts Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
              {/* Income vs Expenses Chart */}
              <div className="card p-6">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-xl font-bold text-gray-900 dark:text-white">Cash Flow</h2>
                  <span className="text-sm text-gray-500 dark:text-gray-400">Last 7 days</span>
                </div>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={last7Days}>
                    <defs>
                      <linearGradient id="colorIncome" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                      </linearGradient>
                      <linearGradient id="colorExpenses" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" className="dark:stroke-gray-700" />
                    <XAxis dataKey="date" stroke="#6b7280" className="dark:stroke-gray-400" />
                    <YAxis stroke="#6b7280" className="dark:stroke-gray-400" />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: isDarkMode ? '#1f2937' : 'white',
                        border: `1px solid ${isDarkMode ? '#374151' : '#e5e7eb'}`,
                        borderRadius: '12px',
                        boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                        color: isDarkMode ? '#f3f4f6' : '#111827'
                      }}
                    />
                    <Area type="monotone" dataKey="income" stroke="#10b981" fillOpacity={1} fill="url(#colorIncome)" />
                    <Area type="monotone" dataKey="expenses" stroke="#ef4444" fillOpacity={1} fill="url(#colorExpenses)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>

              {/* Category Breakdown */}
              <div className="card p-6">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-xl font-bold text-gray-900 dark:text-white">Spending by Category</h2>
                </div>
                {pieData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={pieData}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                        outerRadius={100}
                        fill="#8884d8"
                        dataKey="value"
                      >
                        {pieData.map((entry, index) => (
                          <Cell 
                            key={`cell-${index}`} 
                            fill={entry.name === 'Others' ? '#6b7280' : COLORS[index % (COLORS.length - 1)]} 
                          />
                        ))}
                      </Pie>
                      <Tooltip 
                        formatter={(value: number) => formatCurrency(value, displayCurrency)}
                        contentStyle={{ 
                          backgroundColor: isDarkMode ? '#1f2937' : 'white',
                          border: `1px solid ${isDarkMode ? '#374151' : '#e5e7eb'}`,
                          borderRadius: '12px',
                          color: isDarkMode ? '#f3f4f6' : '#111827'
                        }}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-[300px] flex items-center justify-center text-gray-400 dark:text-gray-500">
                    No category data yet
                  </div>
                )}
              </div>
            </div>

            {/* Recent Transactions */}
            <div className="card">
              <div className="p-6 border-b border-gray-100 dark:border-gray-700 flex items-center justify-between">
                <h2 className="text-xl font-bold text-gray-900 dark:text-white">Recent Transactions</h2>
                <Link href="/transactions" className="btn-secondary text-sm flex items-center gap-2">
                  View All
                  <ArrowUpRight size={16} />
                </Link>
              </div>
              {loading ? (
                <div className="p-12 text-center text-gray-400 dark:text-gray-500">Loading...</div>
              ) : transactions.length === 0 ? (
                <div className="p-12 text-center">
                  <p className="text-gray-400 dark:text-gray-500 mb-4">No transactions yet</p>
                  <Link href="/transactions" className="btn-primary inline-block">
                    Add Your First Transaction
                  </Link>
                </div>
              ) : (
                <div className="divide-y divide-gray-100 dark:divide-gray-700">
                  {transactions
                    .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
                    .slice(0, 5)
                    .map((tx) => {
                      const convertedAmount = getConvertedAmount(tx)
                      return (
                        <div key={tx.id} className="p-6 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-4">
                              <div
                                className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                                  tx.type === 'income'
                                    ? 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400'
                                    : tx.type === 'expense'
                                    ? 'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400'
                                    : 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400'
                                }`}
                              >
                                {tx.type === 'income' ? (
                                  <TrendingUp size={20} />
                                ) : tx.type === 'expense' ? (
                                  <TrendingDown size={20} />
                                ) : (
                                  <DollarSign size={20} />
                                )}
                              </div>
                              <div>
                                <h3 className="font-semibold text-gray-900 dark:text-white">{tx.description}</h3>
                                <p className="text-sm text-gray-500 dark:text-gray-400">
                                  {format(new Date(tx.date), 'MMM dd, yyyy')}
                                  {tx.category && ` • ${tx.category}`}
                                </p>
                              </div>
                            </div>
                            <div className="text-right">
                              <div className="flex items-baseline gap-2">
                                <p
                                  className={`text-lg font-bold ${
                                    tx.type === 'income' ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                                  }`}
                                >
                                  {tx.type === 'expense' ? '-' : '+'}
                                  {formatCurrency(Math.abs(tx.amount), tx.currency)}
                                </p>
                                {showConverted && convertedAmount && tx.currency !== displayCurrency && (
                                  <>
                                    <span className="text-gray-400 dark:text-gray-500">≈</span>
                                    <p
                                      className={`text-base font-semibold text-gray-600 dark:text-gray-300 ${
                                        tx.type === 'income' ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                                      }`}
                                    >
                                      {formatCurrency(Math.abs(convertedAmount), displayCurrency)}
                                    </p>
                                  </>
                                )}
                              </div>
                              <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                                {tx.currency}
                                {showConverted && convertedAmount && tx.currency !== displayCurrency && (
                                  <span className="ml-1">→ {displayCurrency}</span>
                                )}
                              </p>
                            </div>
                          </div>
                        </div>
                      )
                    })}
                </div>
              )}
            </div>
          </div>
        </main>
      </div>
    </>
  )
}
