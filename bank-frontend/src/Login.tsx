import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { TextField, Button, Box, Typography } from "@mui/material";
import backgroundImage from './assets/pexels-lkloeppel-466685.jpg'
import logo from './assets/JKM_Bank_Logo.png'

function Login() {
  const [loginID, setLoginID] = useState("");
  const [password, setPassword] = useState("");
  const navigate = useNavigate();

  const handleLogin = async () => {
    const formData = new URLSearchParams();
    formData.append("username", loginID);
    formData.append("password", password);

    try {
      const response = await fetch("http://localhost:8000/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded"
        },
        body: formData.toString(),
      });

      if (response.ok) {
        const data = await response.json();
        console.log(data);
        localStorage.setItem("token", data.access_token);
        localStorage.setItem("role", data.role);

        if (data.role === "admin") {
          navigate("/admin/dashboard");
        } else if (data.role === "user") {
          navigate("/user/dashboard");
        }
        else if (data.role === "bank_emp") {
          navigate("/bank_employee/dashboard");
        }
        else if (data.role === "aml") {
          navigate("/aml/dashboard");
        }
      } else {
        const err = await response.json();
        alert(`Błąd logowania: ${err.detail}`);
      }
    } catch (error) {
      console.error("Błąd:", error);
      alert("Wystąpił błąd podczas logowania");
    }
  };

  return (
      <Box
          display="flex"
          justifyContent="center"
          alignItems="center"
          sx={{height: "100vh", bgcolor: "background.paper",
          backgroundImage: `url(${backgroundImage})`,
            backgroundSize: "cover",
            backgroundPosition: "center",
            backgroundRepeat: "no-repeat"}}
      >
        <Box
            width={{xs: "90%", sm: "70%", md: "50%"}}
            p={4}
            boxShadow={3}
            borderRadius={2}
            bgcolor="white"
            sx={{bgcolor: "rgba(255, 255, 255, 0.75)",
            backdropFilter: "blur(3px)",
            border: "1px solid rgba(255, 255, 255, 0.2)"}}
        >

          <Box display="flex" justifyContent="center" mb={2}>
            <img src={logo} alt="Logo" style={{ width: 'auto', height: 'auto', maxWidth: '128px', maxHeight: '128px' }} />
          </Box>
          <Typography variant="h5" gutterBottom textAlign="center" sx={{ fontWeight: 'bold', fontSize: '1.25rem' }}>
            Logowanie
          </Typography>

          <Typography
            variant="body2"
            color="text.secondary"
            textAlign="center"
            sx={{ mb: 2 }}
          >
          Wprowadź swój 10-cyfrowy login oraz hasło, aby się zalogować
          </Typography>

          <TextField
              label="Login ID"
              variant="outlined"
              value={loginID}
              onChange={(e) => setLoginID(e.target.value)}
              fullWidth
              margin="normal"
          />
          <TextField
              label="Hasło"
              type="password"
              variant="outlined"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              fullWidth
              margin="normal"
          />
          <Button
              variant="contained"
              color="primary"
              onClick={handleLogin}
              fullWidth
              sx={{mt: 2}}
          >
            Zaloguj się
          </Button>
        </Box>
      </Box>
  );
}

export default Login;