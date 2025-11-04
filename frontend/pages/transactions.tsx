import { useEffect, useState } from 'react'
import Head from 'next/head'
import Sidebar from '@/components/Sidebar'
import CurrencySelector from '@/components/CurrencySelector'
import DarkModeToggle from '@/components/DarkModeToggle'
import { Plus, Trash2, TrendingUp, TrendingDown, ArrowLeftRight, Calendar, Tag, Wallet } from 'lucide-react'
import { format } from 'date-fns'
import { formatCurrency, convertCurrency } from '@/utils/currency'

interface Transaction {
  id: number
  description: string
  amount: number
  currency: string
  type: 'income' | 'expense' | 'transfer'
  category?: string
  date: string
  account?: string
}

export default function Transactions() {
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [displayCurrency, setDisplayCurrency] = useState('USD')
  const [showConverted, setShowConverted] = useState(true)
  const [convertedAmounts, setConvertedAmounts] = useState<Record<number, number>>({})
  const [formData, setFormData] = useState({
    description: '',
    amount: '',
    currency: 'USD',
    type: 'expense' as 'income' | 'expense' | 'transfer',
    category: '',
    account: '',
    date: format(new Date(), 'yyyy-MM-dd'),
  })

  useEffect(() => {
    fetchTransactions()
  }, [])

  useEffect(() => {
    if (transactions.length > 0 && showConverted) {
      convertAllAmounts()
    }
  }, [transactions, displayCurrency, showConverted])

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

  const fetchTransactions = async () => {
    try {
      const res = await fetch('http://localhost:8000/v1/transactions/')
      const data = await res.json()
      setTransactions(data)
    } catch (err) {
      console.error('Failed to fetch transactions:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const res = await fetch('http://localhost:8000/v1/transactions/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...formData,
          amount: parseFloat(formData.amount),
          date: new Date(formData.date).toISOString(),
        }),
      })
      if (res.ok) {
        await fetchTransactions()
        setShowForm(false)
        setFormData({
          description: '',
          amount: '',
          currency: 'USD',
          type: 'expense',
          category: '',
          account: '',
          date: format(new Date(), 'yyyy-MM-dd'),
        })
      }
    } catch (err) {
      console.error('Failed to create transaction:', err)
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Delete this transaction?')) return
    try {
      const res = await fetch(`http://localhost:8000/v1/transactions/${id}`, {
        method: 'DELETE',
      })
      if (res.ok) {
        await fetchTransactions()
      }
    } catch (err) {
      console.error('Failed to delete transaction:', err)
    }
  }


  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'income':
        return <TrendingUp size={20} />
      case 'expense':
        return <TrendingDown size={20} />
      case 'transfer':
        return <ArrowLeftRight size={20} />
    }
  }

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'income':
        return 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400'
      case 'expense':
        return 'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400'
      case 'transfer':
        return 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400'
    }
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

  return (
    <>
      <Head>
        <title>Transactions - LedgerLight</title>
      </Head>
      <div className="flex min-h-screen bg-gray-50 dark:bg-gray-900">
        <Sidebar />
        <main className="flex-1 ml-64 p-8">
          <div className="max-w-7xl mx-auto">
            {/* Header */}
            <div className="flex items-center justify-between mb-8">
              <div>
                <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">Transactions</h1>
                <p className="text-gray-600 dark:text-gray-400">Manage your income and expenses</p>
              </div>
              <div className="flex items-center gap-4">
                <DarkModeToggle />
                <div className="flex items-center gap-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl px-4 py-2">
                  <input
                    type="checkbox"
                    id="showConverted"
                    checked={showConverted}
                    onChange={(e) => setShowConverted(e.target.checked)}
                    className="w-4 h-4 text-primary-600 rounded focus:ring-primary-500 dark:focus:ring-primary-400"
                  />
                  <label htmlFor="showConverted" className="text-sm font-medium text-gray-700 dark:text-gray-300 cursor-pointer">
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
                <button
                  onClick={() => setShowForm(!showForm)}
                  className="btn-primary flex items-center gap-2"
                >
                  <Plus size={20} />
                  Add Transaction
                </button>
              </div>
            </div>

            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              <div className="card p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Total Income</p>
                    <p className="text-3xl font-bold text-green-600 dark:text-green-400">
                      {formatCurrency(totalIncome, displayCurrency)}
                    </p>
                  </div>
                  <div className="p-4 bg-green-100 dark:bg-green-900/30 rounded-xl">
                    <TrendingUp className="w-8 h-8 text-green-600 dark:text-green-400" />
                  </div>
                </div>
              </div>
              <div className="card p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Total Expenses</p>
                    <p className="text-3xl font-bold text-red-600 dark:text-red-400">
                      {formatCurrency(totalExpenses, displayCurrency)}
                    </p>
                  </div>
                  <div className="p-4 bg-red-100 dark:bg-red-900/30 rounded-xl">
                    <TrendingDown className="w-8 h-8 text-red-600 dark:text-red-400" />
                  </div>
                </div>
              </div>
              <div className="card p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Net</p>
                    <p className={`text-3xl font-bold ${net >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                      {formatCurrency(net, displayCurrency)}
                    </p>
                  </div>
                  <div className={`p-4 rounded-xl ${net >= 0 ? 'bg-green-100 dark:bg-green-900/30' : 'bg-red-100 dark:bg-red-900/30'}`}>
                    {net >= 0 ? (
                      <TrendingUp className={`w-8 h-8 ${net >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`} />
                    ) : (
                      <TrendingDown className="w-8 h-8 text-red-600 dark:text-red-400" />
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Add Transaction Form */}
            {showForm && (
              <div className="card p-6 mb-8">
                <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-6">Add Transaction</h2>
                <form onSubmit={handleSubmit} className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Description *
                      </label>
                      <input
                        type="text"
                        required
                        value={formData.description}
                        onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                        className="input-modern"
                        placeholder="e.g., Grocery shopping"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Amount *
                      </label>
                      <input
                        type="number"
                        step="0.01"
                        required
                        value={formData.amount}
                        onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                        className="input-modern"
                        placeholder="0.00"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Type *
                      </label>
                      <select
                        value={formData.type}
                        onChange={(e) => setFormData({ ...formData, type: e.target.value as any })}
                        className="input-modern"
                      >
                        <option value="expense">Expense</option>
                        <option value="income">Income</option>
                        <option value="transfer">Transfer</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Currency *
                      </label>
                      <select
                        value={formData.currency}
                        onChange={(e) => setFormData({ ...formData, currency: e.target.value })}
                        className="input-modern"
                      >
                        <option value="USD">USD - US Dollar ($)</option>
                        <option value="CAD">CAD - Canadian Dollar (C$)</option>
                        <option value="BRL">BRL - Brazilian Real (R$)</option>
                        <option value="EUR">EUR - Euro (€)</option>
                        <option value="GBP">GBP - British Pound (£)</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Date *
                      </label>
                      <input
                        type="date"
                        required
                        value={formData.date}
                        onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                        className="input-modern"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Category
                      </label>
                      <input
                        type="text"
                        value={formData.category}
                        onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                        className="input-modern"
                        placeholder="e.g., Food, Shopping"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Account
                      </label>
                      <input
                        type="text"
                        value={formData.account}
                        onChange={(e) => setFormData({ ...formData, account: e.target.value })}
                        className="input-modern"
                        placeholder="e.g., Checking, Savings"
                      />
                    </div>
                  </div>
                  <div className="flex gap-4">
                    <button type="submit" className="btn-primary">
                      Add Transaction
                    </button>
                    <button
                      type="button"
                      onClick={() => setShowForm(false)}
                      className="btn-secondary"
                    >
                      Cancel
                    </button>
                  </div>
                </form>
              </div>
            )}

            {/* Transactions List */}
            <div className="card">
              <div className="p-6 border-b border-gray-100 dark:border-gray-700">
                <h2 className="text-xl font-bold text-gray-900 dark:text-white">All Transactions</h2>
              </div>
              {loading ? (
                <div className="p-12 text-center text-gray-400 dark:text-gray-500">Loading...</div>
              ) : transactions.length === 0 ? (
                <div className="p-12 text-center">
                  <p className="text-gray-400 dark:text-gray-500 mb-4">No transactions yet</p>
                  <button onClick={() => setShowForm(true)} className="btn-primary">
                    Add Your First Transaction
                  </button>
                </div>
              ) : (
                <div className="divide-y divide-gray-100 dark:divide-gray-700">
                  {transactions
                    .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
                    .map((tx) => {
                      const convertedAmount = getConvertedAmount(tx)
                      return (
                        <div key={tx.id} className="p-6 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-4 flex-1">
                              <div className={`p-3 rounded-xl ${getTypeColor(tx.type)}`}>
                                {getTypeIcon(tx.type)}
                              </div>
                              <div className="flex-1">
                                <h3 className="font-semibold text-gray-900 dark:text-white text-lg mb-1">
                                  {tx.description}
                                </h3>
                                <div className="flex items-center gap-4 text-sm text-gray-500 dark:text-gray-400">
                                  <span className="flex items-center gap-1">
                                    <Calendar size={14} />
                                    {format(new Date(tx.date), 'MMM dd, yyyy')}
                                  </span>
                                  {tx.category && (
                                    <span className="flex items-center gap-1">
                                      <Tag size={14} />
                                      {tx.category}
                                    </span>
                                  )}
                                  {tx.account && (
                                    <span className="flex items-center gap-1">
                                      <Wallet size={14} />
                                      {tx.account}
                                    </span>
                                  )}
                                </div>
                              </div>
                            </div>
                            <div className="flex items-center gap-6">
                              <div className="text-right">
                                <div className="flex items-baseline gap-2">
                                  <p
                                    className={`text-xl font-bold ${
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
                                        className={`text-lg font-semibold text-gray-600 dark:text-gray-300 ${
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
                              <button
                                onClick={() => handleDelete(tx.id)}
                                className="p-2 text-gray-400 dark:text-gray-500 hover:text-red-600 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/30 rounded-lg transition-colors"
                              >
                                <Trash2 size={18} />
                              </button>
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
