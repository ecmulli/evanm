'use client';

import { useState, useRef, useCallback, useEffect } from 'react';
import { Plus, Loader2, Sparkles, ExternalLink, X } from 'lucide-react';
import type { TaskDomain } from '@/server/dashboard/types';
import { DOMAIN_CONFIG } from '@/server/dashboard/types';

const DOMAINS: TaskDomain[] = ['work', 'career', 'personal'];

const DOMAIN_PILL_STYLES: Record<TaskDomain, { active: string; inactive: string }> = {
  work: {
    active: 'bg-[#1C2B4A] text-white shadow-sm',
    inactive: 'bg-white/30 text-[#1C2B4A] hover:bg-white/50',
  },
  career: {
    active: 'bg-[#4A6B3A] text-white shadow-sm',
    inactive: 'bg-white/30 text-[#4A6B3A] hover:bg-white/50',
  },
  personal: {
    active: 'bg-[#A05040] text-white shadow-sm',
    inactive: 'bg-white/30 text-[#A05040] hover:bg-white/50',
  },
};

interface CreatedTask {
  title: string;
  domain: TaskDomain;
  url: string;
  database: string;
}

interface FloatingAddBarProps {
  onAdd: (text: string, domain: TaskDomain) => Promise<void>;
  onSmartAdd?: (text: string, domain: TaskDomain) => Promise<unknown>;
}

export function FloatingAddBar({ onAdd, onSmartAdd }: FloatingAddBarProps) {
  const [inputValue, setInputValue] = useState('');
  const [selectedDomain, setSelectedDomain] = useState<TaskDomain>('personal');
  const [isAdding, setIsAdding] = useState(false);
  const [isFocused, setIsFocused] = useState(false);
  const [keyboardOffset, setKeyboardOffset] = useState(0);
  const [isSmartMode, setIsSmartMode] = useState(false);
  const [smartError, setSmartError] = useState<string | null>(null);
  const [createdTask, setCreatedTask] = useState<CreatedTask | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-dismiss confirmation after 6 seconds
  useEffect(() => {
    if (!createdTask) return;
    const timer = setTimeout(() => setCreatedTask(null), 6000);
    return () => clearTimeout(timer);
  }, [createdTask]);

  // Track visualViewport so the bar floats above the iOS keyboard
  useEffect(() => {
    const vv = window.visualViewport;
    if (!vv) return;

    const update = () => {
      // How many px the keyboard is pushing the viewport up from the bottom
      const offset = window.innerHeight - vv.height - vv.offsetTop;
      setKeyboardOffset(Math.max(0, offset));
    };

    vv.addEventListener('resize', update);
    vv.addEventListener('scroll', update);
    update();

    return () => {
      vv.removeEventListener('resize', update);
      vv.removeEventListener('scroll', update);
    };
  }, []);

  const handleAdd = useCallback(async () => {
    const text = inputValue.trim();
    if (!text || isAdding) return;

    setIsAdding(true);
    setSmartError(null);

    try {
      if (isSmartMode && onSmartAdd) {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const result: any = await onSmartAdd(text, selectedDomain);
        setInputValue('');
        setCreatedTask({
          title: result.task.title,
          domain: result.task.domain,
          url: result.task.url,
          database: result.task.database,
        });
        inputRef.current?.focus();
      } else {
        await onAdd(text, selectedDomain);
        setInputValue('');
        inputRef.current?.focus();
      }
    } catch (err) {
      if (isSmartMode) {
        setSmartError(
          err instanceof Error ? err.message : 'Failed to create task',
        );
      } else {
        console.error('Failed to add todo:', err);
      }
    } finally {
      setIsAdding(false);
    }
  }, [inputValue, selectedDomain, isAdding, isSmartMode, onAdd, onSmartAdd]);

  const domainColor = {
    work: '#1C2B4A',
    career: '#4A6B3A',
    personal: '#A05040',
  }[selectedDomain];

  return (
    <div
      className="fixed left-0 right-0 z-50 flex justify-center"
      style={{
        bottom: keyboardOffset,
        transition: 'bottom 0.25s cubic-bezier(0.32, 0.72, 0, 1)',
      }}
    >
      {/* The bar itself */}
      <div
        className={`
          mx-4 mb-5 w-full max-w-2xl
          rounded-2xl
          border border-white/40
          shadow-[0_8px_32px_rgba(0,0,0,0.18),0_2px_8px_rgba(0,0,0,0.10),inset_0_1px_0_rgba(255,255,255,0.6)]
          transition-all duration-300
          ${isFocused ? 'shadow-[0_12px_40px_rgba(0,0,0,0.22),0_2px_8px_rgba(0,0,0,0.12),inset_0_1px_0_rgba(255,255,255,0.7)]' : ''}
        `}
        style={{
          background: 'rgba(245, 243, 240, 0.78)',
          backdropFilter: 'blur(28px) saturate(1.8)',
          WebkitBackdropFilter: 'blur(28px) saturate(1.8)',
        }}
      >
        {/* Task creation confirmation */}
        {createdTask && (
          <div
            className="flex items-center gap-2 px-3.5 pt-3 pb-1 text-xs animate-in fade-in slide-in-from-bottom-2"
            style={{ color: DOMAIN_CONFIG[createdTask.domain].color }}
          >
            <Sparkles className="w-3 h-3 flex-shrink-0" />
            <span className="font-medium truncate">{createdTask.title}</span>
            <span className="text-[10px] opacity-60 flex-shrink-0">
              → {createdTask.database.replace('_', ' ')}
            </span>
            <a
              href={createdTask.url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex-shrink-0 hover:opacity-70 transition-opacity"
            >
              <ExternalLink className="w-3 h-3" />
            </a>
            <button
              onClick={() => setCreatedTask(null)}
              className="flex-shrink-0 opacity-40 hover:opacity-70 transition-opacity ml-auto"
            >
              <X className="w-3 h-3" />
            </button>
          </div>
        )}

        {/* Smart mode error */}
        {smartError && (
          <div className="flex items-center gap-2 px-3.5 pt-3 pb-1">
            <span className="text-xs text-[#A0584A] truncate">{smartError}</span>
            <button
              onClick={() => setSmartError(null)}
              className="flex-shrink-0 text-[#A0584A] opacity-40 hover:opacity-70"
            >
              <X className="w-3 h-3" />
            </button>
          </div>
        )}

        {/* Domain pills row */}
        <div className="flex items-center gap-1.5 px-3.5 pt-3 pb-2">
          {DOMAINS.map((d) => {
            const styles = DOMAIN_PILL_STYLES[d];
            const config = DOMAIN_CONFIG[d];
            return (
              <button
                key={d}
                onClick={() => setSelectedDomain(d)}
                className={`px-3 py-1 rounded-full text-xs font-medium transition-all duration-200 ${
                  selectedDomain === d ? styles.active : styles.inactive
                }`}
              >
                {config.label}
              </button>
            );
          })}

          {/* Smart mode toggle */}
          {onSmartAdd && (
            <button
              onClick={() => {
                setIsSmartMode(!isSmartMode);
                setSmartError(null);
                setCreatedTask(null);
              }}
              className="ml-auto flex-shrink-0 w-7 h-7 flex items-center justify-center rounded-lg transition-all duration-200"
              style={{
                backgroundColor: isSmartMode ? domainColor : 'transparent',
                color: isSmartMode ? '#fff' : '#A8A29E',
              }}
              title={
                isSmartMode
                  ? 'Smart mode: AI creates a full task'
                  : 'Quick mode: saves as-is'
              }
            >
              <Sparkles className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        {/* Smart mode hint */}
        {isSmartMode && !isAdding && !smartError && !createdTask && (
          <div
            className="text-[10px] px-3.5 pb-1 opacity-50"
            style={{ color: domainColor }}
          >
            AI will route to the right tracker with inferred properties
          </div>
        )}

        {/* Loading state for smart mode */}
        {isSmartMode && isAdding && (
          <div
            className="flex items-center gap-1.5 px-3.5 pb-1 text-[11px]"
            style={{ color: domainColor }}
          >
            <Loader2 className="w-3 h-3 animate-spin" />
            Creating task with AI...
          </div>
        )}

        {/* Input row */}
        <div className="flex items-center gap-2 px-3.5 pb-3.5">
          <input
            ref={inputRef}
            type="text"
            value={inputValue}
            onChange={(e) => {
              setInputValue(e.target.value);
              if (smartError) setSmartError(null);
            }}
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleAdd();
            }}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            placeholder={isSmartMode ? 'Describe a task...' : 'Add a to-do...'}
            className="flex-1 bg-transparent text-[16px] text-[#1A1714] placeholder-[#A8A29E] focus:outline-none font-sans leading-none py-1"
            disabled={isAdding}
            aria-label={isSmartMode ? 'Describe a task' : 'New to-do'}
            style={{ WebkitTapHighlightColor: 'transparent' }}
          />
          <button
            onClick={handleAdd}
            disabled={!inputValue.trim() || isAdding}
            aria-label={isSmartMode ? 'Create smart task' : 'Add to-do'}
            className="w-9 h-9 flex-shrink-0 flex items-center justify-center rounded-xl text-white transition-all duration-200 active:scale-90 disabled:opacity-30"
            style={{ backgroundColor: domainColor }}
          >
            {isAdding ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : isSmartMode ? (
              <Sparkles className="w-4 h-4" />
            ) : (
              <Plus className="w-4 h-4" strokeWidth={2.5} />
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
