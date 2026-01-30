import React, { useState } from 'react';
import { Key, Video, Settings, ChevronDown, Check } from 'lucide-react';

interface AIProvider {
    id: string;
    name: string;
    model: string;
    status: string;
    recommended?: boolean;
}

interface HomePageNavbarProps {
    // API Key Props
    onShowApiKeySetup: () => void;
    needsApiKeySetup: boolean;
    isConnected: boolean;

    // AI Model Props
    providers: AIProvider[];
    selectedAI: string;
    onSelectedAIChange: (aiId: string) => void;
}

export const HomePageNavbar: React.FC<HomePageNavbarProps> = ({
    onShowApiKeySetup,
    needsApiKeySetup,
    isConnected,
    providers,
    selectedAI,
    onSelectedAIChange,
}) => {
    const [isModelDropdownOpen, setIsModelDropdownOpen] = useState(false);
    const selectedProvider = providers.find(p => p.id === selectedAI);

    return (
        <nav className="navbar-container">
            <div className="navbar-content">
                {/* Logo Area */}
                <div className="navbar-logo">
                    <span style={{ fontWeight: 800, fontSize: '1.25rem', letterSpacing: '-0.02em', color: 'var(--gray-900)' }}>
                        TechGiterview
                    </span>
                </div>

                {/* Right Controls */}
                <div className="navbar-controls flex items-center gap-sm">
                    {/* 1. Model Selector Dropdown - FIX #4: Enhanced UI */}
                    <div className="relative">
                        <button
                            onClick={() => setIsModelDropdownOpen(!isModelDropdownOpen)}
                            className="navbar-dropdown-trigger"
                        >
                            <Video className="w-4 h-4" style={{ color: 'var(--primary-500)' }} />
                            <span>{selectedProvider?.name || 'AI 모델'}</span>
                            <ChevronDown className={`w-3 h-3 transition-transform ${isModelDropdownOpen ? 'rotate-180' : ''}`} style={{ color: 'var(--gray-400)' }} />
                        </button>

                        {isModelDropdownOpen && (
                            <>
                                <div
                                    className="fixed inset-0 z-40"
                                    onClick={() => setIsModelDropdownOpen(false)}
                                />
                                <div className="navbar-dropdown-menu">
                                    <div className="navbar-dropdown-header">
                                        AI 모델 선택
                                    </div>
                                    {providers.map((provider) => (
                                        <button
                                            key={provider.id}
                                            onClick={() => {
                                                onSelectedAIChange(provider.id);
                                                setIsModelDropdownOpen(false);
                                            }}
                                            className={`navbar-dropdown-item ${selectedAI === provider.id ? 'selected' : ''}`}
                                        >
                                            <div className="navbar-dropdown-item-content">
                                                <div className="navbar-dropdown-item-name">
                                                    {provider.name}
                                                    {provider.recommended && (
                                                        <span className="navbar-dropdown-badge">추천</span>
                                                    )}
                                                </div>
                                                <div className="navbar-dropdown-item-model">{provider.model}</div>
                                            </div>
                                            {selectedAI === provider.id && (
                                                <Check className="w-4 h-4" style={{ color: 'var(--primary-600)' }} />
                                            )}
                                        </button>
                                    ))}
                                </div>
                            </>
                        )}
                    </div>

                    <div className="h-4 w-px bg-gray-200 mx-1"></div>

                    {/* 2. API Key Settings */}
                    <button
                        onClick={onShowApiKeySetup}
                        className={`btn-sm flex items-center gap-xs px-3 py-2 rounded-lg transition-all ${needsApiKeySetup
                            ? 'bg-amber-100 text-amber-700 hover:bg-amber-200'
                            : 'text-gray-600 hover:bg-gray-100'
                            }`}
                    >
                        <Key className={`w-4 h-4 ${needsApiKeySetup ? 'text-amber-600' : 'text-gray-400'}`} />
                        <span className="text-sm font-medium">
                            {needsApiKeySetup ? 'API 설정 필요' : '설정'}
                        </span>
                    </button>
                </div>
            </div>
        </nav>
    );
};
