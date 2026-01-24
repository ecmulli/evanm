'use client';

import React, { ReactNode, useRef } from 'react';
import Draggable, { DraggableEvent, DraggableData } from 'react-draggable';
import { useWindow } from '@/hooks/useWindow';
import { useIsMobile } from '@/hooks/useIsMobile';
import { Position } from '@/types/window';

interface WindowFrameProps {
  id: string;
  title: string;
  children: ReactNode;
  position: Position;
  zIndex: number;
  width?: number;
  height?: number;
  minWidth?: number;
  minHeight?: number;
  onClose: () => void;
  onPositionChange?: (position: Position) => void;
}

export default function WindowFrame({
  id,
  title,
  children,
  position,
  zIndex,
  width = 400,
  height = 300,
  minWidth = 200,
  minHeight = 150,
  onClose,
  onPositionChange,
}: WindowFrameProps) {
  const { focusWindow, isWindowFocused } = useWindow();
  const nodeRef = useRef<HTMLDivElement>(null);
  const isActive = isWindowFocused(id);
  const isMobile = useIsMobile();

  const handleDragStart = () => {
    focusWindow(id);
  };

  const handleDragStop = (_e: DraggableEvent, data: DraggableData) => {
    if (onPositionChange) {
      onPositionChange({ x: data.x, y: data.y });
    }
  };

  const handleMouseDown = () => {
    focusWindow(id);
  };

  // Mobile: full-width, fixed position, no dragging
  if (isMobile) {
    return (
      <div
        ref={nodeRef}
        className="retro-window absolute left-0 right-0 mx-2"
        style={{
          top: '8px',
          height: 'calc(100% - 16px)',
          zIndex,
        }}
        onTouchStart={handleMouseDown}
      >
        {/* Title Bar */}
        <div className={`retro-titlebar ${isActive ? 'retro-titlebar-active' : ''}`}>
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
          <span className="retro-titlebar-title flex-1 text-center">
            {title}
          </span>
          <div className="w-[13px]" />
        </div>

        {/* Window Content */}
        <div
          className="overflow-auto bg-white"
          style={{ height: 'calc(100% - 26px)' }}
        >
          {children}
        </div>
      </div>
    );
  }

  // Desktop: draggable windows
  return (
    <Draggable
      nodeRef={nodeRef}
      handle=".window-handle"
      position={position}
      bounds="parent"
      onStart={handleDragStart}
      onStop={handleDragStop}
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
