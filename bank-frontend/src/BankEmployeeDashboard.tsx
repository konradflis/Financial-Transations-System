import {ChangeEvent, useEffect, useState} from "react";
import { useNavigate } from "react-router-dom";
import {
  Box, Typography, Button, Paper, Table, TableHead, TableRow, TableCell,
  TableBody, Modal, TextField, FormControlLabel, Checkbox
} from "@mui/material";
import {SelectChangeEvent} from "@mui/material/Select";
import TopBar from './TopBar'
import Footer from './Footer'
import logo from './assets/JKM_Bank_Logo.png'

interface DashboardData {
  message: string;
}

interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  username: number;
}

interface Account {
  id: number;
  balance: number;
  account_number: string;
  status: string;
}

const BankEmployeeDashboard = () => {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [users, setUsers] = useState<User[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const navigate = useNavigate();
  const [isCreateUserOpen, setisCreateUserOpen] = useState(false);
  const [isCreateAccountOpen, setisCreateAccountOpen] = useState(false);
  const [firstName, setFirstName] = useState("")
  const [lastName, setLastName] = useState("")
  const [email, setEmail] = useState("")
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [userId, setUserId] = useState("")
  const [addCard, setAddCard] = useState(false);
  const [pinCode, setPinCode] = useState("");

  const [filters, setFilters] = useState({
    username: '',
    email: ''
  });

  const handleFilterChange = (
    e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement> | SelectChangeEvent<string>) => {
    const { name, value } = e.target;

    setFilters((prevFilters) => ({
      ...prevFilters,
      [name]: value,
    }));
  };

  const filteredUsers = users.filter((usr) => {
    return (
      (filters.username ? usr.username === Number(filters.username) : true) &&
      (filters.email ? usr.email.includes(filters.email) : true)
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
      const response = await fetch("http://localhost:8000/bank_employee/dashboard", {
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

  const fetchUsers = async (username: string, email: string) => {
    const token = localStorage.getItem("token");
    const queryParams = new URLSearchParams({
      username: username,
      email: email,
    });

    try {
      const response = await fetch(
        `http://localhost:8000/bank_employee/user-data?${queryParams.toString()}`,
        {
          method: "GET",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (response.ok) {
        const res = await response.json();
        setUsers([res.user]);
        setAccounts(res.accounts);
      } else {
        setUsers([]);
        setAccounts([]);
      }
    } catch (err) {
      console.error("Błąd pobierania użytkownika:", err);
      setUsers([]);
      setAccounts([]);
    }
  };


  const handleUserCreation = async () => {
    const token = localStorage.getItem("token");

    if (!token || !firstName || !lastName || !email || !username || !password) {
      alert("Uzupełnij wszystkie dane użytkownika.");
      return;
    }

    try {
      const response = await fetch("http://localhost:8000/bank_employee/add-user", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          first_name: firstName,
          last_name: lastName,
          email: email,
          username: parseInt(username),
          password: password,
          role: "user",
        }),
      });

      if (response.ok) {
        alert("Użytkownik utworzony!");
        setFirstName("");
        setLastName("");
        setEmail("");
        setUsername("");
        setPassword("");
      } else {
        const errorData = await response.json();
        alert(`Błąd: ${errorData.detail || "Nieznany błąd"}`);
      }
    } catch (err) {
      console.error("Błąd tworzenia użytkownika:", err);
      alert("Wystąpił błąd podczas tworzenia użytkownika.");
    }
  };

  const handleAccountCreation = async () => {
    const token = localStorage.getItem("token");

    if (!token || !userId) {
      alert("Brak danych do utworzenia konta.");
      return;
    }

    try {
      const response = await fetch("http://localhost:8000/bank_employee/add-account", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          user_id: parseInt(userId),
          initial_balance: 0, // lub inna wartość początkowa
        }),
      });

      if (response.ok) {
        const data = await response.json();
        const accountId = data.account_id;

        alert("Konto zostało utworzone!");

        // Jeśli zaznaczono checkbox "Dodaj kartę"
        if (addCard) {
          await handleCardCreation(accountId);
        }

        // Reset danych formularza
        setUserId("");
        setPinCode("");
        setAddCard(false);
      } else {
        const errorData = await response.json();
        alert(`Błąd: ${errorData.detail || "Nieznany błąd"}`);
      }
    } catch (err) {
      console.error("Błąd tworzenia konta:", err);
      alert("Wystąpił błąd podczas tworzenia konta.");
    }
  };

  const handleCardCreation = async (accountId: number) => {
    const token = localStorage.getItem("token");

    if (!token || !pinCode || !accountId) {
      alert("Brak danych do utworzenia karty.");
      return;
    }

    if (!/^\d{4}$/.test(pinCode)) {
      alert("PIN musi składać się z dokładnie 4 cyfr.");
      return;
    }

    try {
      const response = await fetch("http://localhost:8000/bank_employee/add-card", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          account_id: accountId,
          pin_code: pinCode,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        alert("Karta została dodana!");
        setPinCode("");
        setAddCard(false);
      } else {
        const errorData = await response.json();
        alert(`Błąd przy dodawaniu karty: ${errorData.detail || "Nieznany błąd"}`);
      }
    } catch (err) {
      console.error("Błąd tworzenia karty:", err);
      alert("Wystąpił błąd podczas dodawania karty.");
    }
  };

  useEffect(() => {
    if (filters.username || filters.email) {
      fetchUsers(filters.username, filters.email);
    }
  }, [filters]);

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
                    Panel pracownika
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
                  onClick={() => setisCreateUserOpen(true)}
                >
                  Załóż konto użytkownika
                </Button>
                <Button
                  sx={{ mt: 2 }}
                  variant="contained"
                  color="primary"
                  fullWidth
                  onClick={() => setisCreateAccountOpen(true)}
                >
                  Utwórz konto bankowe
                </Button>
              </Box>
            </Box>
          </Box>

          {/* PRAWA STRONA */}
          <Box sx={{width: "70%",}}>
            <Typography variant="h5" gutterBottom fontWeight="bold">
              Dane użytkownika
            </Typography>
            <Typography
            variant="body2"
            color="text.secondary"
            textAlign="left"
            sx={{ mb: 2 }}
          >
          Wprowadź ID użytkownika oraz jego adres e-mail, aby zobaczyć szczegółowe dane dotyczące kont.
          </Typography>
            <Box sx={{ display: "flex", gap: 2, mb: 2 }}>
            <TextField
              label="ID użytkownika"
              variant="outlined"
              size="small"
              name="username"
              value={filters.username}
              onChange={handleFilterChange}
              fullWidth
            />
            <TextField
              label="E-mail"
              variant="outlined"
              size="small"
              name="email"
              value={filters.email}
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
                  <TableCell sx={{ fontWeight: 'bold' }}>ID</TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>Imię</TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>Nazwisko</TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>E-mail</TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>Username</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredUsers.length > 0 ? (
                    filteredUsers.map((usr) => (
                        <TableRow key={usr.id}>
                          <TableCell>{usr.id}</TableCell>
                          <TableCell>{usr.first_name}</TableCell>
                          <TableCell>{usr.last_name}</TableCell>
                          <TableCell>{usr.email}</TableCell>
                          <TableCell>{usr.username}</TableCell>
                        </TableRow>
                    ))
                ) : (
                    <TableRow>
                      <TableCell colSpan={5} align="center">
                        Żaden użytkownik nie został wybrany
                      </TableCell>
                    </TableRow>
                )}
              </TableBody>
            </Table>
          </Box>
          <Typography variant="h5" fontWeight="bold" sx={{ mt: 4 }}>
            Konta użytkownika
          </Typography>
          <Typography
            variant="body2"
            color="text.secondary"
            textAlign="left"
            sx={{ mb: 2 }}
          >
          Konta będą widoczne, jeśli powyżej zostaną wprowadzone poprawne dane dotyczące użytkownika.
          </Typography>
          <Box sx={{ maxHeight: "300px", overflowY: "auto" }}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell sx={{ fontWeight: 'bold' }}>ID Konta</TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>Numer Konta</TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>Status</TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>Saldo</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {accounts.length > 0 ? (
                  accounts.map((account) => (
                    <TableRow key={account.id}>
                      <TableCell>{account.id}</TableCell>
                      <TableCell>{account.account_number}</TableCell>
                      <TableCell>{account.status}</TableCell>
                      <TableCell>{account.balance}</TableCell>
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={4} align="center">
                      Żaden użytkownik nie został wybrany
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </Box>
          </Box>
        </Paper>

        <Modal
          open={isCreateUserOpen}
          onClose={() => setisCreateUserOpen(false)}
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
              Nowe konto użytkownika
            </Typography>
            <TextField
              fullWidth
              label="Imię"
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
              sx={{ mb: 2 }}
            />
            <TextField
              fullWidth
              label="Nazwisko"
              value={lastName}
              onChange={(e) => setLastName(e.target.value)}
              sx={{ mb: 2 }}
            />
            <TextField
              fullWidth
              label="E-mail"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              sx={{ mb: 2 }}
            />
            <TextField
              fullWidth
              label="Username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              sx={{ mb: 2 }}
            />
            <TextField
              fullWidth
              label="Hasło"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              sx={{ mb: 2 }}
            />
            <Box display="flex" justifyContent="space-between">
              <Button variant="outlined" onClick={() => setisCreateUserOpen(false)}>
                Anuluj
              </Button>
              <Button
                variant="contained"
                color="primary"
                onClick={() => handleUserCreation()}
                disabled={!firstName || !lastName || !email || !username || !password}
              >
                Zatwierdź
              </Button>
            </Box>
          </Box>
        </Modal>

        <Modal
          open={isCreateAccountOpen}
          onClose={() => setisCreateAccountOpen(false)}
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
              Nowe konto bankowe
            </Typography>

            <TextField
              fullWidth
              label="ID użytkownika"
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
              sx={{ mb: 2 }}
            />

            <FormControlLabel
              control={
                <Checkbox
                  checked={addCard}
                  onChange={(e) => setAddCard(e.target.checked)}
                />
              }
              label="Dodaj kartę"
              sx={{ mb: 2 }}
            />

            <TextField
              fullWidth
              label="Kod PIN (4 cyfry)"
              value={pinCode}
              onChange={(e) => setPinCode(e.target.value)}
              disabled={!addCard}
              inputProps={{ maxLength: 4 }}
              sx={{ mb: 2 }}
            />

            <Box display="flex" justifyContent="space-between">
              <Button variant="outlined" onClick={() => setisCreateAccountOpen(false)}>
                Anuluj
              </Button>
              <Button
                variant="contained"
                color="primary"
                onClick={() => {
                  handleAccountCreation();
                }}
                disabled={!userId}
              >
                Zatwierdź
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

export default BankEmployeeDashboard;
