import React from 'react';

interface RepositoryAnalysisFormProps {
  repoUrl: string;
  isAnalyzing: boolean;
  selectedAI: string;
  onRepoUrlChange: (url: string) => void;
  onSubmit: (e: React.FormEvent) => void;
}

export const RepositoryAnalysisForm: React.FC<RepositoryAnalysisFormProps> = ({
  repoUrl,
  isAnalyzing,
  selectedAI,
  onRepoUrlChange,
  onSubmit,
}) => {
  return (
    <form
      onSubmit={onSubmit}
      className="input-form"
      role="form"
      aria-label="저장소 분석 요청"
    >
      <div className="url-input-group terminal-style">
        {/* Terminal prompt icon */}
        <span className="terminal-prompt" aria-hidden="true">›_</span>
        <label htmlFor="repo-url-input" className="sr-only">
          GitHub 저장소 URL
        </label>
        <input
          id="repo-url-input"
          type="url"
          value={repoUrl}
          onChange={(e) => onRepoUrlChange(e.target.value)}
          placeholder="github.com/owner/repo"
          className="form-input form-input-lg terminal-input"
          required
          disabled={isAnalyzing}
          aria-describedby="url-help"
        />
        <div id="url-help" className="sr-only">
          분석하고 싶은 GitHub 저장소의 전체 URL을 입력해주세요.
        </div>
        <button
          type="submit"
          className="btn btn-primary btn-analyze"
          disabled={isAnalyzing || !repoUrl.trim() || !selectedAI}
          aria-label={isAnalyzing ? '저장소 분석 중...' : '저장소 분석 시작'}
        >
          {isAnalyzing ? (
            <>
              <span className="spinner"></span>
              분석 중...
            </>
          ) : (
            'Analyze'
          )}
        </button>
      </div>
    </form>
  );
};
