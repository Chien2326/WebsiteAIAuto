import { useEffect, useState } from "react";
import { Link, Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import { SESSION_EXPIRED_EVENT, api } from "./api.js";
import { AuthContext, useAuth } from "./auth-context.js";
import {
  AdminDashboard,
  AdminUsers,
  AuthPage,
  ContactPage,
  Dashboard,
  HomePage,
  PricingPage,
} from "./pages.jsx";
import { ImageGenerator, VideoGenerator, WebsiteBuilder } from "./generators.jsx";

function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [sessionError, setSessionError] = useState("");
  const [config, setConfig] = useState({
    registration_enabled: false,
    show_demo_accounts: false,
    credit_prices: null,
  });

  useEffect(() => {
    const clearUser = () => setUser(null);
    window.addEventListener(SESSION_EXPIRED_EVENT, clearUser);
    return () => window.removeEventListener(SESSION_EXPIRED_EVENT, clearUser);
  }, []);

  useEffect(() => {
    let active = true;
    Promise.all([
      api("/api/auth/me").catch((error) => {
        if (error.status === 401) return null;
        throw error;
      }),
      api("/api/config"),
    ])
      .then(([session, publicConfig]) => {
        if (!active) return;
        setUser(session);
        setConfig(publicConfig);
      })
      .catch(() => {
        if (active) setSessionError("Không thể kết nối máy chủ. Hãy kiểm tra backend rồi tải lại trang.");
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  const login = async (email, password) => {
    const signedInUser = await api("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    setUser(signedInUser);
    return signedInUser;
  };

  const register = async (payload) => {
    const newUser = await api("/api/auth/register", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    setUser(newUser);
    return newUser;
  };

  const setCredits = (balance) => {
    if (typeof balance !== "number") return;
    setUser((current) => (current ? { ...current, credits_balance: balance } : current));
  };

  const logout = async () => {
    await api("/api/auth/logout", { method: "POST" });
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, setUser, setCredits, loading, sessionError, config, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

function Layout({ children }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  async function handleLogout() {
    try {
      await logout();
      navigate("/");
    } catch (error) {
      window.alert(error.message);
    }
  }

  const active = (path) => location.pathname === path ? "image-nav-link" : undefined;

  return (
    <>
      <header className="header">
        <Link className="logo" to="/">WebAiAuto</Link>
        <nav className="navbar" aria-label="Điều hướng chính">
          <Link to="/">Trang chủ</Link>
          <Link className={active("/pricing")} to="/pricing">Bảng giá</Link>
          {user && <Link to="/dashboard">Dashboard</Link>}
          {user && <Link className={active("/image")} to="/image">Tạo ảnh</Link>}
          {user && <Link className={active("/video")} to="/video">Tạo video</Link>}
          {user && <Link className={active("/website")} to="/website">Tạo website</Link>}
          <Link className={active("/contact")} to="/contact">Liên hệ</Link>
          {user?.role === "admin" && <Link to="/admin">Quản trị</Link>}
          {user ? (
            <>
              <span className="nav-user">{user.full_name}</span>
              {typeof user.credits_balance === "number" && (
                <span className="nav-credits" title="Số credit còn lại">◈ {user.credits_balance} credit</span>
              )}
              <button className="nav-logout" type="button" onClick={handleLogout}>Đăng xuất</button>
            </>
          ) : (
            <>
              <Link to="/login">Đăng nhập</Link>
              <Link className="nav-register" to="/register">Đăng ký</Link>
            </>
          )}
        </nav>
      </header>
      {children}
      <footer className="footer">
        <div className="footer-content">
          <div><strong>WebAiAuto</strong><p>Nền tảng sáng tạo nội dung bằng AI.</p></div>
          <div><p>© 2026 WebAiAuto</p></div>
        </div>
      </footer>
    </>
  );
}

function RequireUser({ children, admin = false }) {
  const { user, loading } = useAuth();
  const location = useLocation();
  if (loading) return <main className="dashboard"><p>Đang tải...</p></main>;
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  if (admin && user.role !== "admin") return <Navigate to="/dashboard" replace />;
  return children;
}

function AppRoutes() {
  const { loading, sessionError } = useAuth();
  if (loading) {
    return <main className="dashboard"><p>Đang kết nối WebAiAuto...</p></main>;
  }
  return (
    <Layout>
      {sessionError && <p className="login-error" role="alert">{sessionError}</p>}
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/pricing" element={<PricingPage />} />
        <Route path="/login" element={<AuthPage mode="login" />} />
        <Route path="/register" element={<AuthPage mode="register" />} />
        <Route path="/contact" element={<ContactPage />} />
        <Route path="/dashboard" element={<RequireUser><Dashboard /></RequireUser>} />
        <Route path="/image" element={<RequireUser><ImageGenerator /></RequireUser>} />
        <Route path="/video" element={<RequireUser><VideoGenerator /></RequireUser>} />
        <Route path="/website" element={<RequireUser><WebsiteBuilder /></RequireUser>} />
        <Route path="/admin" element={<RequireUser admin><AdminDashboard /></RequireUser>} />
        <Route path="/admin/users" element={<RequireUser admin><AdminUsers /></RequireUser>} />
        <Route path="*" element={<main className="dashboard"><h1>Không tìm thấy trang</h1><Link to="/">Về trang chủ</Link></main>} />
      </Routes>
    </Layout>
  );
}

export default function App() {
  return <AuthProvider><AppRoutes /></AuthProvider>;
}
