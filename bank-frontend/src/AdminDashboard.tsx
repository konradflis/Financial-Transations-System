import {ChangeEvent, useEffect, useState} from "react";
import { useNavigate } from "react-router-dom";
import {
  Box, Typography, Button, Paper, Select, MenuItem, Table, TableHead, TableRow, TableCell,
  TableBody, Modal, TextField, FormControl, InputLabel, Checkbox, FormControlLabel, CircularProgress
} from "@mui/material";
import { LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer } from 'recharts';
import {SelectChangeEvent} from "@mui/material/Select";
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDayjs } from "@mui/x-date-pickers/AdapterDayjs";
import { Dayjs } from 'dayjs';
import TopBar from './TopBar'
import Footer from './Footer'
import logo from './assets/JKM_Bank_Logo.png'

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
  const [isDeleteATMOpen, setIsDeleteATMOpen] = useState(false);
  const [granularity, setGranularity] = useState<'days' | 'hours' | 'minutes'>('days');
  const [selectedStatus, setSelectedStatus] = useState<'pending' | "completed" | "cancelled" | "failed" | null>(null);
  const [transactionData, setTransactionData] = useState<{ time: string, count: number }[]>([]);
const [startDate, setStartDate] = useState<Dayjs | null>(null);
const [endDate, setEndDate] = useState<Dayjs | null>(null);


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

  const fetchTransactionStats = async (granularity: string, status?: string, start?: string, end?: string) => {
    const token = localStorage.getItem("token");

    try {
      const url = new URL("http://localhost:8000/admin/transaction-stats");
      url.searchParams.append("granularity", granularity);
      if (status && status !== "undefined") {
        url.searchParams.append('status', status as string);
      }

      if (start) {
        url.searchParams.append('start_date', start);
      }

      if (end) {
        url.searchParams.append('end_date', end);
      }

      const response = await fetch(url.toString(), {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        if (data.length === 0) {
          setTransactionData([]);
        } else {
          setTransactionData(data);
        }
      } else {
        console.error('Błąd pobierania statystyk');
        setTransactionData([]);
      }
    } catch (error) {
      console.error('Błąd połączenia:', error);
      setTransactionData([]);
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
      setIsDeleteATMOpen(false);
      fetchAtmDevices();
    } catch (err) {
      console.error("Błąd usuwania wpłatomatów:", err);
      alert("Wystąpił błąd podczas usuwania wpłatomatów.");
    } finally {
      setLoading(false);
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
    fetchTransactionStats(granularity, selectedStatus ?? undefined,
        startDate ? startDate.toISOString().split('T')[0] : undefined,
        endDate ? endDate.toISOString().split('T')[0] : undefined);
  }, [granularity, selectedStatus, startDate, endDate]);

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
                  <Typography variant="h5" gutterBottom fontWeight="bold">
                    Panel administratora
                  </Typography>
                </Box>

                <Box sx={{ display: "flex", alignItems: "center" }}>
                  <img src={logo} alt="Logo" style={{ height: "64px", width: "64px" }} />
                </Box>
              </Box>
              <Typography variant="subtitle1" gutterBottom>
              {data?.message ?? "Twoje konto"}
              </Typography>
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
                  onClick={() => setIsDeleteATMOpen(true)}
                >
                  Usuń bankomat
                </Button>
              </Box>
            </Box>
          </Box>

          <Box sx={{width: "70%", flexDirection: "column",}}>
            <Typography variant="h5" gutterBottom fontWeight="bold">
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
                <MenuItem value="completed">completed</MenuItem>
                <MenuItem value="cancelled">cancelled</MenuItem>
                <MenuItem value="failed">failed</MenuItem>
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
                  <TableCell sx={{ fontWeight: 'bold' }}>Data</TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>Nadawca</TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>Odbiorca</TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>Kwota</TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>Typ</TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>Status</TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>Urządzenie</TableCell>
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

          <Box sx={{ mt: 4 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <Typography variant="h5" fontWeight="bold">
                Analiza ruchu
              </Typography>
            </Box>

            <Box sx={{ display: 'flex', justifyContent: 'space-between', gap: 2 }}>
              <FormControl size="small" sx={{ minWidth: 120, flex: 1 }}>
                <InputLabel>Granulacja</InputLabel>
                <Select
                  value={granularity}
                  onChange={(e) => setGranularity(e.target.value as 'days' | 'hours' | 'minutes')}
                  size="small"
                  sx={{ width: '100%' }}
                >
                  <MenuItem value="">Dni</MenuItem>
                  <MenuItem value="days">Dni</MenuItem>
                  <MenuItem value="hours">Godziny</MenuItem>
                  <MenuItem value="minutes">Minuty</MenuItem>
                </Select>
              </FormControl>

              <FormControl size="small" sx={{ minWidth: 120, flex: 1 }}>
                <InputLabel>Stan</InputLabel>
                <Select
                  value={selectedStatus ?? ''}
                  onChange={(e) => setSelectedStatus(e.target.value as "pending" | "completed" | "cancelled" | "failed" | null)}
                  size="small"
                  sx={{ width: '100%' }}
                >
                  <MenuItem value="undefined">Wszystkie</MenuItem>
                  <MenuItem value="pending">Oczekujące</MenuItem>
                  <MenuItem value="completed">Zakończone</MenuItem>
                  <MenuItem value="cancelled">Anulowane</MenuItem>
                  <MenuItem value="failed">Odrzucone</MenuItem>
                </Select>
              </FormControl>

              <LocalizationProvider dateAdapter={AdapterDayjs}>
                <DatePicker
                  label="Data początkowa"
                  value={startDate}
                  onChange={(newValue) => setStartDate(newValue)}
                  slotProps={{ textField: { size: 'small' } }}
                  sx={{ flex: 1 }}
                />
                <DatePicker
                  label="Data końcowa"
                  value={endDate}
                  onChange={(newValue) => setEndDate(newValue)}
                  slotProps={{ textField: { size: 'small' } }}
                  sx={{ flex: 1 }}
                />
              </LocalizationProvider>
            </Box>
          </Box>

          <Box sx={{ width: '100%', height: 300, mt: 2 }}>
            <ResponsiveContainer>
              {transactionData.length === 0 ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
                  <Typography variant="h6" color="textSecondary">
                    Brak danych do wyświetlenia
                  </Typography>
                </Box>
              ) : (
                <LineChart data={transactionData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis
                    label={{
                      value: 'Liczba transakcji',
                      angle: -90,
                      position: 'insideLeft',
                      allowDecimals: false,
                      style: { textAnchor: 'middle' }
                    }}
                  />
                  <Tooltip />
                  <Line type="monotone" dataKey="count" stroke="#1976d2" strokeWidth={2} />
                </LineChart>
              )}
            </ResponsiveContainer>
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
          open={isDeleteATMOpen}
          onClose={() => setIsDeleteATMOpen(false)}
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

            {loading ? (
              <CircularProgress />
            ) : error ? (
              <Typography color="error">{error}</Typography>
            ) : (
              <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
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
              <Button variant="outlined" onClick={() => setIsDeleteATMOpen(false)}>
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
      </Box>
    <Footer />
  </>
  );
}

export default AdminDashboard;
