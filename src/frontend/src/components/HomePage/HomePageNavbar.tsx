import React, { useState } from 'react';
import { Key, Video, ChevronDown, Check } from 'lucide-react';

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
                    <span className="home-v2-brand">
                        TechGiterview
                    </span>
                </div>

                {/* Right Controls */}
                <div className="navbar-controls">
                    <span
                        className={`navbar-connection-dot ${isConnected ? 'navbar-connection-dot--ok' : 'navbar-connection-dot--error'}`}
                        title={isConnected ? '백엔드 연결 정상' : '백엔드 연결 확인 필요'}
                        aria-label={isConnected ? '백엔드 연결 정상' : '백엔드 연결 확인 필요'}
                    />
                    {/* 1. Model Selector Dropdown - FIX #4: Enhanced UI */}
                    <div className="navbar-model-selector">
                        <button
                            onClick={() => setIsModelDropdownOpen(!isModelDropdownOpen)}
                            className="navbar-dropdown-trigger"
                            type="button"
                        >
                            <Video className="v2-icon-sm navbar-trigger-icon" />
                            <span>{selectedProvider?.name || 'AI 모델'}</span>
                            <ChevronDown className={`v2-icon-xs navbar-trigger-chevron ${isModelDropdownOpen ? 'navbar-trigger-chevron--open' : ''}`} />
                        </button>

                        {isModelDropdownOpen && (
                            <>
                                <div
                                    className="navbar-dropdown-backdrop"
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
                                                <Check className="v2-icon-sm navbar-dropdown-check" />
                                            )}
                                        </button>
                                    ))}
                                </div>
                            </>
                        )}
                    </div>

                    <div className="navbar-divider"></div>

                    {/* 2. API Key Settings */}
                    <button
                        onClick={onShowApiKeySetup}
                        className={`navbar-settings-btn ${needsApiKeySetup
                            ? 'navbar-settings-btn--warning'
                            : 'navbar-settings-btn--normal'
                            }`}
                        type="button"
                    >
                        <Key className={`v2-icon-sm navbar-settings-key-icon ${needsApiKeySetup ? 'navbar-settings-icon--warning' : 'navbar-settings-icon--normal'}`} />
                        <span className="navbar-settings-label">
                            {needsApiKeySetup ? 'API 설정 필요' : '설정'}
                        </span>
                    </button>
                </div>
            </div>
        </nav>
    );
};
