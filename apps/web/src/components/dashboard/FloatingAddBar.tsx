'use client';

import { useState, useRef, useCallback, useEffect } from 'react';
import { Plus, Loader2 } from 'lucide-react';
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

interface FloatingAddBarProps {
  onAdd: (text: string, domain: TaskDomain) => Promise<void>;
}

export function FloatingAddBar({ onAdd }: FloatingAddBarProps) {
  const [inputValue, setInputValue] = useState('');
  const [selectedDomain, setSelectedDomain] = useState<TaskDomain>('personal');
  const [isAdding, setIsAdding] = useState(false);
  const [isFocused, setIsFocused] = useState(false);
  const [keyboardOffset, setKeyboardOffset] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

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
    try {
      await onAdd(text, selectedDomain);
      setInputValue('');
      inputRef.current?.focus();
    } catch (err) {
      console.error('Failed to add todo:', err);
    } finally {
      setIsAdding(false);
    }
  }, [inputValue, selectedDomain, isAdding, onAdd]);

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
        </div>

        {/* Input row */}
        <div className="flex items-center gap-2 px-3.5 pb-3.5">
          <input
            ref={inputRef}
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleAdd();
            }}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            placeholder="Add a to-do..."
            className="flex-1 bg-transparent text-[16px] text-[#1A1714] placeholder-[#A8A29E] focus:outline-none font-sans leading-none py-1"
            disabled={isAdding}
            aria-label="New to-do"
            style={{ WebkitTapHighlightColor: 'transparent' }}
          />
          <button
            onClick={handleAdd}
            disabled={!inputValue.trim() || isAdding}
            aria-label="Add to-do"
            className="w-9 h-9 flex-shrink-0 flex items-center justify-center rounded-xl text-white transition-all duration-200 active:scale-90 disabled:opacity-30"
            style={{ backgroundColor: domainColor }}
          >
            {isAdding ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Plus className="w-4 h-4" strokeWidth={2.5} />
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
