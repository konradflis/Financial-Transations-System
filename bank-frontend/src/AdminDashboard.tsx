import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Box, Typography, Button, Paper } from "@mui/material";

interface DashboardData {
  message: string;
}

const AdminDashboard = () => {
  const [data, setData] = useState<DashboardData | null>(null); // Typ danych z backendu
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem("token");
    navigate("/");
  };

  const fetchDashboard = async () => {
    const token = localStorage.getItem("token");

    if (!token) {
      alert("Brak tokenu, nie jesteś zalogowany!");
      navigate("/");
      return;
    }

    try {
      const response = await fetch("http://localhost:8000/admin/dashboard", {
        method: "GET",
        headers: {
          "Authorization": `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data: DashboardData = await response.json();
        setData(data);
        setLoading(false);
      } else {
        const error = await response.json();
        setError(error.detail);
        setLoading(false);
      }
    } catch (error) {
      console.error("Błąd połączenia:", error);
      setError("Wystąpił błąd podczas pobierania danych");
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, []);

  if (loading) {
    return <div>Ładowanie...</div>;
  }

  if (error) {
    return <div>{error}</div>;
  }

  return (
    <Box
      display="flex"
      justifyContent="center"
      alignItems="center"
      sx={{ height: "100vh", bgcolor: "background.default" }}
    >
      <Paper elevation={4} sx={{ p: 4, width: "90%", maxWidth: 500 }}>
        <Typography variant="h4" gutterBottom>
          Dashboard
        </Typography>
        <Typography variant="body1" sx={{ mb: 3 }}>
          {data?.message ?? "Witaj w panelu administracyjnym!"}
        </Typography>
        <Button
          variant="contained"
          color="secondary"
          onClick={handleLogout}
          fullWidth
        >
          Wyloguj się
        </Button>
      </Paper>
    </Box>
  );
};

export default AdminDashboard;
