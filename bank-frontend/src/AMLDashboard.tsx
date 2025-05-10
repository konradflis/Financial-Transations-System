import {ChangeEvent, useEffect, useState} from "react";
import { useNavigate } from "react-router-dom";
import {
  Box, Typography, Button, Paper, Select, MenuItem, Table, TableHead, TableRow, TableCell,
  TableBody, Modal, TextField, FormControl, InputLabel, Checkbox, FormControlLabel, CircularProgress
} from "@mui/material";
import {SelectChangeEvent} from "@mui/material/Select";
import TopBar from "./TopBar";
import Footer from "./Footer";
import logo from "./assets/JKM_Bank_Logo.png";

interface DashboardData {
  message: string;
}

interface Transaction {
  id: number;
  date: string;
  from_account_id: number;
  to_account_id: number;
  type: string;
  amount: number;
  status: string;
  device: string;
}

const AMLDashboard = () => {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [selectedTx, setSelectedTx] = useState<Transaction | null>(null);
  const [reason, setReason] = useState<string | null>(null);

  const [filters, setFilters] = useState({
    date: '',
    from_account_id: '',
    to_account_id: '',
    amount: '',
    type: '',
    status: '',
    device: ''
  });

  const handleFilterChange = (
    e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement> | SelectChangeEvent<string>) => {
    const { name, value } = e.target;

    setFilters((prevFilters) => ({
      ...prevFilters,
      [name]: value,
    }));
  };

  const filteredTransactions = transactions.filter((tx) => {
    return (
      (filters.date ? tx.date.includes(filters.date) : true) &&
      (filters.to_account_id ? tx.to_account_id === Number(filters.to_account_id) : true) &&
      (filters.from_account_id ? tx.from_account_id === Number(filters.from_account_id) : true) &&
      (filters.amount ? tx.amount.toString().includes(filters.amount) : true) &&
      (filters.type ? tx.type.includes(filters.type) : true) &&
      (filters.status ? tx.status.includes(filters.status) : true) &&
      (filters.device ? tx.device.includes(filters.device) : true)
    );
  });

  const handleLogout = () => {
    localStorage.removeItem("token");
    navigate("/");
  };

  const handleOpen = async (tx: Transaction) => {
    setSelectedTx(tx);
    setOpen(true);
    const token = localStorage.getItem("token");

    try {
      const response = await fetch(`http://localhost:8000/aml/reason?id=${tx.id}`, {
        method: "GET",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const res = await response.json();
        setReason(res.reasoning);
      } else {
        setReason("Brak powodu lub błąd podczas pobierania.");
      }
    } catch (err) {
      console.error("Błąd przy pobieraniu powodu:", err);
      setReason("Błąd serwera.");
    }
  };

  const handleClose = () => {
    setOpen(false);
    setSelectedTx(null);
  };

  const handleAccept = async () => {
    if (!selectedTx) return;
    const token = localStorage.getItem("token");

    try {
      const response = await fetch(`http://localhost:8000/aml/accept`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ id: selectedTx.id }),
      });

      if (response.ok) {
        fetchTransactions(); // refresh the data
        handleClose();
      } else {
        console.error("Nie udało się zaakceptować transakcji");
      }
    } catch (err) {
      console.error("Błąd przy akceptacji transakcji:", err);
    }
  };

  const handleReject = async () => {
    if (!selectedTx) return;
    const token = localStorage.getItem("token");

    try {
      const response = await fetch(`http://localhost:8000/aml/reject`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ id: selectedTx.id }),
      });

      if (response.ok) {
        fetchTransactions(); // refresh the data
        handleClose();
      } else {
        console.error("Nie udało się odrzucić transakcji");
      }
    } catch (err) {
      console.error("Błąd przy odrzucaniu transakcji:", err);
    }
  };

  const fetchDashboard = async () => {
    const token = localStorage.getItem("token");

    if (!token) {
      alert("Brak tokenu, nie jesteś zalogowany!");
      navigate("/");
      return;
    }

    try {
      const response = await fetch("http://localhost:8000/aml/dashboard", {
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

  const fetchTransactions = async () => {
    const token = localStorage.getItem("token");
    try {
      const response = await fetch(`http://localhost:8000/aml/transactions`, {
        headers: {Authorization: `Bearer ${token}`},
      });

      if (response.ok) {
        const res: Transaction[] = await response.json();
        setTransactions(res);
      } else {
        setTransactions([]);
      }
    } catch (err) {
      console.error("Błąd pobierania transakcji:", err);
    }
  };

  const fetchReason = async () => {
    const token = localStorage.getItem("token");
    try {
      const response = await fetch(`http://localhost:8000/aml/reason`, {
        headers: {Authorization: `Bearer ${token}`},
      });

      if (response.ok) {
        const res: Transaction[] = await response.json();
        setTransactions(res);
      } else {
        setTransactions([]);
      }
    } catch (err) {
      console.error("Błąd pobierania transakcji:", err);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const options: Intl.DateTimeFormatOptions = {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    };
    return date.toLocaleString('pl-PL', options);
  };

  useEffect(() => {
    fetchDashboard();
    fetchTransactions();
  }, []);

  if (loading) {
    return <div>Ładowanie...</div>;
  }

  if (error) {
    return <div>{error}</div>;
  }

  return (
  <>

    <TopBar onLogout={handleLogout} />
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        minHeight: "100vh",
        pt: "64px",
        pb: "64px",
        position: "relative",
        backgroundColor: "#eef1f3",
        overflow: "hidden"
      }}
    >
        <Box
          component="main"
          sx={{
                flexGrow: 1,
                bgcolor: "#eef1f3",
                display: "flex",
                justifyContent: "center",
                alignItems: "center",
                p: 2,
                overflowY: "hidden",
                scrollBehavior: "smooth",
                backdropFilter: "blur(3px)",
                border: "1px solid rgba(255, 255, 255, 0.2)"
          }}
        >
        <Paper
            elevation={4}
            sx={{
              display: "flex",
              flexDirection: "row",
              width: "100%",
              maxWidth: "1200px",
              height: "auto",
              p: 3,
              gap: 4,
            }}
        >

          <Box
              sx={{
                width: "30%",
                display: "flex",
                flexDirection: "column",
                justifyContent: "space-between",
              }}
          >
            <Box>
              <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <Box>
                  <Typography variant="h5" gutterBottom>
                    Panel AML
                  </Typography>
                </Box>

                <Box sx={{ display: "flex", alignItems: "center" }}>
                  <img src={logo} alt="Logo" style={{ height: "64px", width: "64px" }} />
                </Box>
              </Box>
            </Box>
          </Box>

          {/* PRAWA STRONA */}
          <Box sx={{width: "70%",}}>
            <Typography variant="h5" gutterBottom>
              Transakcje wymagające weryfikacji
            </Typography>
            <Box sx={{ display: "flex", gap: 2, mb: 2 }}>
            <TextField
              label="Data"
              variant="outlined"
              size="small"
              name="date"
              value={filters.date}
              onChange={handleFilterChange}
              fullWidth
            />
            <TextField
              label="Odbiorca"
              variant="outlined"
              size="small"
              name="to_account_id"
              value={filters.to_account_id}
              onChange={handleFilterChange}
              fullWidth
            />
            <TextField
              label="Nadawca"
              variant="outlined"
              size="small"
              name="from_account_id"
              value={filters.from_account_id}
              onChange={handleFilterChange}
              fullWidth
            />
            <TextField
              label="Kwota"
              variant="outlined"
              size="small"
              name="amount"
              value={filters.amount}
              onChange={handleFilterChange}
              fullWidth
            />
            <FormControl fullWidth size="small">
              <InputLabel>Typ</InputLabel>
              <Select
                label="Typ"
                name="type"
                value={filters.type}
                onChange={handleFilterChange}
              >
                <MenuItem value="">all</MenuItem>
                <MenuItem value="transfer">transfer</MenuItem>
                <MenuItem value="withdrawal">withdrawal</MenuItem>
                <MenuItem value="deposit">deposit</MenuItem>
              </Select>
            </FormControl>
            <FormControl fullWidth size="small">
              <InputLabel>Status</InputLabel>
              <Select
                label="Status"
                name="status"
                value={filters.status}
                onChange={handleFilterChange}
              >
                <MenuItem value="">all</MenuItem>
                <MenuItem value="pending">pending</MenuItem>
                <MenuItem value="success">success</MenuItem>
                <MenuItem value="cancelled">cancelled</MenuItem>
              </Select>
            </FormControl>
            <TextField
              label="Urządzenie"
              variant="outlined"
              size="small"
              name="device"
              value={filters.device}
              onChange={handleFilterChange}
              fullWidth
            />
          </Box>
          <Box
            sx={{
              maxHeight: "500px",
              overflowY: "auto",
            }}
          >
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Data</TableCell>
                  <TableCell>Nadawca</TableCell>
                  <TableCell>Odbiorca</TableCell>
                  <TableCell>Kwota</TableCell>
                  <TableCell>Typ</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Urządzenie</TableCell>
                  <TableCell>Decyzja</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredTransactions.length > 0 ? (
                    filteredTransactions.map((tx) => (
                        <TableRow key={tx.id}>
                          <TableCell>{formatDate(tx.date)}</TableCell>
                          <TableCell>{tx.from_account_id}</TableCell>
                          <TableCell>{tx.to_account_id}</TableCell>
                          <TableCell>{tx.amount.toFixed(2)} PLN</TableCell>
                          <TableCell>{tx.type}</TableCell>
                          <TableCell>{tx.status}</TableCell>
                          <TableCell>{tx.device}</TableCell>
                          <TableCell>
                            <Button onClick={() => handleOpen(tx)}>Oceń</Button>
                          </TableCell>
                        </TableRow>
                    ))
                ) : (
                    <TableRow>
                      <TableCell colSpan={3} align="center">
                        Brak transakcji
                      </TableCell>
                    </TableRow>
                )}
              </TableBody>
            </Table>
          </Box>
          </Box>
        </Paper>
          <Modal open={open} onClose={handleClose} >
            <Box sx={{
              position: "absolute",
              top: "50%",
              left: "50%",
              transform: "translate(-50%, -50%)",
              bgcolor: "background.paper",
              p: 4,
              borderRadius: 2,
              boxShadow: 24,
              maxHeight: "80vh",
              overflowY: "auto",
              width: "80%",
              maxWidth: "600px",
            }}>
              <Typography variant="h6" component="h2">
                Szczegóły Transakcji
              </Typography>
              <Typography variant="subtitle1" sx={{ mt: 2 }}>
                Powód podejrzenia:
              </Typography>
              <Typography variant="body2" sx={{ mb: 2 }}>
                {reason || "Ładowanie..."}
              </Typography>
              <Typography sx={{ mt: 2 }}>
                Czy chcesz zaakceptować tę transakcję?
              </Typography>
              <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 1, mt: 4 }}>
                <Button onClick={handleReject} color="error" variant="outlined">Odrzuć</Button>
                <Button onClick={handleAccept} color="primary" variant="contained">Akceptuj</Button>
              </Box>
            </Box>
          </Modal>
        </Box>
      </Box>
    <Footer />
  </>
  );
}

export default AMLDashboard;
