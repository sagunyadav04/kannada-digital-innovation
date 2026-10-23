'use client';
import { useEffect, useState } from 'react';
import { LANGUAGES, downscaleToBase64 } from '../lib/helpers';
import ResultView from './components/ResultView';

function ThemeToggle() {
  const [theme, setTheme] = useState('light');

  // Pick up whatever the inline script in layout.js already applied.
  useEffect(() => {
    setTheme(document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light');
  }, []);

  function toggle() {
    const next = theme === 'dark' ? 'light' : 'dark';
    setTheme(next);
    document.documentElement.setAttribute('data-theme', next);
    try {
      localStorage.setItem('theme', next);
    } catch {
      // Storage can be blocked (private mode); the toggle still works for this visit.
    }
  }

  return (
    <button
      className="theme-toggle"
      onClick={toggle}
      aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
    >
      {theme === 'dark' ? '☀️ Light' : '🌙 Dark'}
    </button>
  );
}

export default function Home() {
  const [language, setLanguage] = useState('English');
  const [preview, setPreview] = useState(null);
  const [image, setImage] = useState(null);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState('');

  async function onFile(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    setErr('');
    setData(null);
    try {
      const dataUrl = await downscaleToBase64(file);
      setPreview(dataUrl);
      setImage(dataUrl.split(',')[1]);
    } catch (ex) {
      setErr(ex.message);
    }
  }

  async function explain() {
    if (!image) return;
    setLoading(true);
    setErr('');
    setData(null);
    try {
      const res = await fetch('/api/explain', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image, language }),
      });
      const json = await res.json();
      if (!res.ok) throw new Error(json.error || 'Request failed');
      setData(json);
    } catch (ex) {
      setErr(ex.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="wrap">
      <header>
        <div>
          <h1><span>ಅರ್ಥ</span> Artha</h1>
          <p className="sub">
            Photograph any Kannada document. Get searchable text, a plain-language explanation and your next steps.
          </p>
        </div>
        <ThemeToggle />
      </header>

      <div className="drop">
        <p style={{ margin: '0 0 10px' }}>
          Bills, land records, notices, forms, agreements, prescriptions or handwritten notes.
        </p>
        <input type="file" accept="image/*" capture="environment" onChange={onFile} aria-label="Upload a document photo" />
        {preview && <div><img className="preview" src={preview} alt="Document to explain" /></div>}
      </div>

      <div className="controls">
        <label className="field">
          Explain in
          <select value={language} onChange={(e) => setLanguage(e.target.value)}>
            {LANGUAGES.map((l) => <option key={l.name}>{l.name}</option>)}
          </select>
        </label>
        <button className="btn primary" onClick={explain} disabled={!image || loading} style={{ alignSelf: 'flex-end' }}>
          {loading ? 'Reading document…' : 'Explain this document'}
        </button>
      </div>

      <p className="small">Photos are sent for processing only and are not stored by this app.</p>

      {err && <div className="err">{err}</div>}
      {data && <ResultView data={data} />}

      <footer>Kannada Technology Challenge · Problem #05 Kannada Text Digitization</footer>
    </div>
  );
}
