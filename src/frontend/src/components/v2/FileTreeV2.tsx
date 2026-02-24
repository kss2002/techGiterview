import React from 'react'
import {
  ChevronRight, Folder, FileText, FileCode, Cpu, Globe, Palette,
  Settings, Archive, Shield, BookOpen, File, Database, Github, Monitor
} from 'lucide-react'
import type { FileTreeNode } from '../../types/dashboard'
import './FileTreeV2.css'

interface FileTreeV2Props {
  nodes: FileTreeNode[]
  expandedFolders: Set<string>
  onToggleFolder: (path: string) => void
  onFileClick: (node: FileTreeNode) => void
  searchTerm: string
  onSearch: (term: string) => void
  isLoading?: boolean
}

function getFileIcon(filePath: string): React.ReactNode {
  const ext = filePath.split('.').pop()?.toLowerCase() || ''
  const name = filePath.split('/').pop()?.toLowerCase() || ''
  if (name === 'dockerfile' || name.startsWith('dockerfile')) return <Monitor className="v2-icon-sm v2-file-icon" />
  if (name === '.gitignore') return <Github className="v2-icon-sm v2-file-icon" />
  if (name.startsWith('readme')) return <BookOpen className="v2-icon-sm v2-file-icon" />
  if (name === 'license' || name.startsWith('license')) return <Shield className="v2-icon-sm v2-file-icon" />
  if (name === 'package.json' || name === 'pyproject.toml') return <Settings className="v2-icon-sm v2-file-icon v2-file-icon--config" />
  if (name === 'package-lock.json' || name === 'yarn.lock') return <Archive className="v2-icon-sm v2-file-icon" />
  switch (ext) {
    case 'ts': case 'tsx': return <FileCode className="v2-icon-sm v2-file-icon v2-file-icon--ts" />
    case 'js': case 'jsx': return <FileCode className="v2-icon-sm v2-file-icon v2-file-icon--js" />
    case 'py': case 'pyx': return <Cpu className="v2-icon-sm v2-file-icon v2-file-icon--py" />
    case 'html': case 'htm': return <Globe className="v2-icon-sm v2-file-icon v2-file-icon--html" />
    case 'css': case 'scss': case 'sass': return <Palette className="v2-icon-sm v2-file-icon v2-file-icon--css" />
    case 'json': case 'yaml': case 'yml': case 'toml': return <Settings className="v2-icon-sm v2-file-icon v2-file-icon--config" />
    case 'md': return <FileText className="v2-icon-sm v2-file-icon" />
    case 'sql': case 'db': return <Database className="v2-icon-sm v2-file-icon" />
    default: return <File className="v2-icon-sm v2-file-icon" />
  }
}

function FileTreeNodeItem({
  node, expandedFolders, onToggleFolder, onFileClick, searchTerm, depth = 0
}: {
  node: FileTreeNode
  expandedFolders: Set<string>
  onToggleFolder: (path: string) => void
  onFileClick: (node: FileTreeNode) => void
  searchTerm: string
  depth?: number
}) {
  const isExpanded = expandedFolders.has(node.path)
  const isMatchSearch = searchTerm && node.name.toLowerCase().includes(searchTerm.toLowerCase())

  return (
    <>
      <div className="v2-tree-node" style={{ paddingLeft: `${8 + depth * 14}px` }}>
        {node.type === 'dir' ? (
          <button
            className="v2-tree-folder"
            onClick={() => onToggleFolder(node.path)}
            aria-expanded={isExpanded}
          >
            <ChevronRight className={`v2-icon-xs v2-tree-chevron ${isExpanded ? 'v2-tree-chevron--open' : ''}`} />
            <Folder className="v2-icon-sm v2-tree-folder-icon" />
            <span className="v2-tree-label v2-truncate">{node.name}</span>
          </button>
        ) : (
          <button
            className={`v2-tree-file ${isMatchSearch ? 'v2-tree-file--match' : ''}`}
            onClick={() => onFileClick(node)}
          >
            {getFileIcon(node.name)}
            <span className={`v2-tree-label v2-truncate ${isMatchSearch ? 'v2-tree-label--match' : ''}`}>
              {node.name}
            </span>
            {node.size ? (
              <span className="v2-tree-size">{(node.size / 1024).toFixed(1)}k</span>
            ) : null}
          </button>
        )}
      </div>
      {node.type === 'dir' && isExpanded && node.children && (
        <div className="v2-tree-children">
          {node.children.map(child => (
            <FileTreeNodeItem
              key={child.path}
              node={child}
              expandedFolders={expandedFolders}
              onToggleFolder={onToggleFolder}
              onFileClick={onFileClick}
              searchTerm={searchTerm}
              depth={depth + 1}
            />
          ))}
        </div>
      )}
    </>
  )
}

export function FileTreeV2({ nodes, expandedFolders, onToggleFolder, onFileClick, searchTerm, onSearch, isLoading }: FileTreeV2Props) {
  return (
    <div className="v2-file-tree">
      <div className="v2-file-tree-search">
        <input
          type="text"
          className="v2-input v2-file-tree-input"
          placeholder="파일 검색..."
          value={searchTerm}
          onChange={e => onSearch(e.target.value)}
          aria-label="파일 검색"
        />
      </div>
      <div className="v2-file-tree-content">
        {isLoading ? (
          <div className="v2-file-tree-loading">
            <div className="v2-spinner v2-spinner-sm" />
            <span>로딩 중...</span>
          </div>
        ) : nodes.length === 0 ? (
          <p className="v2-file-tree-empty">파일을 불러올 수 없습니다.</p>
        ) : (
          nodes.map(node => (
            <FileTreeNodeItem
              key={node.path}
              node={node}
              expandedFolders={expandedFolders}
              onToggleFolder={onToggleFolder}
              onFileClick={onFileClick}
              searchTerm={searchTerm}
            />
          ))
        )}
      </div>
    </div>
  )
}
