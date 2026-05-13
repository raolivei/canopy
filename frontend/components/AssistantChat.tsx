import { useState, useRef, useEffect } from 'react';
import { Button } from './ui/Button';
import { Input } from './ui/Input';
import { Copy, Check, TrendingUp, DollarSign, PieChart, Calendar } from 'lucide-react';

interface Message {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  functionsCalled?: any[];
  createdAt: string;
}

interface AssistantChatProps {
  conversationId?: number;
  onConversationStart?: (id: number) => void;
}

const SUGGESTED_QUESTIONS = [
  { icon: DollarSign, text: "How much did I spend this month?", category: "Spending" },
  { icon: TrendingUp, text: "Show my biggest expenses last week", category: "Analysis" },
  { icon: PieChart, text: "Break down my spending by category", category: "Insights" },
  { icon: Calendar, text: "What were my transactions yesterday?", category: "Recent" },
];

export function AssistantChat({ conversationId, onConversationStart }: AssistantChatProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [copiedId, setCopiedId] = useState<number | null>(null);
  const [currentConversationId, setCurrentConversationId] = useState<number | undefined>(conversationId);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const API_URL = process.env.NEXT_PUBLIC_API_URL;

  useEffect(() => {
    if (conversationId) {
      loadConversation(conversationId);
    }
  }, [conversationId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadConversation = async (id: number) => {
    try {
      const res = await fetch(`${API_URL}/v1/assistant/conversations/${id}`);
      const data = await res.json();
      setMessages(data.messages);
      setCurrentConversationId(data.id);
    } catch (error) {
      console.error('Failed to load conversation:', error);
    }
  };

  const copyToClipboard = async (text: string, messageId: number) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedId(messageId);
      setTimeout(() => setCopiedId(null), 2000);
    } catch (error) {
      console.error('Failed to copy:', error);
    }
  };

  const sendMessage = async (text?: string) => {
    const messageText = text || input.trim();
    if (!messageText || loading) return;

    setInput('');
    setLoading(true);

    const tempUserMsg: Message = {
      id: Date.now(),
      role: 'user',
      content: messageText,
      createdAt: new Date().toISOString(),
    };
    setMessages(prev => [...prev, tempUserMsg]);

    try {
      const res = await fetch(`${API_URL}/v1/assistant/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: messageText,
          conversation_id: currentConversationId,
        }),
      });

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }

      const data = await res.json();

      if (!currentConversationId) {
        setCurrentConversationId(data.conversation_id);
        onConversationStart?.(data.conversation_id);
      }

      const assistantMsg: Message = {
        id: data.message_id,
        role: 'assistant',
        content: data.response,
        functionsCalled: data.functions_called,
        createdAt: new Date().toISOString(),
      };
      setMessages(prev => [...prev, assistantMsg]);
    } catch (error) {
      console.error('Failed to send message:', error);
      setMessages(prev => [
        ...prev,
        {
          id: Date.now(),
          role: 'assistant',
          content: '❌ Sorry, I encountered an error. Please check that the AI service is running and try again.',
          createdAt: new Date().toISOString(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const startNewConversation = () => {
    setMessages([]);
    setCurrentConversationId(undefined);
  };

  return (
    <div className="flex flex-col h-full bg-gradient-to-b from-slate-50 to-white dark:from-slate-900 dark:to-slate-950">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center space-y-6 py-8">
            {/* Welcome Message */}
            <div className="space-y-3">
              <div className="text-5xl">✨</div>
              <h3 className="text-xl font-semibold text-slate-900 dark:text-white">
                AI Financial Assistant
              </h3>
              <p className="text-sm text-slate-600 dark:text-slate-400 max-w-sm mx-auto">
                Ask me anything about your transactions, spending patterns, or portfolio performance
              </p>
            </div>

            {/* Suggested Questions */}
            <div className="space-y-3 max-w-md mx-auto">
              <p className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                Try asking
              </p>
              <div className="grid grid-cols-1 gap-2">
                {SUGGESTED_QUESTIONS.map((question, idx) => {
                  const Icon = question.icon;
                  return (
                    <button
                      key={idx}
                      onClick={() => sendMessage(question.text)}
                      className="group flex items-center gap-3 p-3 bg-white dark:bg-slate-800 hover:bg-primary-50 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700 rounded-xl transition-all hover:shadow-md hover:scale-[1.02] text-left"
                    >
                      <div className="flex-shrink-0 w-8 h-8 bg-primary-100 dark:bg-primary-900/30 rounded-lg flex items-center justify-center group-hover:bg-primary-200 dark:group-hover:bg-primary-900/50 transition-colors">
                        <Icon className="w-4 h-4 text-primary-600 dark:text-primary-400" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-slate-900 dark:text-white truncate">
                          {question.text}
                        </p>
                        <p className="text-xs text-slate-500 dark:text-slate-400">
                          {question.category}
                        </p>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} group`}
          >
            <div
              className={`max-w-[85%] rounded-2xl px-4 py-3 shadow-sm relative ${
                message.role === 'user'
                  ? 'bg-gradient-to-br from-primary-600 to-primary-700 text-white rounded-br-sm'
                  : 'bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 rounded-bl-sm border border-slate-200 dark:border-slate-700'
              }`}
            >
              <p className="whitespace-pre-wrap leading-relaxed text-sm">{message.content}</p>
              
              {/* Function Calls */}
              {message.functionsCalled && message.functionsCalled.length > 0 && (
                <div className="mt-3 pt-3 border-t border-white/10 dark:border-slate-700">
                  <details className="cursor-pointer group/details">
                    <summary className="text-xs opacity-70 hover:opacity-100 transition-opacity flex items-center gap-2">
                      <span className="inline-block w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse" />
                      Analyzed {message.functionsCalled.length} data source{message.functionsCalled.length > 1 ? 's' : ''}
                    </summary>
                    <ul className="mt-2 space-y-1 pl-4 text-xs opacity-70">
                      {message.functionsCalled.map((fc, idx) => (
                        <li key={idx} className="list-disc">{fc.name}</li>
                      ))}
                    </ul>
                  </details>
                </div>
              )}

              {/* Copy Button (Assistant only) */}
              {message.role === 'assistant' && (
                <button
                  onClick={() => copyToClipboard(message.content, message.id)}
                  className="absolute -right-2 -top-2 opacity-0 group-hover:opacity-100 transition-opacity bg-white dark:bg-slate-700 hover:bg-slate-100 dark:hover:bg-slate-600 p-1.5 rounded-lg shadow-md border border-slate-200 dark:border-slate-600"
                  title="Copy message"
                >
                  {copiedId === message.id ? (
                    <Check className="w-3.5 h-3.5 text-green-600" />
                  ) : (
                    <Copy className="w-3.5 h-3.5 text-slate-600 dark:text-slate-300" />
                  )}
                </button>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-white dark:bg-slate-800 rounded-2xl rounded-bl-sm px-4 py-3 shadow-sm border border-slate-200 dark:border-slate-700">
              <div className="flex items-center space-x-3">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-primary-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <div className="w-2 h-2 bg-primary-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <div className="w-2 h-2 bg-primary-600 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
                <span className="text-sm text-slate-600 dark:text-slate-400">Analyzing your data...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t border-slate-200 dark:border-slate-700 p-4 bg-white dark:bg-slate-900 space-y-2">
        {/* New Conversation Button */}
        {messages.length > 0 && (
          <button
            onClick={startNewConversation}
            className="text-xs text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 font-medium transition-colors"
          >
            + Start new conversation
          </button>
        )}
        
        <div className="flex space-x-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask about your finances..."
            disabled={loading}
            className="flex-1 rounded-full bg-slate-50 dark:bg-slate-800 border-slate-200 dark:border-slate-700 focus:border-primary-500 dark:focus:border-primary-500"
          />
          <Button 
            onClick={() => sendMessage()} 
            disabled={loading || !input.trim()}
            className="rounded-full px-6 bg-gradient-to-r from-primary-600 to-primary-700 hover:from-primary-700 hover:to-primary-800 shadow-lg hover:shadow-xl transition-all"
          >
            {loading ? '...' : 'Send'}
          </Button>
        </div>
      </div>
    </div>
  );
}
