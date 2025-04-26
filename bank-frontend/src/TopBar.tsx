import { AppBar, Box, Toolbar, Button, Typography } from "@mui/material";
import logo from "./assets/JKM_Bank_Logo.png";

const TopBar = ({ onLogout }: { onLogout: () => void }) => (
  <AppBar position="fixed" sx={{ height: "64px", justifyContent: "center", backgroundColor: "#a4b9bf" }}>
    <Toolbar sx={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
      <Box sx={{ display: "flex", alignItems: "center" }}>
        <img src={logo} alt="Logo" style={{ height: "64px", width: "64px" }} />
      </Box>

      <Box sx={{ display: "flex", gap: 3 }}>
        <Typography variant="body1" sx={{ cursor: "default", color: "#0F4C81", fontWeight: 'bold' }}>
          ZGŁOŚ PROBLEM
        </Typography>
        <Typography variant="body1" sx={{ cursor: "default", color: "#0F4C81", fontWeight: 'bold' }}>
          KONTAKT
        </Typography>
        <Typography variant="body1" sx={{ cursor: "default", color: "#0F4C81", fontWeight: 'bold' }}>
          FAQ
        </Typography>
      </Box>

      <Box>
        <Button
          variant="contained"
          color="primary"
          onClick={onLogout}
          sx={{ height: "40px" }}
        >
          Wyloguj
        </Button>
      </Box>
    </Toolbar>
  </AppBar>
);

export default TopBar;