import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Login from "./Login";
import ProtectedRoute from "./ProtectedRoute";
import AdminDashboard from "./AdminDashboard";
import UserDashboard from "./UserDashboard";

const App = () => {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route
          path="/admin/dashboard"
          element={
            <ProtectedRoute requiredRole="admin">
              <AdminDashboard />
            </ProtectedRoute>
          }
        />
          <Route path="/user/dashboard" element={<UserDashboard />} />
      </Routes>
    </Router>
  );
};

export default App;