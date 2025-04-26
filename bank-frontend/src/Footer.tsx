import { Box, Typography } from "@mui/material";

const Footer = () => (
  <Box
    sx={{
      backgroundColor: "#121212",
      py: 1,
      textAlign: "center",
      position: "fixed",
      bottom: 0,
      left: 0,
      right: 0,
      zIndex: 1000,
    }}
  >
    <Typography variant="caption" color="white">
      JMK Bank – Systemy Rozproszone 2024/2025
    </Typography>
  </Box>
);

export default Footer;