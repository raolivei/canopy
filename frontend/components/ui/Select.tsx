import React, { forwardRef, useState, useRef, useEffect } from "react";
import { ChevronDown, Check, X } from "lucide-react";
import { cn } from "@/utils/cn";

export interface SelectOption {
  value: string;
  label: string;
  icon?: React.ReactNode;
  disabled?: boolean;
}

export interface SelectProps {
  options: SelectOption[];
  value?: string;
  onChange?: (value: string) => void;
  placeholder?: string;
  label?: string;
  error?: string;
  disabled?: boolean;
  className?: string;
  searchable?: boolean;
}

const Select = forwardRef<HTMLDivElement, SelectProps>(
  (
    {
      options,
      value,
      onChange,
      placeholder = "Select...",
      label,
      error,
      disabled = false,
      className,
      searchable = false,
    },
    ref
  ) => {
    const [isOpen, setIsOpen] = useState(false);
    const [searchQuery, setSearchQuery] = useState("");
    const containerRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);

    const selectedOption = options.find((opt) => opt.value === value);

    const filteredOptions = searchable
      ? options.filter((opt) =>
          opt.label.toLowerCase().includes(searchQuery.toLowerCase())
        )
      : options;

    useEffect(() => {
      const handleClickOutside = (event: MouseEvent) => {
        if (
          containerRef.current &&
          !containerRef.current.contains(event.target as Node)
        ) {
          setIsOpen(false);
          setSearchQuery("");
        }
      };

      document.addEventListener("mousedown", handleClickOutside);
      return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    useEffect(() => {
      if (isOpen && searchable && inputRef.current) {
        inputRef.current.focus();
      }
    }, [isOpen, searchable]);

    const handleSelect = (optionValue: string) => {
      onChange?.(optionValue);
      setIsOpen(false);
      setSearchQuery("");
    };

    return (
      <div ref={ref} className={cn("w-full", className)}>
        {label && (
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">
            {label}
          </label>
        )}
        <div ref={containerRef} className="relative">
          <button
            type="button"
            onClick={() => !disabled && setIsOpen(!isOpen)}
            disabled={disabled}
            className={cn(
              "w-full flex items-center justify-between gap-2 px-3 py-2 text-sm",
              "bg-white dark:bg-slate-900",
              "border border-slate-300 dark:border-slate-700 rounded-md",
              "text-left transition-colors duration-150",
              "focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500",
              "disabled:opacity-50 disabled:cursor-not-allowed",
              error && "border-danger-500",
              isOpen && "ring-2 ring-primary-500 border-primary-500"
            )}
          >
            <span
              className={cn(
                "flex items-center gap-2 truncate",
                !selectedOption && "text-slate-400 dark:text-slate-500"
              )}
            >
              {selectedOption?.icon}
              {selectedOption?.label || placeholder}
            </span>
            <ChevronDown
              className={cn(
                "w-4 h-4 text-slate-400 transition-transform duration-150",
                isOpen && "rotate-180"
              )}
            />
          </button>

          {isOpen && (
            <div className="absolute z-50 w-full mt-1 py-1 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-md shadow-lg animate-fade-in">
              {searchable && (
                <div className="px-2 pb-2">
                  <input
                    ref={inputRef}
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search..."
                    className="w-full px-2 py-1.5 text-sm bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded focus:outline-none focus:ring-1 focus:ring-primary-500"
                  />
                </div>
              )}
              <div className="max-h-60 overflow-auto">
                {filteredOptions.length === 0 ? (
                  <div className="px-3 py-2 text-sm text-slate-500 dark:text-slate-400">
                    No options found
                  </div>
                ) : (
                  filteredOptions.map((option) => (
                    <button
                      key={option.value}
                      type="button"
                      onClick={() => !option.disabled && handleSelect(option.value)}
                      disabled={option.disabled}
                      className={cn(
                        "w-full flex items-center justify-between gap-2 px-3 py-2 text-sm text-left",
                        "hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors",
                        option.disabled && "opacity-50 cursor-not-allowed",
                        option.value === value && "bg-primary-50 dark:bg-primary-950/50"
                      )}
                    >
                      <span className="flex items-center gap-2 truncate">
                        {option.icon}
                        {option.label}
                      </span>
                      {option.value === value && (
                        <Check className="w-4 h-4 text-primary-600 dark:text-primary-400" />
                      )}
                    </button>
                  ))
                )}
              </div>
            </div>
          )}
        </div>
        {error && (
          <p className="text-xs text-danger-600 dark:text-danger-400 mt-1">
            {error}
          </p>
        )}
      </div>
    );
  }
);

Select.displayName = "Select";

export interface MultiSelectProps {
  options: SelectOption[];
  value: string[];
  onChange: (value: string[]) => void;
  placeholder?: string;
  label?: string;
  error?: string;
  disabled?: boolean;
  className?: string;
}

const MultiSelect = forwardRef<HTMLDivElement, MultiSelectProps>(
  (
    {
      options,
      value = [],
      onChange,
      placeholder = "Select...",
      label,
      error,
      disabled = false,
      className,
    },
    ref
  ) => {
    const [isOpen, setIsOpen] = useState(false);
    const containerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
      const handleClickOutside = (event: MouseEvent) => {
        if (
          containerRef.current &&
          !containerRef.current.contains(event.target as Node)
        ) {
          setIsOpen(false);
        }
      };

      document.addEventListener("mousedown", handleClickOutside);
      return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    const handleToggle = (optionValue: string) => {
      if (value.includes(optionValue)) {
        onChange(value.filter((v) => v !== optionValue));
      } else {
        onChange([...value, optionValue]);
      }
    };

    const handleRemove = (optionValue: string, e: React.MouseEvent) => {
      e.stopPropagation();
      onChange(value.filter((v) => v !== optionValue));
    };

    const selectedOptions = options.filter((opt) => value.includes(opt.value));

    return (
      <div ref={ref} className={cn("w-full", className)}>
        {label && (
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">
            {label}
          </label>
        )}
        <div ref={containerRef} className="relative">
          <button
            type="button"
            onClick={() => !disabled && setIsOpen(!isOpen)}
            disabled={disabled}
            className={cn(
              "w-full flex items-center justify-between gap-2 px-3 py-2 text-sm min-h-[38px]",
              "bg-white dark:bg-slate-900",
              "border border-slate-300 dark:border-slate-700 rounded-md",
              "text-left transition-colors duration-150",
              "focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500",
              "disabled:opacity-50 disabled:cursor-not-allowed",
              error && "border-danger-500",
              isOpen && "ring-2 ring-primary-500 border-primary-500"
            )}
          >
            <div className="flex flex-wrap gap-1 flex-1">
              {selectedOptions.length === 0 ? (
                <span className="text-slate-400 dark:text-slate-500">
                  {placeholder}
                </span>
              ) : (
                selectedOptions.map((option) => (
                  <span
                    key={option.value}
                    className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium bg-primary-100 dark:bg-primary-900/50 text-primary-700 dark:text-primary-300 rounded"
                  >
                    {option.label}
                    <X
                      className="w-3 h-3 cursor-pointer hover:text-primary-900"
                      onClick={(e) => handleRemove(option.value, e)}
                    />
                  </span>
                ))
              )}
            </div>
            <ChevronDown
              className={cn(
                "w-4 h-4 text-slate-400 shrink-0 transition-transform duration-150",
                isOpen && "rotate-180"
              )}
            />
          </button>

          {isOpen && (
            <div className="absolute z-50 w-full mt-1 py-1 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-md shadow-lg animate-fade-in max-h-60 overflow-auto">
              {options.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => !option.disabled && handleToggle(option.value)}
                  disabled={option.disabled}
                  className={cn(
                    "w-full flex items-center justify-between gap-2 px-3 py-2 text-sm text-left",
                    "hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors",
                    option.disabled && "opacity-50 cursor-not-allowed",
                    value.includes(option.value) && "bg-primary-50 dark:bg-primary-950/50"
                  )}
                >
                  <span className="flex items-center gap-2 truncate">
                    {option.icon}
                    {option.label}
                  </span>
                  {value.includes(option.value) && (
                    <Check className="w-4 h-4 text-primary-600 dark:text-primary-400" />
                  )}
                </button>
              ))}
            </div>
          )}
        </div>
        {error && (
          <p className="text-xs text-danger-600 dark:text-danger-400 mt-1">
            {error}
          </p>
        )}
      </div>
    );
  }
);

MultiSelect.displayName = "MultiSelect";

export { Select, MultiSelect };
