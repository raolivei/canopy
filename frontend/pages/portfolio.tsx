import React from 'react'
import Head from 'next/head'
import Sidebar from '../components/Sidebar'
import DarkModeToggle from '../components/DarkModeToggle'
import { TrendingUp, DollarSign, PieChart, BarChart3 } from 'lucide-react'

export default function Portfolio() {
  return (
    <>
      <Head>
        <title>Portfolio - LedgerLight</title>
      </Head>
      <div className="flex min-h-screen bg-gray-50 dark:bg-gray-950">
      <Sidebar />
      <div className="ml-64 flex-1 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Portfolio</h1>
              <p className="text-gray-500 dark:text-gray-400 mt-2">Track your investments and assets</p>
            </div>
            <DarkModeToggle />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div className="card p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Total Portfolio Value</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white mt-2">$0.00</p>
                </div>
                <div className="p-3 bg-primary-100 dark:bg-primary-900/30 rounded-xl">
                  <TrendingUp className="w-6 h-6 text-primary-600 dark:text-primary-400" />
                </div>
              </div>
            </div>

            <div className="card p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Investments</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white mt-2">$0.00</p>
                </div>
                <div className="p-3 bg-green-100 dark:bg-green-900/30 rounded-xl">
                  <BarChart3 className="w-6 h-6 text-green-600 dark:text-green-400" />
                </div>
              </div>
            </div>

            <div className="card p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Cash</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white mt-2">$0.00</p>
                </div>
                <div className="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-xl">
                  <DollarSign className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                </div>
              </div>
            </div>

            <div className="card p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Allocation</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white mt-2">--</p>
                </div>
                <div className="p-3 bg-purple-100 dark:bg-purple-900/30 rounded-xl">
                  <PieChart className="w-6 h-6 text-purple-600 dark:text-purple-400" />
                </div>
              </div>
            </div>
          </div>

          <div className="card p-6">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Coming Soon</h2>
            <p className="text-gray-500 dark:text-gray-400">
              Portfolio tracking and investment management features will be available soon.
            </p>
          </div>
        </div>
      </div>
      </div>
    </>
  )
}

