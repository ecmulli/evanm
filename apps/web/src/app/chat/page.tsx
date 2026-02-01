'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, Upload, AlertCircle, Clock, User, Bot, LogOut, Menu, X, Sun, Zap, TrendingUp } from 'lucide-react';
import { getEnvironmentInfo } from '@/utils/environment';

interface SolarData {
  start_date?: string;
  end_date?: string;
  total_kwh?: number;
  average_daily_kwh?: number;
  production_kwh?: number;
  consumption_kwh?: number;
  net_kwh?: number;
  grid_independence_pct?: number;
  self_consumption_pct?: number;
  current_power_kw?: number;
  energy_today_kwh?: number;
  system_size_kw?: number;
  num_panels?: number;
  is_producing?: boolean;
  status?: string;
}

interface TaskData {
  task_name?: string;
  workspace?: string;
  priority?: string;
  estimated_hours?: number;
  due_date?: string;
  task_id?: string;
  task_url?: string;
}

interface ToolCall {
  tool_name: string;
  arguments: Record<string, unknown>;
  result?: {
    success: boolean;
    data?: Record<string, unknown>;
    summary?: string;
    error?: string;
  };
}

interface Message {
  id: string;
  content: string;
  type: 'user' | 'assistant' | 'system';
  timestamp: Date;
  solarData?: SolarData;
  taskData?: TaskData;
  toolCalls?: ToolCall[];
}

interface ConversationMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      content: 'Hi! I\'m your personal assistant. I can help you with:\n\n☀️ **Solar Data** - Check your solar production, consumption, and net energy usage\n📋 **Task Creation** - Create tasks in Notion with AI assistance\n\nJust ask me anything!',
      type: 'assistant',
      timestamp: new Date(),
    }
  ]);
  const [conversationHistory, setConversationHistory] = useState<ConversationMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { agentDomain } = getEnvironmentInfo();
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() && selectedFiles.length === 0) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: input,
      type: 'user',
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    
    // Add to conversation history
    const newHistory: ConversationMessage[] = [
      ...conversationHistory,
      { role: 'user', content: input }
    ];
    setConversationHistory(newHistory);
    
    setInput('');
    setIsLoading(true);

    try {
      const response = await sendAgentMessage(input, newHistory);
      
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: response.message || 'I received your message but couldn\'t generate a response.',
        type: 'assistant',
        timestamp: new Date(),
        solarData: response.solar_data,
        taskData: response.task_data,
        toolCalls: response.tool_calls,
      };
      
      setMessages(prev => [...prev, assistantMessage]);
      
      // Update conversation history with assistant response
      setConversationHistory(prev => [
        ...prev,
        { role: 'assistant', content: response.message || '' }
      ]);

      if (!response.success) {
        console.warn('Agent response indicated failure:', response);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: 'Failed to connect to the server. Please try again.',
        type: 'system',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      setSelectedFiles([]);
    }
  };

  const sendAgentMessage = async (
    message: string,
    history: ConversationMessage[]
  ): Promise<{
    success: boolean;
    message: string;
    tool_calls: ToolCall[];
    solar_data?: SolarData;
    task_data?: TaskData;
  }> => {
    const token = localStorage.getItem('bearerToken') || process.env.NEXT_PUBLIC_BEARER_TOKEN || '';
    
    console.log('🤖 Sending to agent:', message.substring(0, 50) + '...');

    const requestBody = {
      message,
      conversation_history: history.slice(-10), // Keep last 10 messages for context
      include_solar_context: true,
      include_task_context: true,
    };

    const response = await fetch('/api/v1/agent', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody),
    });

    console.log('📥 Agent Response:', response.status, response.statusText);
    
    const result = await response.json();
    console.log('📋 Response data:', result);
    
    return result;
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setSelectedFiles(Array.from(e.target.files));
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('bearerToken');
    document.cookie = 'bearerToken=; path=/; max-age=0';
    window.location.href = '/login';
  };

  const clearConversation = () => {
    setMessages([{
      id: '1',
      content: 'Hi! I\'m your personal assistant. I can help you with:\n\n☀️ **Solar Data** - Check your solar production, consumption, and net energy usage\n📋 **Task Creation** - Create tasks in Notion with AI assistance\n\nJust ask me anything!',
      type: 'assistant',
      timestamp: new Date(),
    }]);
    setConversationHistory([]);
  };

  const renderSolarData = (data: SolarData) => {
    // Determine what type of solar data this is
    const isNetEnergy = data.net_kwh !== undefined;
    const isSystemStatus = data.current_power_kw !== undefined;
    const isProduction = data.total_kwh !== undefined && !isNetEnergy;

    return (
      <div className="mt-3 p-4 bg-gradient-to-br from-amber-50 to-orange-50 rounded-lg border border-amber-200">
        <div className="flex items-center gap-2 mb-3">
          <Sun className="w-5 h-5 text-amber-600" />
          <h4 className="font-semibold text-amber-900">Solar Data</h4>
        </div>
        
        <div className="grid grid-cols-2 gap-3 text-sm">
          {/* Date Range */}
          {data.start_date && data.end_date && (
            <div className="col-span-2 text-amber-700 text-xs">
              {data.start_date} → {data.end_date}
            </div>
          )}

          {/* System Status */}
          {isSystemStatus && (
            <>
              <div className="bg-white/60 rounded-lg p-2">
                <div className="text-amber-600 text-xs">Current Power</div>
                <div className="text-lg font-bold text-amber-900 flex items-center gap-1">
                  <Zap className="w-4 h-4" />
                  {data.current_power_kw} kW
                </div>
              </div>
              <div className="bg-white/60 rounded-lg p-2">
                <div className="text-amber-600 text-xs">Today</div>
                <div className="text-lg font-bold text-amber-900">
                  {data.energy_today_kwh} kWh
                </div>
              </div>
              {data.system_size_kw && (
                <div className="bg-white/60 rounded-lg p-2">
                  <div className="text-amber-600 text-xs">System Size</div>
                  <div className="font-semibold text-amber-900">
                    {data.system_size_kw} kW ({data.num_panels} panels)
                  </div>
                </div>
              )}
              <div className="bg-white/60 rounded-lg p-2">
                <div className="text-amber-600 text-xs">Status</div>
                <div className={`font-semibold ${data.is_producing ? 'text-green-600' : 'text-gray-600'}`}>
                  {data.is_producing ? '🟢 Producing' : '⚫ Not Producing'}
                </div>
              </div>
            </>
          )}

          {/* Net Energy */}
          {isNetEnergy && (
            <>
              <div className="bg-white/60 rounded-lg p-2">
                <div className="text-amber-600 text-xs">Production</div>
                <div className="text-lg font-bold text-green-600">
                  {data.production_kwh} kWh
                </div>
              </div>
              <div className="bg-white/60 rounded-lg p-2">
                <div className="text-amber-600 text-xs">Consumption</div>
                <div className="text-lg font-bold text-blue-600">
                  {data.consumption_kwh} kWh
                </div>
              </div>
              <div className="bg-white/60 rounded-lg p-2">
                <div className="text-amber-600 text-xs">Net Energy</div>
                <div className={`text-lg font-bold flex items-center gap-1 ${
                  (data.net_kwh || 0) >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  <TrendingUp className="w-4 h-4" />
                  {(data.net_kwh || 0) >= 0 ? '+' : ''}{data.net_kwh} kWh
                </div>
              </div>
              {data.grid_independence_pct !== undefined && (
                <div className="bg-white/60 rounded-lg p-2">
                  <div className="text-amber-600 text-xs">Grid Independence</div>
                  <div className="text-lg font-bold text-amber-900">
                    {data.grid_independence_pct}%
                  </div>
                </div>
              )}
            </>
          )}

          {/* Production Only */}
          {isProduction && !isNetEnergy && !isSystemStatus && (
            <>
              <div className="bg-white/60 rounded-lg p-2">
                <div className="text-amber-600 text-xs">Total Production</div>
                <div className="text-lg font-bold text-green-600">
                  {data.total_kwh} kWh
                </div>
              </div>
              {data.average_daily_kwh && (
                <div className="bg-white/60 rounded-lg p-2">
                  <div className="text-amber-600 text-xs">Daily Average</div>
                  <div className="text-lg font-bold text-amber-900">
                    {data.average_daily_kwh} kWh/day
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    );
  };

  const renderTaskData = (data: TaskData) => {
    return (
      <div className="mt-3 p-4 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg border border-blue-200">
        <h4 className="font-semibold text-blue-900 mb-2">📋 Task Created</h4>
        <div className="space-y-1 text-sm text-blue-800">
          <div><strong>Name:</strong> {data.task_name}</div>
          <div><strong>Workspace:</strong> {data.workspace}</div>
          <div><strong>Priority:</strong> {data.priority}</div>
          {data.estimated_hours && (
            <div><strong>Estimated:</strong> {data.estimated_hours} hours</div>
          )}
          {data.task_url && (
            <div>
              <a 
                href={data.task_url} 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-blue-600 hover:text-blue-800 underline"
              >
                Open in Notion →
              </a>
            </div>
          )}
        </div>
      </div>
    );
  };

  const formatMessageContent = (content: string) => {
    // Simple markdown-like formatting
    return content.split('\n').map((line, i) => {
      // Bold text
      const formattedLine = line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
      return (
        <span key={i} dangerouslySetInnerHTML={{ __html: formattedLine }}>
        </span>
      );
    }).reduce((acc: React.ReactNode[], curr, i) => {
      if (i > 0) acc.push(<br key={`br-${i}`} />);
      acc.push(curr);
      return acc;
    }, []);
  };

  return (
    <div className="flex h-screen bg-gray-50 relative">
      {/* Mobile Menu Button */}
      <button
        onClick={() => setIsSidebarOpen(true)}
        className="md:hidden fixed top-4 left-4 z-40 p-2 rounded-lg bg-white border border-gray-200 shadow-lg"
      >
        <Menu size={20} className="text-gray-600" />
      </button>

      {/* Mobile Overlay */}
      {isSidebarOpen && (
        <div 
          className="md:hidden fixed inset-0 bg-black bg-opacity-50 z-40"
          onClick={() => setIsSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div className={`
        fixed md:static inset-y-0 left-0 z-50 w-80 bg-white border-r border-gray-200 flex flex-col
        transform transition-transform duration-300 ease-in-out
        ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
      `}>
        <div className="p-4 border-b border-gray-200 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold text-gray-900">AI Assistant</h1>
            <p className="text-sm text-gray-600">Solar & Task Management</p>
          </div>
          <button
            onClick={() => setIsSidebarOpen(false)}
            className="md:hidden p-1 rounded-lg hover:bg-gray-100"
          >
            <X size={20} className="text-gray-600" />
          </button>
        </div>
        
        <div className="flex-1 overflow-y-auto p-4">
          <h2 className="text-sm font-medium text-gray-900 mb-3">Capabilities</h2>
          <div className="space-y-2 mb-6">
            <div className="p-3 rounded-lg bg-amber-50 border border-amber-200">
              <div className="flex items-center gap-2">
                <Sun size={16} className="text-amber-600" />
                <span className="text-sm font-medium text-amber-900">Solar Data</span>
              </div>
              <div className="text-xs text-amber-700 mt-1">
                Production, consumption, net usage
              </div>
            </div>
            <div className="p-3 rounded-lg bg-blue-50 border border-blue-200">
              <div className="flex items-center gap-2">
                <span className="text-blue-600">📋</span>
                <span className="text-sm font-medium text-blue-900">Task Creation</span>
              </div>
              <div className="text-xs text-blue-700 mt-1">
                AI-powered Notion tasks
              </div>
            </div>
          </div>

          <h2 className="text-sm font-medium text-gray-900 mb-3">Session</h2>
          <div className="space-y-2">
            <div className="p-3 rounded-lg bg-gray-50 border border-gray-200">
              <div className="text-sm text-gray-900">{messages.length} messages</div>
              <button 
                onClick={clearConversation}
                className="text-xs text-gray-500 hover:text-gray-700 mt-1"
              >
                Clear conversation
              </button>
            </div>
          </div>

          <h2 className="text-sm font-medium text-gray-900 mb-3 mt-6">Example Questions</h2>
          <div className="space-y-2">
            {[
              "What's my solar production today?",
              "Show me my net energy this week",
              "Create a task to clean solar panels",
              "Is my system producing right now?",
            ].map((question, i) => (
              <button
                key={i}
                onClick={() => setInput(question)}
                className="w-full text-left p-2 text-xs text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              >
                "{question}"
              </button>
            ))}
          </div>
        </div>
        
        <div className="p-4 border-t border-gray-200">
          <button
            onClick={handleLogout}
            className="w-full flex items-center justify-center space-x-2 px-3 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg transition-colors"
          >
            <LogOut size={16} />
            <span>Logout</span>
          </button>
          <div className="text-xs text-gray-500 mt-2 text-center">
            Connected to {agentDomain}
          </div>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col md:ml-0">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 pt-16 md:pt-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div className={`flex max-w-full md:max-w-3xl ${message.type === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                <div className={`flex-shrink-0 ${message.type === 'user' ? 'ml-3' : 'mr-3'}`}>
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                    message.type === 'user' 
                      ? 'bg-blue-500 text-white' 
                      : message.type === 'assistant'
                      ? 'bg-green-500 text-white'
                      : 'bg-gray-500 text-white'
                  }`}>
                    {message.type === 'user' ? <User size={16} /> : message.type === 'assistant' ? <Bot size={16} /> : <AlertCircle size={16} />}
                  </div>
                </div>
                
                <div className={`rounded-2xl px-4 py-2 ${
                  message.type === 'user' 
                    ? 'bg-blue-500 text-white' 
                    : message.type === 'assistant'
                    ? 'bg-white border border-gray-200 text-gray-900'
                    : 'bg-yellow-50 border border-yellow-200 text-yellow-800'
                }`}>
                  <div className="text-sm">
                    {formatMessageContent(message.content)}
                  </div>
                  
                  {/* Solar Data Display */}
                  {message.solarData && renderSolarData(message.solarData)}
                  
                  {/* Task Data Display */}
                  {message.taskData && renderTaskData(message.taskData)}
                  
                  <div className="text-xs opacity-70 mt-2">
                    {message.timestamp.toLocaleTimeString()}
                  </div>
                </div>
              </div>
            </div>
          ))}
          
          {isLoading && (
            <div className="flex justify-start">
              <div className="flex mr-3">
                <div className="w-8 h-8 rounded-full bg-green-500 text-white flex items-center justify-center">
                  <Bot size={16} />
                </div>
              </div>
              <div className="bg-white border border-gray-200 rounded-2xl px-4 py-2">
                <div className="flex items-center space-x-2">
                  <Clock size={16} className="animate-spin text-gray-400" />
                  <span className="text-sm text-gray-600">Thinking...</span>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="border-t border-gray-200 bg-white p-4 pb-safe">
          {selectedFiles.length > 0 && (
            <div className="mb-3 flex flex-wrap gap-2">
              {selectedFiles.map((file, index) => (
                <div key={index} className="bg-blue-50 border border-blue-200 rounded-lg px-3 py-1 text-sm text-blue-800">
                  {file.name}
                  <button
                    onClick={() => setSelectedFiles(prev => prev.filter((_, i) => i !== index))}
                    className="ml-2 text-blue-600 hover:text-blue-800"
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          )}
          
          <form onSubmit={handleSubmit} className="flex items-end space-x-2 md:space-x-3">
            <div className="flex-1">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask about solar data, create tasks, or just chat..."
                className="w-full resize-none rounded-lg border border-gray-300 px-3 md:px-4 py-2 text-sm md:text-base focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                rows={2}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSubmit(e);
                  }
                }}
              />
            </div>
            
            <div className="flex space-x-1 md:space-x-2">
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileUpload}
                accept="image/*"
                multiple
                className="hidden"
              />
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="p-2 rounded-lg border border-gray-300 hover:bg-gray-50 transition-colors"
              >
                <Upload size={18} className="text-gray-600 md:w-5 md:h-5" />
              </button>
              
              <button
                type="submit"
                disabled={(!input.trim() && selectedFiles.length === 0) || isLoading}
                className="p-2 rounded-lg bg-blue-500 text-white hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <Send size={18} className="md:w-5 md:h-5" />
              </button>
            </div>
          </form>
          
          <div className="text-xs text-gray-500 mt-2">
            Press Enter to send, Shift+Enter for new line
          </div>
        </div>
      </div>
    </div>
  );
}
