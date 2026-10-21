import React, { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import { trackPageView } from './utils/analytics'
import SignIn from './pages/SignIn'
import SignUp from './pages/SignUp'
import Dashboard from './pages/Dashboard'
import Verify from './pages/Verify'
import Services from './pages/Services'
import FAQ from './pages/FAQ'
import AdminDashboard from './pages/admin/AdminDashboard'
import AdminUsers from './pages/admin/AdminUsers'
import AdminServices from './pages/admin/AdminServices'
import AdminTransactions from './pages/admin/AdminTransactions'
import AdminFAQs from './pages/admin/AdminFAQs'
import AdminLayout from './pages/admin/AdminLayout'

function PrivateRoute({ children }) {
  const { user } = useAuth()
  return user ? children : <Navigate to="/signin" />
}

function PublicRoute({ children }) {
  const { user } = useAuth()
  return !user ? children : <Navigate to="/dashboard" />
}

function AdminRoute({ children }) {
  const { user } = useAuth()
  if (!user) return <Navigate to="/signin" />
  if (!user.is_admin) return <Navigate to="/dashboard" />
  return children
}

// Component to track page views
function Analytics() {
  const location = useLocation()
  
  useEffect(() => {
    trackPageView(location.pathname + location.search)
  }, [location])
  
  return null
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Analytics />
        <Routes>
          <Route path="/signin" element={<PublicRoute><SignIn /></PublicRoute>} />
          <Route path="/signup" element={<PublicRoute><SignUp /></PublicRoute>} />
          <Route path="/verify" element={<Verify />} />
          <Route path="/services" element={<Services />} />
          <Route path="/faq" element={<FAQ />} />
          <Route path="/dashboard" element={<PrivateRoute><Dashboard /></PrivateRoute>} />

          {/* Admin routes */}
          <Route path="/admin" element={<AdminRoute><AdminLayout /></AdminRoute>}>
            <Route index element={<Navigate to="/admin/dashboard" />} />
            <Route path="dashboard"    element={<AdminDashboard />} />
            <Route path="users"        element={<AdminUsers />} />
            <Route path="services"     element={<AdminServices />} />
            <Route path="transactions" element={<AdminTransactions />} />
            <Route path="faqs"         element={<AdminFAQs />} />
          </Route>

          <Route path="/" element={<Navigate to="/dashboard" />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}

export default App
