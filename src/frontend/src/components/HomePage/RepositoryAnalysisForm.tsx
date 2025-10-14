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
      <div className="url-input-group">
        <label htmlFor="repo-url-input" className="sr-only">
          GitHub 저장소 URL
        </label>
        <input
          id="repo-url-input"
          type="url"
          value={repoUrl}
          onChange={(e) => onRepoUrlChange(e.target.value)}
          placeholder="GitHub 저장소 URL을 입력하세요 (예: https://github.com/facebook/react)"
          className="form-input form-input-lg focus-ring transition-fast"
          required
          disabled={isAnalyzing}
          aria-describedby="url-help"
        />
        <div id="url-help" className="sr-only">
          분석하고 싶은 GitHub 저장소의 전체 URL을 입력해주세요. 예:
          https://github.com/facebook/react
        </div>
        <button
          type="submit"
          className="btn btn-primary btn-xl hover-lift active-scale focus-ring"
          disabled={isAnalyzing || !repoUrl.trim() || !selectedAI}
          aria-label={isAnalyzing ? '저장소 분석 중...' : '저장소 분석 시작'}
        >
          {isAnalyzing ? (
            <>
              <span className="spinner"></span>
              분석 중...
            </>
          ) : (
            '분석 시작'
          )}
        </button>
      </div>
    </form>
  );
};
