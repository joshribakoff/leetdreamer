import React from 'react'
import ReactDOM from 'react-dom/client'
import { Layout } from './components/Layout'
import { MArray } from './components/MArray'

// Demo for development
const App = () => (
  <Layout title="Two Sum" target={9}>
    <MArray values={[2, 7, 11, 15]} highlight={[0, 1]} />
  </Layout>
)

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
