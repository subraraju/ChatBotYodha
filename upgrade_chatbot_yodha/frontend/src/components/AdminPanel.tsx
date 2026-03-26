/* ── Admin panel — config view + doc upload ─────────────────────── */

import { useState, useEffect } from 'react';
import { api } from '../api';
import type { ConfigResponse } from '../types';

export default function AdminPanel() {
  const [config, setConfig] = useState<ConfigResponse | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadMsg, setUploadMsg] = useState('');

  useEffect(() => {
    api.getConfig().then(setConfig).catch(console.error);
  }, []);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files?.length) return;

    const form = new FormData();
    for (const f of files) form.append('files', f);

    setUploading(true);
    setUploadMsg('');
    try {
      const res = await fetch('/admin/upload-docs', { method: 'POST', body: form });
      const data = await res.json();
      setUploadMsg(data.message || 'Done');
    } catch (err) {
      setUploadMsg('Upload failed');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="admin-panel">
      <h2>Admin Panel</h2>

      {config && (
        <section className="config-section">
          <h3>Configuration</h3>
          <table>
            <tbody>
              <tr><td>Company</td><td>{config.company_name}</td></tr>
              <tr><td>LLM Provider</td><td>{config.llm_provider}</td></tr>
              <tr><td>Embedding Model</td><td>{config.embedding_model}</td></tr>
              <tr><td>Storage Backend</td><td>{config.storage_backend}</td></tr>
            </tbody>
          </table>
        </section>
      )}

      <section className="upload-section">
        <h3>Upload Product Documentation</h3>
        <p>Upload PDF or TXT files to rebuild the product knowledge base.</p>
        <input
          type="file"
          multiple
          accept=".pdf,.txt,.md"
          onChange={handleUpload}
          disabled={uploading}
        />
        {uploading && <p className="status">Uploading &amp; indexing…</p>}
        {uploadMsg && <p className="status">{uploadMsg}</p>}
      </section>
    </div>
  );
}
