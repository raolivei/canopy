import React, { useState } from "react";
import Link from "next/link";
import PageLayout, { PageHeader } from "@/components/layout/PageLayout";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import {
  Settings as SettingsIcon,
  User,
  Bell,
  Shield,
  Globe,
  Moon,
  Sun,
  Plug,
  ChevronRight,
  Check,
} from "lucide-react";
import { cn } from "@/utils/cn";
import { motion } from "framer-motion";

export default function Settings() {
  const [displayCurrency, setDisplayCurrency] = useState("CAD");
  const [isDarkMode, setIsDarkMode] = useState(false);

  React.useEffect(() => {
    setIsDarkMode(document.documentElement.classList.contains("dark"));
  }, []);

  const toggleDarkMode = () => {
    const newValue = !isDarkMode;
    setIsDarkMode(newValue);
    if (newValue) {
      document.documentElement.classList.add("dark");
      localStorage.setItem("darkMode", "true");
    } else {
      document.documentElement.classList.remove("dark");
      localStorage.setItem("darkMode", "false");
    }
  };

  const currencyOptions = [
    { value: "CAD", label: "CAD - Canadian Dollar" },
    { value: "USD", label: "USD - US Dollar" },
    { value: "BRL", label: "BRL - Brazilian Real" },
    { value: "EUR", label: "EUR - Euro" },
    { value: "GBP", label: "GBP - British Pound" },
  ];

  return (
    <PageLayout title="Settings" description="Manage your preferences">
      <PageHeader title="Settings" description="Customize your Canopy experience" />

      <div className="max-w-3xl space-y-6">
        {/* General Settings */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          <Card>
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="p-2 bg-primary-100 dark:bg-primary-900/30 rounded-lg">
                  <SettingsIcon className="w-5 h-5 text-primary-600 dark:text-primary-400" />
                </div>
                <div>
                  <CardTitle>General</CardTitle>
                  <CardDescription>Basic app preferences</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-slate-900 dark:text-white">Display Currency</p>
                  <p className="text-sm text-slate-500 dark:text-slate-400">
                    Choose your preferred currency for displaying values
                  </p>
                </div>
                <Select
                  options={currencyOptions}
                  value={displayCurrency}
                  onChange={setDisplayCurrency}
                  className="w-48"
                />
              </div>

              <div className="border-t border-slate-100 dark:border-slate-800 pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-slate-900 dark:text-white">Dark Mode</p>
                    <p className="text-sm text-slate-500 dark:text-slate-400">Toggle dark theme</p>
                  </div>
                  <button
                    onClick={toggleDarkMode}
                    className={cn(
                      "relative w-14 h-8 rounded-full transition-colors",
                      isDarkMode ? "bg-primary-600" : "bg-slate-200 dark:bg-slate-700"
                    )}
                  >
                    <span
                      className={cn(
                        "absolute top-1 left-1 w-6 h-6 rounded-full bg-white shadow-sm transition-transform flex items-center justify-center",
                        isDarkMode && "translate-x-6"
                      )}
                    >
                      {isDarkMode ? (
                        <Moon className="w-3.5 h-3.5 text-primary-600" />
                      ) : (
                        <Sun className="w-3.5 h-3.5 text-amber-500" />
                      )}
                    </span>
                  </button>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Integrations Link */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.1 }}
        >
          <Link href="/settings/integrations">
            <Card variant="interactive" className="group">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="p-2 bg-accent-100 dark:bg-accent-900/30 rounded-lg">
                      <Plug className="w-5 h-5 text-accent-600 dark:text-accent-400" />
                    </div>
                    <div>
                      <p className="font-medium text-slate-900 dark:text-white">Integrations</p>
                      <p className="text-sm text-slate-500 dark:text-slate-400">
                        Connect your accounts and services
                      </p>
                    </div>
                  </div>
                  <ChevronRight className="w-5 h-5 text-slate-400 group-hover:text-slate-600 dark:group-hover:text-slate-300 transition-colors" />
                </div>
              </CardContent>
            </Card>
          </Link>
        </motion.div>

        {/* Profile Settings */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.2 }}
        >
          <Card>
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                  <User className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                </div>
                <div>
                  <CardTitle>Profile</CardTitle>
                  <CardDescription>Your account information</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <Input label="Name" placeholder="Your name" disabled />
              <Input label="Email" type="email" placeholder="your@email.com" disabled />
            </CardContent>
          </Card>
        </motion.div>

        {/* Notifications */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.3 }}
        >
          <Card>
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="p-2 bg-warning-100 dark:bg-warning-900/30 rounded-lg">
                  <Bell className="w-5 h-5 text-warning-600 dark:text-warning-400" />
                </div>
                <div>
                  <CardTitle>Notifications</CardTitle>
                  <CardDescription>Manage your notification preferences</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              <SettingToggle
                title="Email Notifications"
                description="Receive email updates"
                disabled
              />
              <div className="border-t border-slate-100 dark:border-slate-800 pt-6">
                <SettingToggle
                  title="Transaction Alerts"
                  description="Get notified of large transactions"
                  disabled
                />
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Privacy & Security */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.4 }}
        >
          <Card>
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="p-2 bg-success-100 dark:bg-success-900/30 rounded-lg">
                  <Shield className="w-5 h-5 text-success-600 dark:text-success-400" />
                </div>
                <div>
                  <CardTitle>Privacy & Security</CardTitle>
                  <CardDescription>Keep your data safe</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-slate-900 dark:text-white">Data Encryption</p>
                  <p className="text-sm text-slate-500 dark:text-slate-400">
                    All data is encrypted at rest
                  </p>
                </div>
                <Badge variant="success">
                  <Check className="w-3 h-3 mr-1" />
                  Enabled
                </Badge>
              </div>
              <div className="border-t border-slate-100 dark:border-slate-800 pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-slate-900 dark:text-white">
                      Two-Factor Authentication
                    </p>
                    <p className="text-sm text-slate-500 dark:text-slate-400">
                      Add an extra layer of security
                    </p>
                  </div>
                  <Button variant="secondary" size="sm" disabled>
                    Enable
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </PageLayout>
  );
}

interface SettingToggleProps {
  title: string;
  description: string;
  enabled?: boolean;
  onChange?: (enabled: boolean) => void;
  disabled?: boolean;
}

function SettingToggle({
  title,
  description,
  enabled = false,
  onChange,
  disabled = false,
}: SettingToggleProps) {
  return (
    <div className="flex items-center justify-between">
      <div>
        <p className="font-medium text-slate-900 dark:text-white">{title}</p>
        <p className="text-sm text-slate-500 dark:text-slate-400">{description}</p>
      </div>
      <button
        onClick={() => onChange?.(!enabled)}
        disabled={disabled}
        className={cn(
          "relative w-11 h-6 rounded-full transition-colors",
          enabled ? "bg-primary-600" : "bg-slate-200 dark:bg-slate-700",
          disabled && "opacity-50 cursor-not-allowed"
        )}
      >
        <span
          className={cn(
            "absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white shadow-sm transition-transform",
            enabled && "translate-x-5"
          )}
        />
      </button>
    </div>
  );
}
