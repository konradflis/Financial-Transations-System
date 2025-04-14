import { Navigate } from "react-router-dom";
import React from "react";

const ProtectedRoute = ({ children, requiredRole }: { children: React.ReactNode, requiredRole: string }) => {
  const token = localStorage.getItem("token");

  if (!token) {
    return <Navigate to="/" />;
  }

  try {
    const decodedToken = JSON.parse(atob(token.split('.')[1]));
    const userRole = decodedToken.role;

    if (userRole !== requiredRole) {
      return <Navigate to="/" />;
    }

    return <>{children}</>;
  } catch (error) {
    return <Navigate to="/" />;
  }
};

export default ProtectedRoute;