import { useState, useRef, useCallback } from 'react'
import './App.css'

const ACCEPTED_TYPES = {
  'text/markdown': 'md',
  'text/plain': 'txt',
  'text/html': 'html',
  'application/pdf': 'pdf',
}

const ACCEPTED_EXTENSIONS = ['.md', '.txt', '.html', '.htm', '.pdf']

const FILE_ICONS = {
  md: '📝',
  txt: '📄',
  html: '🌐',
  htm: '🌐',
  pdf: '📕',
}

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function getExt(filename) {
  return filename.split('.').pop().toLowerCase()
}

function isAccepted(file) {
  const ext = `.${getExt(file.name)}`
  return ACCEPTED_EXTENSIONS.includes(ext) || file.type in ACCEPTED_TYPES
}

function FileRow({ file, onRemove }) {
  const ext = getExt(file.name)
  const icon = FILE_ICONS[ext] ?? '📄'

  return (
    <div className="file-row">
      <span className="file-icon">{icon}</span>
      <div className="file-info">
        <span className="file-name">{file.name}</span>
        <span className="file-meta">{formatBytes(file.size)} · .{ext}</span>
      </div>
      <button className="remove-btn" onClick={() => onRemove(file.name)} aria-label="Remove file">
        ✕
      </button>
    </div>
  )
}

export default function App() {
  const [files, setFiles] = useState([])
  const [dragging, setDragging] = useState(false)
  const [errors, setErrors] = useState([])
  const [uploading, setUploading] = useState(false)
  const [results, setResults] = useState(null)
  const inputRef = useRef(null)

  const addFiles = useCallback((incoming) => {
    const newErrors = []
    const toAdd = []

    for (const f of incoming) {
      if (!isAccepted(f)) {
        newErrors.push(`"${f.name}" is not a supported file type`)
        continue
      }
      if (files.some((existing) => existing.name === f.name)) {
        newErrors.push(`"${f.name}" is already added`)
        continue
      }
      toAdd.push(f)
    }

    setErrors(newErrors)
    if (toAdd.length) setFiles((prev) => [...prev, ...toAdd])
  }, [files])

  const removeFile = useCallback((name) => {
    setFiles((prev) => prev.filter((f) => f.name !== name))
  }, [])

  const onDragOver = (e) => {
    e.preventDefault()
    setDragging(true)
  }

  const onDragLeave = (e) => {
    if (!e.currentTarget.contains(e.relatedTarget)) setDragging(false)
  }

  const onDrop = (e) => {
    e.preventDefault()
    setDragging(false)
    addFiles(Array.from(e.dataTransfer.files))
  }

  const onInputChange = (e) => {
    addFiles(Array.from(e.target.files))
    e.target.value = ''
  }

  const handleUpload = async () => {
    setUploading(true)
    setErrors([])
    setResults(null)
    try {
      const form = new FormData()
      for (const f of files) form.append('files', f)
      const res = await fetch('http://localhost:8000/documents', { method: 'POST', body: form })
      if (!res.ok) {
        const err = await res.json()
        setErrors([err.detail ?? 'Upload failed'])
        return
      }
      const data = await res.json()
      setResults(data.documents)
      setFiles([])
    } catch {
      setErrors(['Could not reach the backend. Is it running on port 8000?'])
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="layout">
      <header className="header">
        <h1>Doc Upload</h1>
        <p className="subtitle">Add your internal docs to get started with the knowledge base</p>
      </header>

      <main className="main">
        <div
          className={`drop-zone ${dragging ? 'dragging' : ''}`}
          onDragOver={onDragOver}
          onDragLeave={onDragLeave}
          onDrop={onDrop}
          onClick={() => inputRef.current?.click()}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => e.key === 'Enter' && inputRef.current?.click()}
          aria-label="Upload documents"
        >
          <input
            ref={inputRef}
            type="file"
            multiple
            accept=".md,.txt,.html,.htm,.pdf"
            onChange={onInputChange}
            style={{ display: 'none' }}
          />
          <div className="drop-icon">⬆</div>
          <p className="drop-primary">Drop files here or <span className="link">browse</span></p>
          <p className="drop-secondary">Supports .md, .txt, .html, .pdf</p>
        </div>

        {errors.length > 0 && (
          <div className="error-list">
            {errors.map((err) => (
              <p key={err} className="error-item">⚠ {err}</p>
            ))}
          </div>
        )}

        {files.length > 0 && (
          <section className="file-list-section">
            <div className="file-list-header">
              <h2>Documents <span className="count">{files.length}</span></h2>
              <button className="clear-btn" onClick={() => setFiles([])}>Clear all</button>
            </div>
            <div className="file-list">
              {files.map((f) => (
                <FileRow key={f.name} file={f} onRemove={removeFile} />
              ))}
            </div>
            <button className="upload-btn" onClick={handleUpload} disabled={uploading}>
              {uploading ? 'Processing...' : `Upload ${files.length} ${files.length === 1 ? 'document' : 'documents'}`}
            </button>
          </section>
        )}

        {results && (
          <section className="results-section">
            <h2 className="results-heading">Normalized <span className="count">{results.length}</span></h2>
            {results.map((doc) => (
              <div key={doc.filename} className="result-card">
                <div className="result-meta">
                  <span className="result-name">{doc.filename}</span>
                  <span className="result-stats">{doc.word_count.toLocaleString()} words · {doc.char_count.toLocaleString()} chars</span>
                </div>
                <pre className="result-preview">{doc.text.slice(0, 400)}{doc.text.length > 400 ? '\n…' : ''}</pre>
              </div>
            ))}
          </section>
        )}
      </main>
    </div>
  )
}
