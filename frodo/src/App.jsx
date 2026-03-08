
import { useState } from 'react';
import './App.css';

function App() {
  const [email, setEmail] = useState('');
  const [scanning, setScanning] = useState(false);
  const [scanResult, setScanResult] = useState(null);

  const handleScan = () => {
    setScanning(true);
    setTimeout(() => {
      setScanResult({
        brokers: 53,
        message: 'Your home address is listed for sale on 53 data broker sites.'
      });
      setScanning(false);
    }, 2000);
  };

  return (
    <div className="frodo-landing" style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', background: '#181a20', color: '#fff' }}>
      <h1 style={{ fontSize: '2.5rem', marginBottom: '1rem' }}>Ghost: Strategic Invisibility</h1>
      <p style={{ maxWidth: 400, textAlign: 'center', marginBottom: '2rem' }}>
        Enter your email to scan the web for your exposed personal data. Frodo will show you where your digital footprint is at risk.
      </p>
      <input
        type="email"
        placeholder="Enter your email"
        value={email}
        onChange={e => setEmail(e.target.value)}
        style={{ padding: '0.75rem', borderRadius: 8, border: 'none', width: 280, marginBottom: 16, fontSize: '1rem' }}
        disabled={scanning}
      />
      <button
        onClick={handleScan}
        disabled={!email || scanning}
        style={{ padding: '0.75rem 2rem', borderRadius: 8, background: '#4f8cff', color: '#fff', border: 'none', fontWeight: 600, fontSize: '1rem', cursor: scanning ? 'not-allowed' : 'pointer', marginBottom: 24 }}
      >
        {scanning ? 'Scanning...' : 'Scan for Exposure'}
      </button>
      {scanResult && (
        <div style={{ background: '#23262f', padding: 24, borderRadius: 12, marginTop: 16, textAlign: 'center', maxWidth: 400 }}>
          <h2 style={{ color: '#ffb347', marginBottom: 8 }}>Exposure Detected</h2>
          <p style={{ fontSize: '1.1rem', marginBottom: 0 }}>{scanResult.message}</p>
        </div>
      )}
    </div>
  );
}

export default App;
