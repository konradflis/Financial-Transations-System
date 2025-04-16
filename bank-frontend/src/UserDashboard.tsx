import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Box, Typography, Button, Paper, FormControl, InputLabel, Select, MenuItem,
  Card, CardContent, CircularProgress, Table, TableCell, TableRow, TableBody, TableHead } from "@mui/material";

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
}

const UserDashboard = () => {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [selectedAccount, setSelectedAccount] = useState<number | null>(null);
  const [balance, setBalance] = useState<number | null>(null);
  const [balanceLoading, setBalanceLoading] = useState(false);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
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
        setSelectedAccount(accountsData[0].id);
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

  useEffect(() => {
    fetchDashboard();
    fetchAccounts();
  }, []);

  useEffect(() => {
    if (selectedAccount !== null) {
      fetchBalance(selectedAccount);
      fetchTransactions(selectedAccount);
    }
  }, [selectedAccount]);

  const handleAccountChange = async (event: any) => {
    const accountId = event.target.value;
    setSelectedAccount(accountId);
    setBalance(null);
    setBalanceLoading(true);

    const token = localStorage.getItem("token");

    try {
      const res = await fetch(`http://localhost:8000/user/account/${accountId}/balance`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      const data = await res.json();
      setBalance(data.balance);
    } catch (e) {
      console.error("Błąd ładowania salda:", e);
    } finally {
      setBalanceLoading(false);
    }
  };

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
          sx={{height: "100vh", bgcolor: "background.default", p: 2}}
      >
        <Paper
            elevation={4}
            sx={{
              display: "flex",
              flexDirection: "row",
              width: "100%",
              maxWidth: "1200px",
              height: "95vh",
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
              <Typography variant="h5" gutterBottom>
                Serwis transakcyjny
              </Typography>
              <Typography variant="subtitle1" gutterBottom>
                {data?.message ?? "Twoje konto"}
              </Typography>

              {/* Wybór konta */}
              <Box mt={3}>
                <Typography variant="body1" gutterBottom>
                  Wybierz konto:
                </Typography>
                <Select
                    fullWidth
                    value={selectedAccount}
                    onChange={(e) => setSelectedAccount(Number(e.target.value))}
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

              {/* Saldo */}
              <Box mt={4}>
                <Typography variant="h6">Saldo:</Typography>
                <Typography variant="body1" color="primary">
                  {balanceLoading
                      ? "Ładowanie..."
                      : balance !== null
                          ? `${balance.toFixed(2)} PLN`
                          : "Brak danych"}
                </Typography>
              </Box>
            </Box>

            <Button
                variant="contained"
                color="secondary"
                onClick={handleLogout}
                fullWidth
            >
              Wyloguj się
            </Button>
          </Box>

          {/* PRAWA STRONA */}
          <Box sx={{width: "70%", overflowY: "auto"}}>
            <Typography variant="h5" gutterBottom>
              Historia transakcji
            </Typography>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Data</TableCell>
                  <TableCell>Odbiorca</TableCell>
                  <TableCell>Kwota</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {transactions.length > 0 ? (
                    transactions.map((tx) => (
                        <TableRow key={tx.id}>
                          <TableCell>{tx.date}</TableCell>
                          <TableCell>{tx.receiver}</TableCell>
                          <TableCell>{tx.amount.toFixed(2)} PLN</TableCell>
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
        </Paper>
      </Box>
  );
}

export default UserDashboard;
