import React, { useState } from 'react'
import Head from 'next/head'
import Sidebar from '../components/Sidebar'
import DarkModeToggle from '../components/DarkModeToggle'
import CurrencySelector from '../components/CurrencySelector'
import { Settings as SettingsIcon, User, Bell, Shield, Globe } from 'lucide-react'

export default function Settings() {
  const [displayCurrency, setDisplayCurrency] = useState('USD')

  return (
    <>
      <Head>
        <title>Settings - Canopy</title>
      </Head>
      <div className="flex min-h-screen bg-gray-50 dark:bg-gray-950">
      <Sidebar />
      <div className="ml-64 flex-1 p-8">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Settings</h1>
              <p className="text-gray-500 dark:text-gray-400 mt-2">Manage your preferences</p>
            </div>
            <DarkModeToggle />
          </div>

          <div className="space-y-6">
            {/* General Settings */}
            <div className="card p-6">
              <div className="flex items-center gap-3 mb-6">
                <div className="p-2 bg-primary-100 dark:bg-primary-900/30 rounded-lg">
                  <SettingsIcon className="w-5 h-5 text-primary-600 dark:text-primary-400" />
                </div>
                <h2 className="text-xl font-bold text-gray-900 dark:text-white">General</h2>
              </div>
              
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <label className="text-sm font-medium text-gray-900 dark:text-white">Display Currency</label>
                    <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Choose your preferred currency</p>
                  </div>
                  <CurrencySelector 
                    selectedCurrency={displayCurrency} 
                    onCurrencyChange={setDisplayCurrency}
                  />
                </div>

                <div className="flex items-center justify-between pt-4 border-t border-gray-200 dark:border-gray-700">
                  <div>
                    <label className="text-sm font-medium text-gray-900 dark:text-white">Dark Mode</label>
                    <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Toggle dark theme</p>
                  </div>
                  <DarkModeToggle />
                </div>
              </div>
            </div>

            {/* Profile Settings */}
            <div className="card p-6">
              <div className="flex items-center gap-3 mb-6">
                <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                  <User className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                </div>
                <h2 className="text-xl font-bold text-gray-900 dark:text-white">Profile</h2>
              </div>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-900 dark:text-white mb-2">Name</label>
                  <input 
                    type="text" 
                    className="input-modern"
                    placeholder="Your name"
                    disabled
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-900 dark:text-white mb-2">Email</label>
                  <input 
                    type="email" 
                    className="input-modern"
                    placeholder="your@email.com"
                    disabled
                  />
                </div>
              </div>
            </div>

            {/* Notifications */}
            <div className="card p-6">
              <div className="flex items-center gap-3 mb-6">
                <div className="p-2 bg-yellow-100 dark:bg-yellow-900/30 rounded-lg">
                  <Bell className="w-5 h-5 text-yellow-600 dark:text-yellow-400" />
                </div>
                <h2 className="text-xl font-bold text-gray-900 dark:text-white">Notifications</h2>
              </div>
              
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <label className="text-sm font-medium text-gray-900 dark:text-white">Email Notifications</label>
                    <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Receive email updates</p>
                  </div>
                  <input type="checkbox" className="w-4 h-4" disabled />
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <label className="text-sm font-medium text-gray-900 dark:text-white">Transaction Alerts</label>
                    <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Get notified of large transactions</p>
                  </div>
                  <input type="checkbox" className="w-4 h-4" disabled />
                </div>
              </div>
            </div>

            {/* Privacy & Security */}
            <div className="card p-6">
              <div className="flex items-center gap-3 mb-6">
                <div className="p-2 bg-green-100 dark:bg-green-900/30 rounded-lg">
                  <Shield className="w-5 h-5 text-green-600 dark:text-green-400" />
                </div>
                <h2 className="text-xl font-bold text-gray-900 dark:text-white">Privacy & Security</h2>
              </div>
              
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <label className="text-sm font-medium text-gray-900 dark:text-white">Data Encryption</label>
                    <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">All data is encrypted at rest</p>
                  </div>
                  <span className="text-sm text-green-600 dark:text-green-400 font-medium">Enabled</span>
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <label className="text-sm font-medium text-gray-900 dark:text-white">Two-Factor Authentication</label>
                    <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Add an extra layer of security</p>
                  </div>
                  <button className="btn-secondary text-sm" disabled>Enable</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      </div>
    </>
  )
}

