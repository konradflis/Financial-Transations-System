import {ChangeEvent, useEffect, useState} from "react";
import { useNavigate } from "react-router-dom";
import {
  Box, Typography, Button, Paper, Select, MenuItem, Table, TableHead, TableRow, TableCell,
  TableBody, Modal, TextField, FormControl, InputLabel, Checkbox, FormControlLabel, CircularProgress
} from "@mui/material";
import {SelectChangeEvent} from "@mui/material/Select";

interface DashboardData {
  message: string;
}

interface Transaction {
  id: number;
  date: string;
  from_account_id: number;
  to_account_id: number;
  transaction_type: string;
  amount: number;
  status: string;
  device: string;
}

const AdminDashboard = () => {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const navigate = useNavigate();
  const [isCreateATMOpen, setIsCreateATMOpen] = useState(false);
  const [ATMLocalization, setATMLocalization] = useState("");
  const [atmDevices, setAtmDevices] = useState<any[]>([]);
  const [selectedAtms, setSelectedAtms] = useState<Set<number>>(new Set());
  const [isPopupOpen, setIsPopupOpen] = useState(false);

  const [filters, setFilters] = useState({
    date: '',
    from_account_id: '',
    to_account_id: '',
    amount: '',
    transaction_type: '',
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
      (filters.transaction_type ? tx.transaction_type.includes(filters.transaction_type) : true) &&
      (filters.status ? tx.status.includes(filters.status) : true) &&
      (filters.device ? tx.device.includes(filters.device) : true)
    );
  });

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

  const fetchTransactions = async () => {
    const token = localStorage.getItem("token");
    try {
      const response = await fetch(`http://localhost:8000/admin/transactions`, {
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

  const fetchAtmDevices = async () => {
    setLoading(true);
    const token = localStorage.getItem("token");
    try {
      const response = await fetch("http://localhost:8000/admin/atms", {
        headers: {Authorization: `Bearer ${token}`},
      });
      if (response.ok) {
        const data = await response.json();
        setAtmDevices(data);
      } else {
        setError("Nie udało się załadować wpłatomatów");
      }
    } catch (err) {
      console.error("Błąd pobierania wpłatomatów:", err);
      setError("Błąd połączenia");
    } finally {
      setLoading(false);
    }
  };

  const handleATMCreation = async () => {
    const token = localStorage.getItem("token");

    if (!token || !ATMLocalization) {
      alert("Brak danych do utworzenia bankomatu.");
      return;
    }

    try {
      const response = await fetch("http://localhost:8000/admin/add-atm", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          localization: ATMLocalization,
          status: "ready",
        }),
      });

      if (response.ok) {
        alert("Bankomat utworzony!");
        setATMLocalization("");
      } else {
        const errorData = await response.json();
        alert(`Błąd: ${errorData.detail || "Nieznany błąd"}`);
      }
    } catch (err) {
      console.error("Błąd tworzenia bankomatu:", err);
      alert("Wystąpił błąd podczas tworzenia bankomatu.");
    }
  };

  const handleCheckboxChange = (id: number) => {
    setSelectedAtms((prevSelected) => {
      const newSelected = new Set(prevSelected);
      if (newSelected.has(id)) {
        newSelected.delete(id);
      } else {
        newSelected.add(id);
      }
      return newSelected;
    });
  };

  const deleteSelectedAtms = async () => {
    const token = localStorage.getItem("token");
    setLoading(true);
    try {
      for (let id of selectedAtms) {
        const response = await fetch(`http://localhost:8000/admin/delete-atm?atm_id=${id}`, {
          method: "DELETE",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (!response.ok) {
          const errorData = await response.json();
          alert(`Błąd przy usuwaniu wpłatomatu o ID ${id}: ${errorData.detail || "Nieznany błąd"}`);
        }
      }

      alert("Wypłatomaty zostały usunięte!");
      setSelectedAtms(new Set());
      setIsPopupOpen(false);
      fetchAtmDevices();
    } catch (err) {
      console.error("Błąd usuwania wpłatomatów:", err);
      alert("Wystąpił błąd podczas usuwania wpłatomatów.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
    fetchTransactions();
    fetchAtmDevices();
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
          sx={{height: "100vh", bgcolor: "#4682B4", p: 2, overflow: "hidden"}}
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
          {/* LEWA STRONA */}
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
                    Panel administratora
                  </Typography>
                </Box>

                {/* Przycisk Wyloguj się */}
                <Button
                  variant="contained"
                  color="primary"
                  onClick={handleLogout}
                  sx={{ height: "40px" }}
                >
                  Wyloguj
                </Button>
              </Box>
              <Box>
                <Button
                  sx={{ mt: 2 }}
                  variant="contained"
                  color="primary"
                  fullWidth
                  onClick={() => setIsCreateATMOpen(true)}
                >
                  Wprowadź bankomat
                </Button>
                <Button
                  sx={{ mt: 2 }}
                  variant="contained"
                  color="primary"
                  fullWidth
                  onClick={() => setIsPopupOpen(true)}
                >
                  Usuń wpłatomat
                </Button>
              </Box>
            </Box>
          </Box>

          {/* PRAWA STRONA */}
          <Box sx={{width: "70%",}}>
            <Typography variant="h5" gutterBottom>
              Historia transakcji
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
                name="transaction_type"
                value={filters.transaction_type}
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
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredTransactions.length > 0 ? (
                    filteredTransactions.map((tx) => (
                        <TableRow key={tx.id}>
                          <TableCell>{tx.date}</TableCell>
                          <TableCell>{tx.from_account_id}</TableCell>
                          <TableCell>{tx.to_account_id}</TableCell>
                          <TableCell>{tx.amount.toFixed(2)} PLN</TableCell>
                          <TableCell>{tx.transaction_type}</TableCell>
                          <TableCell>{tx.status}</TableCell>
                          <TableCell>{tx.device}</TableCell>
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
        <Modal
          open={isCreateATMOpen}
          onClose={() => setIsCreateATMOpen(false)}
          aria-labelledby="transfer-modal"
        >
          <Box
            sx={{
              position: "absolute",
              top: "50%",
              left: "50%",
              transform: "translate(-50%, -50%)",
              bgcolor: "background.paper",
              p: 4,
              borderRadius: 2,
              boxShadow: 24,
              minWidth: 300,
            }}
          >
            <Typography id="transfer-modal" variant="h6" mb={2}>
              Nowy bankomat
            </Typography>
            <TextField
              fullWidth
              label="Lokalizacja"
              value={ATMLocalization}
              onChange={(e) => setATMLocalization(e.target.value)}
              sx={{ mb: 2 }}
            />
            <Box display="flex" justifyContent="space-between">
              <Button variant="outlined" onClick={() => setIsCreateATMOpen(false)}>
                Anuluj
              </Button>
              <Button
                variant="contained"
                color="primary"
                onClick={() => handleATMCreation()}
                disabled={!ATMLocalization}
              >
                Zatwierdź
              </Button>
            </Box>
          </Box>
        </Modal>
        <Modal
          open={isPopupOpen}
          onClose={() => setIsPopupOpen(false)}
          aria-labelledby="modal-title"
          aria-describedby="modal-description"
        >
          <Box
            sx={{
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
            }}
          >
            <Typography id="modal-title" variant="h6" component="h2" gutterBottom>
              Wybierz wpłatomaty do usunięcia
            </Typography>

            {/* Ładowanie i komunikat błędu */}
            {loading ? (
              <CircularProgress />
            ) : error ? (
              <Typography color="error">{error}</Typography>
            ) : (
              <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
                {/* Lista wpłatomatów z checkboxami */}
                {atmDevices.map((atm) => (
                  <FormControlLabel
                    key={atm.id}
                    control={
                      <Checkbox
                        checked={selectedAtms.has(atm.id)}
                        onChange={() => handleCheckboxChange(atm.id)}
                        color="primary"
                      />
                    }
                    label={`${atm.localization} (ID: ${atm.id})`}
                  />
                ))}
              </Box>
            )}

            <Box sx={{ mt: 2, display: "flex", justifyContent: "space-between" }}>
              <Button variant="outlined" onClick={() => setIsPopupOpen(false)}>
                Anuluj
              </Button>
              <Button
                variant="contained"
                color="error"
                onClick={deleteSelectedAtms}
                disabled={selectedAtms.size === 0}
              >
                Usuń
              </Button>
            </Box>
          </Box>
        </Modal>
      </Box>
  );
}

export default AdminDashboard;
