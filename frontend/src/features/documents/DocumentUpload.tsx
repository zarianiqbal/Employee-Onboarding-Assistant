import { useCallback, useEffect, useRef, useState } from 'react';

import { ApiError, api } from '../../api/client';
import type { DocumentRecord } from '../../api/types';
import './DocumentUpload.css';

interface DocumentUploadProps {
  employeeId: number;
}

const DOC_TYPES = ['ID', 'TaxForm', 'Offer', 'Certificate', 'Other'];
const MAX_BYTES = 20 * 1024 * 1024; // 20 MB

type UploadState = 'idle' | 'uploading' | 'success' | 'error';

/**
 * Drag-and-drop secure upload using the valet-key (SAS) pattern:
 * request a short-lived token, PUT the file straight to Blob Storage, then
 * commit the reference. File bytes never pass through the API server.
 */
export function DocumentUpload({ employeeId }: DocumentUploadProps) {
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [docType, setDocType] = useState('ID');
  const [state, setState] = useState<UploadState>('idle');
  const [message, setMessage] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const refresh = useCallback(async () => {
    try {
      setDocuments(await api.listDocuments(employeeId));
    } catch {
      /* non-fatal for the list */
    }
  }, [employeeId]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const upload = useCallback(
    async (file: File) => {
      if (file.size > MAX_BYTES) {
        setState('error');
        setMessage('File is larger than the 20 MB limit.');
        return;
      }
      setState('uploading');
      setMessage(`Uploading ${file.name}…`);
      try {
        const contentType = file.type || 'application/octet-stream';
        const sas = await api.requestSasToken(employeeId, file.name, contentType, docType);

        // In local/stub mode the upload URL is not a real blob endpoint, so we
        // skip the direct PUT and go straight to committing the reference.
        const isStub = sas.upload_url.includes('stub-sas');
        if (!isStub) {
          const put = await fetch(sas.upload_url, {
            method: 'PUT',
            headers: sas.required_headers,
            body: file,
          });
          if (!put.ok) throw new ApiError(put.status, 'Direct upload to storage failed');
        }

        await api.commitDocument(employeeId, {
          blob_name: sas.blob_name,
          original_file_name: file.name,
          document_type: docType,
          content_type: contentType,
          size_bytes: file.size,
        });

        setState('success');
        setMessage(`${file.name} uploaded.`);
        await refresh();
      } catch (err) {
        setState('error');
        setMessage(err instanceof ApiError ? err.message : 'Upload failed. Please try again.');
      }
    },
    [employeeId, docType, refresh],
  );

  const onDrop = (event: React.DragEvent) => {
    event.preventDefault();
    setDragging(false);
    const file = event.dataTransfer.files?.[0];
    if (file) void upload(file);
  };

  return (
    <section className="card" aria-labelledby="upload-title">
      <h2 id="upload-title">Upload documents</h2>
      <p style={{ color: 'var(--color-text-muted)', marginTop: 0 }}>
        Files upload securely and directly to encrypted storage. Accepted: PDF, JPG, PNG up to
        20&nbsp;MB.
      </p>

      <div className="field">
        <label htmlFor="doc-type">Document type</label>
        <select id="doc-type" value={docType} onChange={(e) => setDocType(e.target.value)}>
          {DOC_TYPES.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
      </div>

      <div
        className={`dropzone ${dragging ? 'is-dragging' : ''}`}
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => inputRef.current?.click()}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            inputRef.current?.click();
          }
        }}
        role="button"
        tabIndex={0}
        aria-label="Upload a document: drag a file here or press Enter to browse"
      >
        <span className="dropzone__icon" aria-hidden="true">
          📄
        </span>
        <p className="dropzone__text">
          <strong>Drag &amp; drop</strong> a file here, or click to browse
        </p>
        <input
          ref={inputRef}
          type="file"
          className="sr-only"
          accept=".pdf,.jpg,.jpeg,.png"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) void upload(file);
            e.target.value = '';
          }}
        />
      </div>

      {message && (
        <div
          className={`toast ${state === 'error' ? 'toast-error' : 'toast-success'}`}
          role={state === 'error' ? 'alert' : 'status'}
        >
          {message}
        </div>
      )}

      {documents.length > 0 && (
        <ul className="doc-list">
          {documents.map((doc) => (
            <li key={doc.document_id} className="doc-list__item">
              <span className="doc-list__name">{doc.original_file_name}</span>
              <span className="badge badge-muted">{doc.document_type}</span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
