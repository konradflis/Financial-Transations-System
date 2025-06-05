import { useEffect, useState, ChangeEvent } from "react";
import { useNavigate } from "react-router-dom";
import { Box, Typography, Button, Paper, FormControl, InputLabel, Select, MenuItem,
  Card, CardContent, CircularProgress, Table, TableCell, TableRow, TableBody, TableHead,
  Modal, TextField } from "@mui/material";
import { SelectChangeEvent } from '@mui/material/Select'
import TopBar from './TopBar'
import Footer from './Footer'
import logo from './assets/JKM_Bank_Logo.png'


interface Account {
  id: number;
  name: string;
}

interface DashboardData {
  message: string;
}

interface Transaction {
  id: number;
  date: string;
  receiver: string;
  amount: number;
  transaction_type: string;
  status: string;
}

const UserDashboard = () => {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [selectedAccount, setSelectedAccount] = useState<Account | null>(null);
  const [balance, setBalance] = useState<number | null>(null);
  const [balanceLoading, setBalanceLoading] = useState(false);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const navigate = useNavigate();
  const [isTransferOpen, setIsTransferOpen] = useState(false);
  const [receiver, setReceiver] = useState("");
  const [amount, setAmount] = useState("");

  const [card_id, setCard_id] = useState<number | null>(null);
  const [atm_id, setATM_id] = useState<number | null>(null);
  const [isWithdrawalOpen, setIsWithdrawalOpen] = useState(false);
  const [isATMVerified, setIsATMVerified] = useState(false);
  const [isAmountOpen, setIsAmountOpen] = useState(false);
  const [pin, setPin] = useState("");
  const [isConfirmationOpen, setIsConfirmationOpen] = useState(false);
  const [lastestTransaction, setLastestTransaction] = useState<number | null>(null);
  const [confirmationData, setConfirmationData] = useState("");

  const [isDepositOpen, setIsDepositOpen] = useState(false);

  const [filters, setFilters] = useState({
    date: '',
    receiver: '',
    amount: '',
    transaction_type: '',
    status: '',
  });

  const handleFilterChange = (
    e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement> | SelectChangeEvent<string>
  ) => {
    const { name, value } = e.target;

    setFilters((prevFilters) => ({
      ...prevFilters,
      [name]: value,
    }));
  };

  const filteredTransactions = transactions.filter((tx) => {
    return (
      (filters.date ? tx.date.includes(filters.date) : true) &&
      (filters.receiver ? tx.receiver.includes(filters.receiver) : true) &&
      (filters.amount ? tx.amount.toString().includes(filters.amount) : true) &&
      (filters.transaction_type ? tx.transaction_type.includes(filters.transaction_type) : true) &&
      (filters.status ? tx.status.includes(filters.status) : true)
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
      const response = await fetch("http://localhost:8000/user/dashboard", {
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

  const fetchAccounts = async () => {
    const token = localStorage.getItem("token");
    try {
      const response = await fetch("http://localhost:8000/user/accounts", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (response.ok) {
        const accountsData = await response.json();
        setAccounts(accountsData);
        setSelectedAccount(accountsData[0]);
      } else {
        setError("Nie udało się pobrać kont użytkownika");
      }
    } catch (e) {
      console.error("Błąd ładowania kont:", e);
    }
  };

  const fetchTransactions = async (accountId: number) => {
    const token = localStorage.getItem("token");
    try {
      const response = await fetch(`http://localhost:8000/user/account/${accountId}/transactions`, {
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

  const fetchBalance = async (accountId: number) => {
    const token = localStorage.getItem("token");
    try {
      const response = await fetch(`http://localhost:8000/user/account/${accountId}/balance`, {
        headers: {Authorization: `Bearer ${token}`},
      });

      if (response.ok) {
        const res = await response.json();
        setBalance(res.balance);
      } else {
        setBalance(null);
      }
    } catch (err) {
      console.error("Błąd pobierania salda:", err);
    }
  };

  const fetchCard = async (accountId: number) => {
    const token = localStorage.getItem("token");
    try {
      const response = await fetch(`http://localhost:8000/user/account/${accountId}/card_id`, {
        headers: {Authorization: `Bearer ${token}`},
      });

      if (response.ok) {
        const res = await response.json();
        setCard_id(res.card_id);
      } else {
        setCard_id(null);
      }
    } catch (err) {
      console.error("Błąd pobierania danych karty.")
    }
  };

  const fetchATM = async () => {
    const token = localStorage.getItem("token");
    try {
      const response = await fetch(`http://localhost:8000/atm-assignment`, {
        headers: {Authorization: `Bearer ${token}`},
      });

      if (response.ok) {
        const res = await response.json();
        setATM_id(res.atm_id);
      } else {
        setATM_id(null);
      }
    } catch (err) {
      console.error("Brak dostępnych bankomatów.")
      setIsWithdrawalOpen(false);
    }
  };

  const verifyATM = async () => {
    const token = localStorage.getItem("token");
    try {
      const response = await fetch(`http://localhost:8000/atm-operation/verification`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        card_id: card_id,
        atm_id: atm_id,
      }),
    });
      if (response.ok) {
        setIsATMVerified(true);
      }
    } catch (err) {
      console.error("Błąd przy wprowadzaniu karty.")
      setIsATMVerified(false);
      setATM_id(null);
    }
  };

  const verifyPIN = async () => {
    const token = localStorage.getItem("token");
    try {
      const response = await fetch(`http://localhost:8000/atm-operation/pin-verification`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        card_id: card_id,
        pin: pin,
      }),
    });
      if (response.ok) {
        setIsAmountOpen(true);
      }
    } catch (err) {
      console.error("Błąd przy wprowadzaniu karty.")
    }
  };

  const cancelATMOperationStage1 = async () => {

    if (!Number.isFinite(atm_id)) {
      console.error("Brak ID bankomatu.");
      return;
    }
    const token = localStorage.getItem("token");
    try {
      const response = await fetch(`http://localhost:8000/atm-free`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        atm_id: atm_id,
      }),
    });
      if (response.ok) {
        const res = await response.json();
        setIsATMVerified(false);
        setATM_id(null);
        setIsWithdrawalOpen(false);
        setIsDepositOpen(false);
      }
    } catch (err) {
      console.error("Nie rozpoznano bankomatu.")
    }
  };


  const cancelATMOperationStage2 = async () => {
    const token = localStorage.getItem("token");
    try {
      if (selectedAccount) {
        const response = await fetch(`http://localhost:8000/account-free`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          account_id: selectedAccount.id,
        }),
      });
        if (response.ok) {
          setPin("");
          setIsAmountOpen(false);
        }
    }
      cancelATMOperationStage1();   // wywołanie też warunków dla zwolnienia urządzenia

    } catch (err) {
      console.error("Nie rozpoznano bankomatu.")
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
    fetchAccounts();
  }, []);

  useEffect(() => {
    if (selectedAccount !== null) {
      fetchBalance(selectedAccount.id);
      fetchTransactions(selectedAccount.id);
      fetchCard(selectedAccount.id);
    }
  }, [selectedAccount]);

  useEffect(() => {
    if (isWithdrawalOpen || isDepositOpen) {
      fetchATM();
    }
  }, [isWithdrawalOpen, isDepositOpen]);

  useEffect(() => {
    if (Number.isFinite(atm_id)) {
      verifyATM();
    }
  }, [atm_id]);


  const handleTransfer = async () => {
    const token = localStorage.getItem("token");
    if (!token || !selectedAccount) {
      alert("Brak danych do wykonania przelewu.");
      return;
    }

    try {
      const response = await fetch(`http://localhost:8000/transfer`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          sender_account: selectedAccount.name,
          receiver_account: receiver,
          amount: parseFloat(amount),
        }),
      });

      if (response.ok) {
        alert("Przelew w toku...");
        setIsTransferOpen(false);
        setReceiver("");
        setAmount("");
        fetchTransactions(selectedAccount.id);
        fetchBalance(selectedAccount.id);
      } else {
        const errorData = await response.json();
        alert(`Błąd: ${errorData.detail || "Nieznany błąd"}`);
      }
    } catch (err) {
      console.error("Błąd przelewu:", err);
      alert("Wystąpił błąd podczas wykonywania przelewu.");
    }
  };

  const handleWithdrawal = async () => {
    const token = localStorage.getItem("token");
    if (!token || !selectedAccount) {
      alert("Brak danych do wykonania operacji.");
      return;
    }

    if (!atm_id || !card_id || !isWithdrawalOpen) {
      alert("Spróbuj ponownie później.")
      return;
    }

    try {
      const response = await fetch(`http://localhost:8000/atm-operation/withdrawal`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          card_id: card_id,
          atm_id: atm_id,
          amount: parseFloat(amount),
        }),
      });

      if (response.ok) {
        const data = await response.json();
        if (data["status"]=="success") {alert("Wypłata wykonana!");}
        else if (data["status"]=="failure") {alert("Operacja zakończona niepowodzeniem!");}
        else {alert("Operacja oczekuje na weryfikację...");}

        setLastestTransaction(data["transaction_id"]);
        setIsConfirmationOpen(true);  // oczekiwanie na potwierdzenie

        //fetchTransactions(selectedAccount.id);
        //fetchBalance(selectedAccount.id);
      } else {
        const errorData = await response.json();
        alert(`Błąd: ${errorData.detail || "Nieznany błąd"}`);
      }
    } catch (err) {
      console.error("Błąd operacji:", err);
      alert("Wystąpił błąd podczas wykonywania operacji.");
    }
  };


  const handleDeposit = async () => {
    const token = localStorage.getItem("token");
    if (!token || !selectedAccount) {
      alert("Brak danych do wykonania operacji.");
      return;
    }

    if (!atm_id || !card_id || !isDepositOpen) {
      alert("Spróbuj ponownie później.")
      return;
    }

    try {
      const response = await fetch(`http://localhost:8000/atm-operation/deposit`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          card_id: card_id,
          atm_id: atm_id,
          amount: parseFloat(amount),
        }),
      });

      if (response.ok) {
        const data = await response.json();
        if (data["status"]=="success") {alert("Wpłata wykonana!");}
        else if (data["status"]=="failure") {alert("Operacja zakończona niepowodzeniem!");}
        else {alert("Operacja oczekuje na weryfikację...");}

        setLastestTransaction(data["transaction_id"]);
        setIsConfirmationOpen(true);  // oczekiwanie na potwierdzenie

        //fetchTransactions(selectedAccount.id);
        //fetchBalance(selectedAccount.id);
      } else {
        const errorData = await response.json();
        alert(`Błąd: ${errorData.detail || "Nieznany błąd"}`);
      }
    } catch (err) {
      console.error("Błąd operacji:", err);
      alert("Wystąpił błąd podczas wykonywania operacji.");
    }
  };


  const handleConfirmation = async () => {
    const token = localStorage.getItem("token");
    if (!token || !selectedAccount) {
      alert("Brak danych do wykonania operacji.");
      return;
    }

    if (!isConfirmationOpen) {
      alert("Błąd drukowania potwierdzenia.")
      return;
    }

    try {
      const response = await fetch(`http://localhost:8000/atm-operation/confirmation?transaction_id=${lastestTransaction}`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data= await response.json();
        setConfirmationData(data["confirmation"]);

        setAmount("");
        setIsConfirmationOpen(false);
        setLastestTransaction(null);

        cancelATMOperationStage2();

        fetchTransactions(selectedAccount.id);
        fetchBalance(selectedAccount.id);

      } else {
        const errorData = await response.json();
        alert(`Błąd: ${errorData.detail || "Nieznany błąd"}`);
      }
    } catch (err) {
      console.error("Błąd operacji:", err);
      alert("Wystąpił błąd podczas wykonywania operacji.");
    }
  };

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
                backdropFilter: "blur(10px)",
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
              overflow: "auto",
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
                    <Typography variant="h5" gutterBottom fontWeight="bold">
                      Serwis transakcyjny
                    </Typography>
                  </Box>

                  <Box sx={{ display: "flex", alignItems: "center" }}>
                    <img src={logo} alt="Logo" style={{ height: "64px", width: "64px" }} />
                  </Box>
                </Box>
                <Typography variant="subtitle1" gutterBottom>
                  {data?.message ?? "Twoje konto"}
                </Typography>

                <Box mt={3}>
                  <Typography variant="body1" gutterBottom fontWeight="bold">
                    Wybierz konto:
                  </Typography>
                  <Select
                    fullWidth
                    value={selectedAccount?.id ? selectedAccount.id : ""}
                    onChange={(e) => {
                      const selectedAccount = accounts.find(acc => acc.id === e.target.value);
                      setSelectedAccount(selectedAccount || null);
                    }}
                    displayEmpty
                    variant="outlined"
                    size="small"
                  >
                    <MenuItem value="">
                      <em>-- wybierz konto --</em>
                    </MenuItem>
                    {accounts.map((acc) => (
                      <MenuItem key={acc.id} value={acc.id}>
                        {acc.name}
                      </MenuItem>
                    ))}
                  </Select>
                </Box>

                <Box mt={4}>
                  <Typography variant="body1" fontWeight="bold">Saldo:</Typography>
                  <Typography variant="body1" color="primary">
                    {balanceLoading
                        ? "Ładowanie..."
                        : balance !== null
                            ? `${balance.toFixed(2)} PLN`
                            : "Brak danych"}
                  </Typography>
                  <Button
                    sx={{ mt: 2 }}
                    variant="contained"
                    color="primary"
                    fullWidth
                    onClick={() => setIsTransferOpen(true)}
                    disabled={!selectedAccount}
                  >
                    Wykonaj przelew
                  </Button>
                  <Button
                    sx={{ mt: 2 }}
                    variant="contained"
                    color="primary"
                    fullWidth
                    onClick={() => {setIsWithdrawalOpen(true); setIsDepositOpen(false)}}
                    disabled={!selectedAccount}
                  >
                    Wypłata środków
                  </Button>
                  <Button
                    sx={{ mt: 2 }}
                    variant="contained"
                    color="primary"
                    fullWidth
                    onClick={() => {setIsDepositOpen(true); setIsWithdrawalOpen(false)}}
                    disabled={!selectedAccount}
                  >
                    Wpłata środków
                  </Button>
                </Box>
              </Box>
            </Box>

            {/* PRAWA STRONA */}
            <Box sx={{ width: "70%", }}>
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
                  name="receiver"
                  value={filters.receiver}
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
              </Box>
              <Box
                sx={{
                  maxHeight: "400px",
                  overflowY: "auto",
                }}
              >
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell sx={{ fontWeight: 'bold' }}>Data</TableCell>
                    <TableCell sx={{ fontWeight: 'bold' }}>Odbiorca</TableCell>
                    <TableCell sx={{ fontWeight: 'bold' }}>Kwota</TableCell>
                    <TableCell sx={{ fontWeight: 'bold' }}>Typ</TableCell>
                    <TableCell sx={{ fontWeight: 'bold' }}>Status</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {filteredTransactions.length > 0 ? (
                    filteredTransactions.map((tx) => (
                      <TableRow key={tx.id}>
                        <TableCell>{formatDate(tx.date)}</TableCell>
                        <TableCell>{tx.receiver}</TableCell>
                        <TableCell>{tx.amount.toFixed(2)} PLN</TableCell>
                        <TableCell>{tx.transaction_type}</TableCell>
                        <TableCell>{tx.status}</TableCell>
                      </TableRow>
                    ))
                  ) : (
                    <TableRow>
                      <TableCell colSpan={5} align="center">
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
            open={isTransferOpen}
            onClose={() => setIsTransferOpen(false)}
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
                Nowy przelew
              </Typography>
              <TextField
                fullWidth
                label="Odbiorca"
                value={receiver}
                onChange={(e) => setReceiver(e.target.value)}
                sx={{ mb: 2 }}
              />
              <TextField
                fullWidth
                label="Kwota"
                type="number"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                sx={{ mb: 2 }}
              />
              <Box display="flex" justifyContent="space-between">
                <Button variant="outlined" onClick={() => setIsTransferOpen(false)}>
                  Anuluj
                </Button>
                <Button
                  variant="contained"
                  color="primary"
                  onClick={() => handleTransfer()}
                  disabled={!receiver || !amount}
                >
                  Zatwierdź
                </Button>
              </Box>
            </Box>
          </Modal>

          <Modal
            open={(isWithdrawalOpen || isDepositOpen) && Number.isFinite(atm_id) && isATMVerified}
            aria-labelledby="withdrawal-verification-modal"
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

              <Typography id="withdrawal-verification-modal" variant="h6" mb={2}>
                Proszę wprowadzić PIN:
              </Typography>
              <TextField
                fullWidth
                label="PIN"
                type="password"
                value={pin}
                onChange={(e) => {
                  const value = e.target.value;
                  if (/^\d{0,4}$/.test(value)) {
                    setPin(value);
                  }
                }}
                inputProps={{ maxLength: 4 }}
                sx={{ mb: 2 }}
              />
              <Box display="flex" justifyContent="space-between">
                <Button variant="outlined" onClick={() => cancelATMOperationStage2()}>
                  Anuluj
                </Button>
                <Button
                  variant="contained"
                  color="primary"
                  onClick={() => verifyPIN()}
                  disabled={!atm_id || !isATMVerified || (!isWithdrawalOpen && !isDepositOpen) || (isWithdrawalOpen && isDepositOpen)}
                >
                  Zatwierdź
                </Button>

              </Box>
            </Box>
          </Modal>

          <Modal
            open={isWithdrawalOpen && Number.isFinite(atm_id) && isATMVerified && isAmountOpen}
            aria-labelledby="withdrawal-modal"
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
              <Typography id="withdrawal-modal" variant="h6" mb={2}>
                Wypłata środków
              </Typography>
              <TextField
                fullWidth
                label="Kwota"
                type="number"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                sx={{ mb: 2 }}
              />
              <Box display="flex" justifyContent="space-between">
                <Button variant="outlined" onClick={() => cancelATMOperationStage2()}>
                  Anuluj
                </Button>
                <Button
                  variant="contained"
                  color="primary"
                  onClick={() => handleWithdrawal()}
                  disabled={!isWithdrawalOpen || !atm_id || !isATMVerified || !isAmountOpen}
                >
                  Zatwierdź
                </Button>
              </Box>
            </Box>
          </Modal>

          <Modal
            open={isDepositOpen && Number.isFinite(atm_id) && isATMVerified && isAmountOpen}
            aria-labelledby="deposit-modal"
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
              <Typography id="deposit-modal" variant="h6" mb={2}>
                Wpłata środków
              </Typography>
              <TextField
                fullWidth
                label="Kwota"
                type="number"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                sx={{ mb: 2 }}
              />
              <Box display="flex" justifyContent="space-between">
                <Button variant="outlined" onClick={() => cancelATMOperationStage2()}>
                  Anuluj
                </Button>
                <Button
                  variant="contained"
                  color="primary"
                  onClick={() => handleDeposit()}
                  disabled={!isDepositOpen || !atm_id || !isATMVerified || !isAmountOpen}
                >
                  Zatwierdź
                </Button>
              </Box>
            </Box>
          </Modal>

          <Modal
            open={isConfirmationOpen}
            onClose={() => {setIsConfirmationOpen(false); setIsAmountOpen(false)}}
            aria-labelledby="confirmation-modal"
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
              <Typography id="confirmation-modal" variant="h6" mb={2}>
                Wydrukować potwierdzenie transakcji?
              </Typography>
              <Box display="flex" justifyContent="space-between">
                <Button variant="outlined" onClick={() => {handleConfirmation(); setIsConfirmationOpen(false)}}>
                  TAK
                </Button>
                 <Button variant="outlined" onClick={() => {setIsConfirmationOpen(false); setAmount(""); cancelATMOperationStage2()}}>
                  NIE
                </Button>
              </Box>
            </Box>
          </Modal>

          <Modal
            open={!!confirmationData?.trim()}
            onClose={() => setConfirmationData("")}
            aria-labelledby="confirmation-show-modal"
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
              <Typography id="confirmation-show-modal" variant="h6" mb={2}>
                Potwierdzenie
              </Typography>
              <Typography variant="body1">
                {confirmationData.split("\n").map((line, index) => (
                  <span key={index}>
                    {line}
                    <br />
                  </span>
                ))}
              </Typography>
              <Box display="flex" justifyContent="space-between">
                <Button variant="outlined" onClick={() => setConfirmationData("")}>
                  OK!
                </Button>

              </Box>
            </Box>
          </Modal>

        </Box>
      </Box>
    <Footer />
  </>
  );
};

export default UserDashboard;
