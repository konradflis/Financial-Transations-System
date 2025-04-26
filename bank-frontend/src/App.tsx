import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { createTheme, ThemeProvider } from '@mui/material/styles';
import Login from "./Login";
import ProtectedRoute from "./ProtectedRoute";
import AdminDashboard from "./AdminDashboard";
import UserDashboard from "./UserDashboard";
import BankEmployeeDashboard from "./BankEmployeeDashboard";
import AMLDashboard from "./AMLDashboard";

const theme = createTheme({
  palette: {
    primary: {
      main: '#0F4C81',
    },
    secondary: {
      main: '#dee7ea',
    },
  },
});

const App = () => {
  return (
  <ThemeProvider theme={theme}>
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
        <Route
          path="/bank_employee/dashboard"
          element={
            <ProtectedRoute requiredRole="bank_emp">
              <BankEmployeeDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/aml/dashboard"
          element={
            <ProtectedRoute requiredRole="aml">
              <AMLDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/user/dashboard"
          element={
            <ProtectedRoute requiredRole="user">
              <UserDashboard />
            </ProtectedRoute>
          }
        />
      </Routes>
    </Router>
  </ThemeProvider>
  );
};

export default App;