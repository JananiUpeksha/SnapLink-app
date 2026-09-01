import { useState } from 'react'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

function App() {
  const [longUrl, setLongUrl] = useState('')
  const [shortUrl, setShortUrl] = useState(null)
  const [error, setError] = useState(null)

  const [statsCode, setStatsCode] = useState('')
  const [stats, setStats] = useState(null)
  const [statsError, setStatsError] = useState(null)

  const handleShorten = async (e) => {
    e.preventDefault()
    setError(null)
    setShortUrl(null)

    try {
      const res = await fetch(`${API_BASE}/shorten`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ long_url: longUrl }),
      })

      if (res.status === 429) {
        setError('Rate limit hit — try again in a minute.')
        return
      }
      if (!res.ok) {
        setError('Something went wrong. Check the URL and try again.')
        return
      }

      const data = await res.json()
      setShortUrl(`${API_BASE}${data.short_url}`)
    } catch {
      setError('Could not reach the server.')
    }
  }

  const handleStats = async (e) => {
    e.preventDefault()
    setStatsError(null)
    setStats(null)

    try {
      const res = await fetch(`${API_BASE}/stats/${statsCode}`)
      if (!res.ok) {
        setStatsError('Short code not found.')
        return
      }
      const data = await res.json()
      setStats(data)
    } catch {
      setStatsError('Could not reach the server.')
    }
  }

  return (
    <div style={{ maxWidth: 480, margin: '60px auto', fontFamily: 'sans-serif' }}>
      <h1>SnapLink</h1>

      <form onSubmit={handleShorten}>
        <input
          type="url"
          placeholder="https://example.com/very/long/url"
          value={longUrl}
          onChange={(e) => setLongUrl(e.target.value)}
          required
          style={{ width: '100%', padding: 8, boxSizing: 'border-box' }}
        />
        <button type="submit" style={{ marginTop: 8 }}>Shorten</button>
      </form>

      {shortUrl && (
        <p>
          Short link: <a href={shortUrl} target="_blank" rel="noreferrer">{shortUrl}</a>
        </p>
      )}
      {error && <p style={{ color: 'red' }}>{error}</p>}

      <hr style={{ margin: '32px 0' }} />

      <h2>Check Stats</h2>
      <form onSubmit={handleStats}>
        <input
          type="text"
          placeholder="short code (e.g. aYLU9h)"
          value={statsCode}
          onChange={(e) => setStatsCode(e.target.value)}
          required
          style={{ width: '100%', padding: 8, boxSizing: 'border-box' }}
        />
        <button type="submit" style={{ marginTop: 8 }}>Get Stats</button>
      </form>

      {stats && (
        <ul>
          <li>Code: {stats.short_code}</li>
          <li>Long URL: {stats.long_url}</li>
          <li>Clicks: {stats.click_count}</li>
          <li>Created: {new Date(stats.created_at).toLocaleString()}</li>
        </ul>
      )}
      {statsError && <p style={{ color: 'red' }}>{statsError}</p>}
    </div>
  )
}

export default App
