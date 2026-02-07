import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Home from './pages/Home'
import ProductAnalysis from './pages/ProductAnalysis'
import CompareProducts from './pages/CompareProducts'

function App() {
    return (
        <Routes>
            <Route path="/" element={<Layout />}>
                <Route index element={<Home />} />
                <Route path="products/:productId" element={<ProductAnalysis />} />
                <Route path="compare" element={<CompareProducts />} />
            </Route>
        </Routes>
    )
}

export default App
