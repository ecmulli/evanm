'use client';

import React, { useState } from 'react';
import { StickyNote } from '@/types/window';
import { initialNotes } from '@/data/content';

export default function Stickies() {
  const [notes, setNotes] = useState<StickyNote[]>(initialNotes);
  const [author, setAuthor] = useState('');
  const [message, setMessage] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!author.trim() || !message.trim()) {
      return;
    }

    const newNote: StickyNote = {
      id: `note-${Date.now()}`,
      author: author.trim(),
      message: message.trim(),
      createdAt: new Date(),
    };

    setNotes([newNote, ...notes]);
    setAuthor('');
    setMessage('');
  };

  const formatDate = (date: Date) => {
    return new Date(date).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  return (
    <div className="h-full flex flex-col" style={{ backgroundColor: '#F5EFE6' }}>
      {/* Leave a Note Form */}
      <div className="p-3 border-b-2 border-[#BEA09A]">
        <h3 className="font-bold text-xs mb-2">Leave a Note</h3>
        <form onSubmit={handleSubmit} className="space-y-2">
          <div>
            <input
              type="text"
              placeholder="Your name"
              value={author}
              onChange={(e) => setAuthor(e.target.value)}
              className="retro-input w-full"
              maxLength={50}
            />
          </div>
          <div>
            <textarea
              placeholder="Your message..."
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              className="retro-textarea w-full"
              rows={3}
              maxLength={280}
            />
          </div>
          <button type="submit" className="retro-button">
            Post Note
          </button>
        </form>
      </div>

      {/* Notes List */}
      <div className="flex-1 overflow-auto p-3">
        <h3 className="font-bold text-xs mb-2">Guestbook ({notes.length})</h3>
        <div className="space-y-2">
          {notes.map((note) => (
            <div key={note.id} className="sticky-note">
              <div className="flex justify-between items-start mb-1">
                <span className="font-bold text-xs">{note.author}</span>
                <span className="text-[10px] text-gray-600">
                  {formatDate(note.createdAt)}
                </span>
              </div>
              <p className="text-xs whitespace-pre-wrap">{note.message}</p>
            </div>
          ))}
          {notes.length === 0 && (
            <p className="text-xs text-gray-600 italic">
              No notes yet. Be the first to leave one!
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
