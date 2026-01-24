'use client';

import React, { ReactNode, useRef } from 'react';
import Draggable, { DraggableEvent, DraggableData } from 'react-draggable';
import { useWindow } from '@/hooks/useWindow';
import { Position } from '@/types/window';

interface WindowFrameProps {
  id: string;
  title: string;
  children: ReactNode;
  initialPosition: Position;
  zIndex: number;
  width?: number;
  height?: number;
  minWidth?: number;
  minHeight?: number;
  onClose: () => void;
}

export default function WindowFrame({
  id,
  title,
  children,
  initialPosition,
  zIndex,
  width = 400,
  height = 300,
  minWidth = 200,
  minHeight = 150,
  onClose,
}: WindowFrameProps) {
  const { focusWindow, isWindowFocused } = useWindow();
  const nodeRef = useRef<HTMLDivElement>(null);
  const isActive = isWindowFocused(id);

  const handleDragStart = (e: DraggableEvent, data: DraggableData) => {
    focusWindow(id);
  };

  const handleMouseDown = () => {
    focusWindow(id);
  };

  return (
    <Draggable
      nodeRef={nodeRef}
      handle=".window-handle"
      defaultPosition={initialPosition}
      bounds="parent"
      onStart={handleDragStart}
    >
      <div
        ref={nodeRef}
        className="retro-window absolute"
        style={{
          width: `${width}px`,
          minWidth: `${minWidth}px`,
          height: `${height}px`,
          minHeight: `${minHeight}px`,
          zIndex,
        }}
        onMouseDown={handleMouseDown}
      >
        {/* Title Bar */}
        <div
          className={`retro-titlebar window-handle ${isActive ? 'retro-titlebar-active' : ''}`}
        >
          {/* Close Button */}
          <button
            className="retro-close-btn"
            onClick={(e) => {
              e.stopPropagation();
              onClose();
            }}
            aria-label="Close window"
          >
            ×
          </button>

          {/* Title */}
          <span className="retro-titlebar-title flex-1 text-center">
            {title}
          </span>

          {/* Spacer for symmetry */}
          <div className="w-[13px]" />
        </div>

        {/* Window Content */}
        <div
          className="overflow-auto bg-white"
          style={{
            height: `calc(100% - 26px)`,
          }}
        >
          {children}
        </div>
      </div>
    </Draggable>
  );
}
