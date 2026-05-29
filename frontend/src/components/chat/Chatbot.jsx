import React, { useState, useEffect, useRef } from 'react';
import { Send, Bot, User, X, MessageSquare, Sparkles } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function Chatbot() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    { role: 'assistant', content: '👋 Bonjour ! Je suis **SOC Copilot**, votre assistant expert en cybersécurité.\n\nJe peux vous aider à :\n• Analyser les alertes de sécurité\n• Investiguer les incidents\n• Expliquer les techniques MITRE ATT&CK\n• Recommander des actions de remédiation\n\nPosez-moi une question !' }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const ws = useRef(null);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  
  const clientId = useRef("client_" + Math.random().toString(36).substring(7));

  useEffect(() => {
    if (isOpen && !ws.current) {
      ws.current = new WebSocket(`ws://localhost:8000/ws/chat/${clientId.current}`);
      
      ws.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.message) {
          setMessages(prev => [...prev, { role: 'assistant', content: data.message }]);
          setIsTyping(false);
        }
        if (data.error) {
          setMessages(prev => [...prev, { role: 'assistant', content: `⚠️ ${data.error}` }]);
          setIsTyping(false);
        }
      };

      ws.current.onerror = () => {
        setIsTyping(false);
        setMessages(prev => [...prev, { 
          role: 'assistant', 
          content: '⚠️ Connexion perdue avec le serveur. Vérifiez que le backend est actif.' 
        }]);
      };
      
      ws.current.onclose = () => {
        ws.current = null;
      };
    }
    
    return () => {
      if (ws.current) {
        ws.current.close();
        ws.current = null;
      }
    };
  }, [isOpen]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  const handleSend = (e) => {
    e.preventDefault();
    if (!input.trim() || !ws.current || ws.current.readyState !== WebSocket.OPEN) return;
    
    setMessages(prev => [...prev, { role: 'user', content: input }]);
    ws.current.send(input);
    setInput('');
    setIsTyping(true);
  };

  const quickActions = [
    "Résume les dernières alertes",
    "Quelles menaces sont critiques ?",
    "Explique le Kerberoasting",
    "Comment défendre contre le brute force ?"
  ];

  const handleQuickAction = (text) => {
    if (!ws.current || ws.current.readyState !== WebSocket.OPEN) return;
    setMessages(prev => [...prev, { role: 'user', content: text }]);
    ws.current.send(text);
    setIsTyping(true);
  };

  // Simple markdown-like rendering
  const renderContent = (text) => {
    return text.split('\n').map((line, i) => {
      // Bold
      line = line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
      // Bullet points
      if (line.startsWith('• ') || line.startsWith('- ')) {
        return <p key={i} className="ml-3 text-sm leading-relaxed" dangerouslySetInnerHTML={{ __html: line }} />;
      }
      // Code blocks
      if (line.startsWith('`') && line.endsWith('`')) {
        return <code key={i} className="block bg-slate-950 text-green-400 px-2 py-1 rounded text-xs my-1 font-mono">{line.slice(1, -1)}</code>;
      }
      return <p key={i} className="text-sm leading-relaxed" dangerouslySetInnerHTML={{ __html: line }} />;
    });
  };

  return (
    <>
      {/* Floating Button */}
      <motion.button
        onClick={() => setIsOpen(true)}
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.95 }}
        className="fixed bottom-6 right-6 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white p-4 rounded-2xl shadow-2xl shadow-blue-500/25 z-50 flex items-center justify-center gap-2 transition-all"
      >
        <Sparkles size={20} />
        <span className="text-sm font-semibold hidden sm:inline">SOC Copilot</span>
      </motion.button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 60, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 60, scale: 0.95 }}
            transition={{ type: "spring", damping: 25, stiffness: 300 }}
            className="fixed bottom-6 right-6 w-[480px] h-[640px] bg-slate-900/95 backdrop-blur-xl border border-slate-700/60 rounded-2xl shadow-2xl shadow-black/40 flex flex-col z-50 overflow-hidden"
          >
            {/* Header */}
            <div className="bg-gradient-to-r from-slate-800 to-slate-800/80 p-4 border-b border-slate-700/50 flex justify-between items-center">
              <div className="flex items-center gap-3">
                <div className="bg-gradient-to-br from-blue-500 to-indigo-600 p-2.5 rounded-xl text-white shadow-lg shadow-blue-500/20">
                  <Bot size={20} />
                </div>
                <div>
                  <h3 className="text-slate-100 font-bold text-base">SOC Copilot</h3>
                  <p className="text-slate-400 text-xs flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span> 
                    Assistant IA • Cybersécurité SOC
                  </p>
                </div>
              </div>
              <button 
                onClick={() => setIsOpen(false)}
                className="text-slate-400 hover:text-slate-200 hover:bg-slate-700/50 p-1.5 rounded-lg transition-all"
              >
                <X size={18} />
              </button>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin">
              {messages.map((msg, idx) => (
                <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`flex gap-2.5 max-w-[88%] ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                    <div className={`w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5 ${
                      msg.role === 'user' 
                        ? 'bg-slate-700 text-slate-300' 
                        : 'bg-gradient-to-br from-blue-500 to-indigo-600 text-white'
                    }`}>
                      {msg.role === 'user' ? <User size={14} /> : <Bot size={14} />}
                    </div>
                    <div className={`px-3.5 py-2.5 rounded-2xl ${
                      msg.role === 'user' 
                        ? 'bg-blue-600 text-white rounded-tr-sm' 
                        : 'bg-slate-800/80 text-slate-200 border border-slate-700/50 rounded-tl-sm'
                    }`}>
                      <div className="space-y-0.5">{renderContent(msg.content)}</div>
                    </div>
                  </div>
                </div>
              ))}

              {/* Quick actions — only shown after initial message */}
              {messages.length === 1 && !isTyping && (
                <div className="space-y-2 pt-2">
                  <p className="text-xs text-slate-500 font-medium px-1">Actions rapides :</p>
                  <div className="flex flex-wrap gap-2">
                    {quickActions.map((action, i) => (
                      <button
                        key={i}
                        onClick={() => handleQuickAction(action)}
                        className="text-xs bg-slate-800 hover:bg-slate-700 text-blue-400 hover:text-blue-300 border border-slate-700/50 px-3 py-1.5 rounded-xl transition-all"
                      >
                        {action}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {isTyping && (
                <div className="flex justify-start">
                  <div className="flex gap-2.5">
                    <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white mt-0.5">
                      <Bot size={14} />
                    </div>
                    <div className="bg-slate-800/80 text-slate-400 px-4 py-3 rounded-2xl rounded-tl-sm border border-slate-700/50">
                      <div className="flex items-center gap-1.5">
                        <div className="w-2 h-2 rounded-full bg-blue-400 animate-bounce" style={{ animationDelay: '0ms' }}></div>
                        <div className="w-2 h-2 rounded-full bg-blue-400 animate-bounce" style={{ animationDelay: '150ms' }}></div>
                        <div className="w-2 h-2 rounded-full bg-blue-400 animate-bounce" style={{ animationDelay: '300ms' }}></div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="p-3 bg-slate-800/50 border-t border-slate-700/50">
              <form onSubmit={handleSend} className="flex gap-2">
                <input
                  ref={inputRef}
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Posez une question sur les alertes..."
                  className="flex-1 bg-slate-900 border border-slate-700/60 text-slate-200 px-4 py-2.5 rounded-xl focus:outline-none focus:border-blue-500/60 focus:ring-1 focus:ring-blue-500/20 transition-all text-sm placeholder:text-slate-500"
                />
                <button 
                  type="submit"
                  disabled={!input.trim() || isTyping}
                  className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed text-white p-2.5 w-10 h-10 flex items-center justify-center rounded-xl transition-all shadow-lg shadow-blue-500/20"
                >
                  <Send size={16} />
                </button>
              </form>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
