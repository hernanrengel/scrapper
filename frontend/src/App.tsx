import { Route, Routes } from 'react-router-dom'
import { PageDetailView } from './pages/PageDetailView'
import { PageListView } from './pages/PageListView'

function App() {
  return (
    <Routes>
      <Route path="/" element={<PageListView />} />
      <Route path="/pages/:id" element={<PageDetailView />} />
    </Routes>
  )
}

export default App
