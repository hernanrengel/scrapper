import { Route, Routes } from 'react-router-dom'
import { PageListView } from './pages/PageListView'

function App() {
  return (
    <Routes>
      <Route path="/" element={<PageListView />} />
    </Routes>
  )
}

export default App
