import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { api } from "./api.js";
import { useAuth } from "./auth-context.js";

export function HomePage() {
  const { user } = useAuth();
  return (
    <>
      <section className="hero">
        <div className="hero-content">
          <span className="badge">AI CREATIVE PLATFORM</span>
          <h1>Sáng tạo mọi thứ bằng AI</h1>
          <p>Tạo hình ảnh, video và website bằng trí tuệ nhân tạo.</p>
          <Link to={user ? "/dashboard" : "/register"} className="btn primary">Bắt đầu ngay</Link>
        </div>
      </section>
      <section className="features">
        <h2>Công cụ AI</h2>
        <div className="feature-grid">
          <article className="feature-card">🎨<h3>Tạo hình ảnh</h3><p>Tạo hình ảnh bằng AI.</p></article>
          <article className="feature-card">🎬<h3>Tạo video</h3><p>Tạo video bằng AI.</p></article>
          <article className="feature-card">🌐<h3>Tạo website</h3><p>AI tự động xây dựng website.</p></article>
        </div>
      </section>
    </>
  );
}

export function PricingPage() {
  const [selectedPlan, setSelectedPlan] = useState("creator");
  const plans = [
    {
      id: "free",
      name: "Dùng thử",
      description: "Bắt đầu khám phá các công cụ sáng tạo AI.",
      price: "0đ",
      period: "mãi mãi",
      features: ["10 credit khởi tạo khi đăng ký", "Truy cập công cụ tạo ảnh", "Trải nghiệm tạo video và website"],
      action: "Bắt đầu miễn phí",
    },
    {
      id: "creator",
      name: "Creator",
      description: "Dành cho nhà sáng tạo nội dung độc lập.",
      price: "199.000đ",
      period: "/ tháng",
      features: ["Bao gồm các công cụ AI sáng tạo", "Phù hợp cho dự án cá nhân", "Hỗ trợ qua email"],
      action: "Chọn Creator",
      featured: true,
    },
    {
      id: "studio",
      name: "Studio",
      description: "Dành cho nhóm nhỏ và nhu cầu chuyên nghiệp.",
      price: "499.000đ",
      period: "/ tháng",
      features: ["Bao gồm các công cụ AI sáng tạo", "Phù hợp cho quy trình của studio", "Liên hệ để tư vấn nhu cầu"],
      action: "Chọn Studio",
    },
  ];
  const selected = plans.find((plan) => plan.id === selectedPlan);

  return (
    <main className="pricing-page">
      <header className="pricing-heading">
        <span className="pricing-eyebrow">BẢNG GIÁ WEB AIAUTO</span>
        <h1>Chọn gói phù hợp với <span>cách bạn sáng tạo.</span></h1>
        <p>Bắt đầu miễn phí, nâng cấp khi bạn cần thêm không gian để phát triển ý tưởng.</p>
        <span className="pricing-sample-note">Giá mẫu tham khảo · Chưa phải giá bán chính thức</span>
      </header>

      <section className="pricing-grid" aria-label="Các gói dịch vụ">
        {plans.map((plan) => (
          <article
            key={plan.id}
            className={`pricing-card${plan.featured ? " is-featured" : ""}${selectedPlan === plan.id ? " is-selected" : ""}`}
          >
            {plan.featured && <span className="pricing-popular">PHỔ BIẾN</span>}
            <div className="pricing-plan-heading">
              <h2>{plan.name}</h2>
              <p>{plan.description}</p>
            </div>
            <div className="pricing-amount"><strong>{plan.price}</strong><span>{plan.period}</span></div>
            <button
              type="button"
              className={`pricing-select${selectedPlan === plan.id ? " is-selected" : ""}`}
              aria-pressed={selectedPlan === plan.id}
              onClick={() => setSelectedPlan(plan.id)}
            >
              {selectedPlan === plan.id ? "Đã chọn gói này" : plan.action}
            </button>
            <div className="pricing-divider" />
            <p className="pricing-includes">Gói này bao gồm:</p>
            <ul>
              {plan.features.map((feature) => <li key={feature}><span aria-hidden="true">✓</span>{feature}</li>)}
            </ul>
          </article>
        ))}
      </section>

      {selected && (
        <div className="pricing-next-step">
          <p>Đang chọn <strong>{selected.name}</strong></p>
          {selected.id === "studio"
            ? <Link className="pricing-continue" to="/contact">Trao đổi với chúng tôi <span aria-hidden="true">→</span></Link>
            : <Link className="pricing-continue" to="/register">Tiếp tục đăng ký <span aria-hidden="true">→</span></Link>}
        </div>
      )}
      <p className="pricing-disclaimer">Giá và quyền lợi trả phí trên trang này là nội dung mẫu để tham khảo. Thanh toán và giới hạn gói chưa được kết nối; vui lòng xác nhận thông tin trước khi công bố.</p>
    </main>
  );
}

export function AuthPage({ mode }) {
  const isRegister = mode === "register";
  const { user, config, login, register } = useAuth();
  const [values, setValues] = useState({ full_name: "", email: "", password: "", password_confirm: "", terms: false });
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    if (user) navigate(user.role === "admin" ? "/admin" : "/dashboard", { replace: true });
  }, [user, navigate]);

  function update(event) {
    const { name, value, checked, type } = event.target;
    setValues((current) => ({ ...current, [name]: type === "checkbox" ? checked : value }));
  }

  async function submit(event) {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      if (isRegister) {
        await register(values);
        navigate("/dashboard", { replace: true });
      } else {
        const signedIn = await login(values.email, values.password);
        navigate(location.state?.from || (signedIn.role === "admin" ? "/admin" : "/dashboard"), { replace: true });
      }
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className={isRegister ? "register-page" : "dashboard login-page"}>
      <div className={isRegister ? "register-card" : "login-card"}>
        <div className="login-brand-mark" aria-hidden="true">W</div>
        <span className="login-eyebrow">{isRegister ? "BẮT ĐẦU SÁNG TẠO" : "CHÀO MỪNG TRỞ LẠI"}</span>
        <h1>{isRegister ? "Tạo tài khoản" : "Đăng nhập"}</h1>
        <p className="login-intro">
          {isRegister ? "Đăng ký để trải nghiệm các công cụ sáng tạo bằng AI." : "Đăng nhập để tiếp tục sáng tạo cùng WebAiAuto."}
        </p>
        {error && <p className="login-error" role="alert">{error}</p>}

        {isRegister && (
          <div className="form-notice" role="status">
            {config.registration_enabled
              ? "Tài khoản mới được lưu vào PostgreSQL và nhận 10 credit khởi tạo."
              : "Hãy cấu hình DATABASE_URL và khởi động lại backend để bật đăng ký tài khoản."}
          </div>
        )}

        <form className={isRegister ? "register-form" : "login-form"} onSubmit={submit}>
          {isRegister && <>
            <label htmlFor="register-name">Họ và tên</label>
            <input id="register-name" name="full_name" value={values.full_name} onChange={update} type="text" placeholder="Nguyễn Văn A" autoComplete="name" maxLength={100} required disabled={!config.registration_enabled || submitting} />
          </>}
          <label htmlFor="auth-email">Email</label>
          <input id="auth-email" name="email" value={values.email} onChange={update} type="email" placeholder="you@example.com" autoComplete={isRegister ? "email" : "username"} maxLength={255} required disabled={isRegister && (!config.registration_enabled || submitting)} />
          <label htmlFor="auth-password">Mật khẩu</label>
          <input id="auth-password" name="password" value={values.password} onChange={update} type="password" placeholder={isRegister ? "Tối thiểu 8 ký tự" : "Nhập mật khẩu"} autoComplete={isRegister ? "new-password" : "current-password"} minLength={isRegister ? 8 : undefined} maxLength={128} required disabled={isRegister && (!config.registration_enabled || submitting)} />
          {isRegister && <>
            <label htmlFor="auth-password-confirm">Xác nhận mật khẩu</label>
            <input id="auth-password-confirm" name="password_confirm" value={values.password_confirm} onChange={update} type="password" placeholder="Nhập lại mật khẩu" autoComplete="new-password" minLength={8} maxLength={128} required disabled={!config.registration_enabled || submitting} />
            <label className="register-terms">
              <input name="terms" type="checkbox" checked={values.terms} onChange={update} required disabled={!config.registration_enabled || submitting} />
              <span>Tôi đồng ý với điều khoản sử dụng và chính sách bảo mật.</span>
            </label>
          </>}
          <button className="btn primary login-submit" type="submit" disabled={submitting || (isRegister && !config.registration_enabled)}>
            {submitting ? "Đang xử lý..." : isRegister ? "Tạo tài khoản" : "Đăng nhập"} <span aria-hidden="true">→</span>
          </button>
        </form>

        <p className="register-login-link">
          {isRegister ? "Đã có tài khoản? " : "Chưa có tài khoản? "}
          <Link to={isRegister ? "/login" : "/register"}>{isRegister ? "Đăng nhập" : "Đăng ký"}</Link>
        </p>

        {!isRegister && config.show_demo_accounts && (
          <aside className="demo-accounts">
            <strong>Tài khoản thử nghiệm</strong>
            <p>Dùng các tài khoản này khi chạy ứng dụng local.</p>
            <div className="demo-account"><span className="demo-role demo-role-admin">ADMIN</span><code>admin@webai.test</code><code>DemoAdmin2026!</code></div>
            <div className="demo-account"><span className="demo-role">USER</span><code>user@webai.test</code><code>DemoUser2026!</code></div>
          </aside>
        )}
      </div>
    </section>
  );
}

export function Dashboard() {
  const tools = [
    { href: "/image", icon: "🎨", title: "Tạo hình ảnh", description: "Tạo hình ảnh từ prompt." },
    { href: "/video", icon: "🎬", title: "Tạo video", description: "Tạo video bằng AI." },
    { href: "/website", icon: "🌐", title: "Tạo website", description: "Tự động xây dựng website." },
  ];
  return (
    <section className="dashboard">
      <h1>Dashboard</h1>
      <p>Chào mừng bạn đến với WebAiAuto.</p>
      <div className="tool-grid">
        {tools.map((tool) => <Link key={tool.href} to={tool.href} className="tool-card">
          <div className="tool-icon">{tool.icon}</div><h2>{tool.title}</h2><p>{tool.description}</p>
        </Link>)}
      </div>
    </section>
  );
}

export function AdminDashboard() {
  const [userCount, setUserCount] = useState(null);
  const [error, setError] = useState("");
  useEffect(() => {
    api("/api/admin/summary").then((summary) => setUserCount(summary.user_count)).catch((requestError) => setError(requestError.message));
  }, []);

  return (
    <section className="dashboard admin-page">
      <div className="admin-page-heading">
        <div><span className="admin-eyebrow">ADMINISTRATION</span><h1>Khu vực quản trị</h1><p>Quản lý và theo dõi hệ thống tại đây.</p></div>
        <span className="admin-status"><span /> Đang hoạt động</span>
      </div>
      {error && <p className="login-error" role="alert">{error}</p>}
      <div className="tool-grid admin-grid">
        <Link to="/admin/users" className="tool-card">
          <div className="admin-card-icon" aria-hidden="true">♙</div>
          <span className="admin-card-label">TÀI KHOẢN</span><h2>Người dùng</h2>
          <p>Quản lý danh sách và vai trò người dùng.</p>
          <strong className="admin-card-metric">{userCount ?? "…"} <span>tài khoản</span></strong>
          <span className="admin-card-link">Xem danh sách <span aria-hidden="true">→</span></span>
        </Link>
      </div>
    </section>
  );
}

export function AdminUsers() {
  const [users, setUsers] = useState(null);
  const [error, setError] = useState("");
  useEffect(() => {
    api("/api/admin/users").then(setUsers).catch((requestError) => setError(requestError.message));
  }, []);

  return (
    <section className="dashboard admin-page">
      <div className="admin-page-heading">
        <div><span className="admin-eyebrow">ADMINISTRATION / USERS</span><h1>Quản lý người dùng</h1><p>Xem tài khoản và vai trò trong hệ thống.</p></div>
        <Link className="admin-back-link" to="/admin"><span aria-hidden="true">←</span> Trang quản trị</Link>
      </div>
      {error && <p className="login-error" role="alert">{error}</p>}
      {users === null && !error ? <p>Đang tải danh sách người dùng...</p> : (
        <div className="tool-grid admin-users-grid">
          {users?.map((user) => <article key={user.id} className="tool-card admin-user-card">
            <div className="admin-user-avatar" aria-hidden="true">{user.full_name?.slice(0, 1) || user.email.slice(0, 1)}</div>
            <div className="admin-user-info"><h2>{user.full_name || "Chưa cập nhật"}</h2><p>{user.email}</p></div>
            <span className={`admin-role-badge${user.role === "admin" ? " is-admin" : ""}`}>{user.role}</span>
          </article>)}
          {users?.length === 0 && <p>Chưa có người dùng nào.</p>}
        </div>
      )}
    </section>
  );
}

export function ContactPage() {
  const [formState, setFormState] = useState({ type: "", message: "" });
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    if (isSubmitting) return;

    const form = event.currentTarget;
    setIsSubmitting(true);
    setFormState({ type: "", message: "" });
    try {
      await api("/api/contact", {
        method: "POST",
        body: JSON.stringify(Object.fromEntries(new FormData(form).entries())),
      });
      form.reset();
      setFormState({ type: "success", message: "Tin nhắn đã được gửi. Cảm ơn bạn đã liên hệ!" });
    } catch (error) {
      setFormState({ type: "error", message: error.message });
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="contact-page">
      <div className="contact-heading">
        <span className="contact-eyebrow">KẾT NỐI VỚI CHÚNG TÔI</span>
        <h1>Bạn cần hỗ trợ?</h1>
        <p>Gửi lời nhắn cho đội ngũ WebAiAuto. Chúng tôi luôn sẵn sàng lắng nghe ý kiến của bạn.</p>
      </div>
      <div className="contact-layout">
        <aside className="contact-aside">
          <div className="contact-aside-icon" aria-hidden="true">✦</div><h2>Cùng tạo nên điều tuyệt vời</h2>
          <p>Chia sẻ câu hỏi, phản hồi hoặc ý tưởng của bạn với chúng tôi.</p>
          <div className="contact-detail"><span className="contact-detail-icon">@</span><div><strong>Email hỗ trợ</strong><span>Gửi lời nhắn qua biểu mẫu bên cạnh</span></div></div>
          <div className="contact-detail"><span className="contact-detail-icon">◷</span><div><strong>Phản hồi</strong><span>Chúng tôi sẽ liên hệ qua email bạn cung cấp</span></div></div>
          <div className="contact-decoration" aria-hidden="true" />
        </aside>
        <div className="contact-form-panel">
          <h2>Gửi lời nhắn</h2><p className="contact-form-intro">Điền thông tin bên dưới để liên hệ với chúng tôi.</p>
          {formState.message && (
            <div
              className={`form-notice${formState.type === "error" ? " is-error" : ""}`}
              role={formState.type === "error" ? "alert" : "status"}
              aria-live="polite"
            >
              {formState.message}
            </div>
          )}
          <form className="contact-form" onSubmit={handleSubmit} aria-busy={isSubmitting}>
            <div className="contact-form-row">
              <div className="contact-field"><label htmlFor="contact-name">Họ và tên</label><input id="contact-name" name="name" type="text" placeholder="Nguyễn Văn A" autoComplete="name" maxLength="100" required /></div>
              <div className="contact-field"><label htmlFor="contact-email">Email</label><input id="contact-email" name="email" type="email" placeholder="you@example.com" autoComplete="email" maxLength="255" required /></div>
            </div>
            <div className="contact-field"><label htmlFor="contact-subject">Chủ đề</label><input id="contact-subject" name="subject" type="text" placeholder="Bạn muốn trao đổi về điều gì?" maxLength="200" required /></div>
            <div className="contact-field"><label htmlFor="contact-message">Nội dung</label><textarea id="contact-message" name="message" rows="5" placeholder="Viết lời nhắn của bạn..." maxLength="5000" required /></div>
            <button className="btn primary contact-submit" type="submit" disabled={isSubmitting}>{isSubmitting ? "Đang gửi..." : "Gửi tin nhắn"} <span aria-hidden="true">→</span></button>
          </form>
        </div>
      </div>
    </section>
  );
}
