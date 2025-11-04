import React from "react";
import Head from "next/head";
import Sidebar from "../components/Sidebar";
import DarkModeToggle from "../components/DarkModeToggle";
import { Wallet, Plus, CreditCard, Building2, PiggyBank } from "lucide-react";

export default function Accounts() {
  return (
    <>
      <Head>
        <title>Accounts - LedgerLight</title>
      </Head>
      <div className="flex min-h-screen bg-gray-50 dark:bg-gray-950">
        <Sidebar />
        <div className="ml-64 flex-1 p-8">
          <div className="max-w-7xl mx-auto">
            <div className="flex items-center justify-between mb-8">
              <div>
                <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                  Accounts
                </h1>
                <p className="text-gray-500 dark:text-gray-400 mt-2">
                  Manage your financial accounts
                </p>
              </div>
              <div className="flex items-center gap-4">
                <button className="btn-primary flex items-center gap-2">
                  <Plus className="w-4 h-4" />
                  Add Account
                </button>
                <DarkModeToggle />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
              <div className="card p-6 card-hover cursor-pointer">
                <div className="flex items-center justify-between mb-4">
                  <div className="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-xl">
                    <Building2 className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                  </div>
                  <span className="text-xs px-2 py-1 bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 rounded-full">
                    Checking
                  </span>
                </div>
                <h3 className="font-semibold text-gray-900 dark:text-white mb-1">
                  Primary Checking
                </h3>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  $0.00
                </p>
              </div>

              <div className="card p-6 card-hover cursor-pointer">
                <div className="flex items-center justify-between mb-4">
                  <div className="p-3 bg-purple-100 dark:bg-purple-900/30 rounded-xl">
                    <CreditCard className="w-6 h-6 text-purple-600 dark:text-purple-400" />
                  </div>
                  <span className="text-xs px-2 py-1 bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 rounded-full">
                    Credit Card
                  </span>
                </div>
                <h3 className="font-semibold text-gray-900 dark:text-white mb-1">
                  Credit Card
                </h3>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  $0.00
                </p>
              </div>

              <div className="card p-6 card-hover cursor-pointer">
                <div className="flex items-center justify-between mb-4">
                  <div className="p-3 bg-green-100 dark:bg-green-900/30 rounded-xl">
                    <PiggyBank className="w-6 h-6 text-green-600 dark:text-green-400" />
                  </div>
                  <span className="text-xs px-2 py-1 bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 rounded-full">
                    Savings
                  </span>
                </div>
                <h3 className="font-semibold text-gray-900 dark:text-white mb-1">
                  Savings Account
                </h3>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  $0.00
                </p>
              </div>
            </div>

            <div className="card p-6">
              <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
                Coming Soon
              </h2>
              <p className="text-gray-500 dark:text-gray-400">
                Account management features will be available soon. You'll be
                able to add, edit, and track multiple accounts.
              </p>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
