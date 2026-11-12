import { useEffect, useState } from "react";
import { api } from "./api.js";
import { useAuth } from "./auth-context.js";

const imageIdeas = [
  ["Bình minh trên núi", "Phong cảnh · Điện ảnh", "Ngôi nhà nhỏ bên hồ trên núi lúc bình minh, sương mờ, ánh sáng ấm áp", "inspiration-dawn"],
  ["Khu vườn mộng mơ", "Thiên nhiên · Minh họa", "Khu vườn hoa mộng mơ với những đóa hoa khổng lồ, ánh nắng xuyên qua tán lá, minh họa nghệ thuật", "inspiration-bloom"],
  ["Du hành ngân hà", "Vũ trụ · 3D", "Phi hành gia nhỏ đứng trên hành tinh tím nhìn ngắm dải ngân hà, nghệ thuật 3D siêu thực", "inspiration-orbit"],
  ["Miền biển dịu êm", "Du lịch · Tả thực", "Ngọn hải đăng trên vách đá bên bờ biển xanh, nắng chiều rực rỡ, phong cách ảnh phim", "inspiration-coast"],
];

const videoIdeas = [
  ["Phố cổ sau cơn mưa", "Đô thị · Chuyển động chậm", "Máy quay lướt qua con phố cổ sau cơn mưa, ánh đèn vàng phản chiếu trên mặt đường, chuyển động chậm, điện ảnh", "inspiration-city"],
  ["Khu rừng trong sương", "Thiên nhiên · Bay lượn", "Máy quay bay xuyên qua khu rừng xanh trong sương sớm, tia nắng xuyên qua tán cây, cảm giác kỳ ảo", "inspiration-forest"],
  ["Hoàng hôn bên biển", "Phong cảnh · Điện ảnh", "Sóng biển vỗ nhẹ vào bờ lúc hoàng hôn, máy quay tiến dần về phía mặt trời, tông màu điện ảnh", "inspiration-coast"],
  ["Trôi giữa ngân hà", "Vũ trụ · 3D", "Phi thuyền nhỏ bay chậm qua tinh vân đầy màu sắc, máy quay theo sau, không gian 3D kỳ vĩ", "inspiration-space"],
];

const websitePresets = {
  coffee: {
    brand: "MỘC STUDIO", icon: "✳", kicker: "CÀ PHÊ · TỪ VƯỜN ĐẾN TÁCH",
    title: "Một chút bình yên,<br>trong từng ngụm cà phê.",
    description: "Hạt cà phê tuyển chọn, rang thủ công mỗi ngày. Dành thời gian cho những điều thật sự đáng nhớ.",
    navCta: "Liên hệ", heroCta: "Khám phá câu chuyện",
    features: ["Nguồn gốc rõ ràng", "Rang thủ công", "Tận tâm mỗi ngày"],
  },
  portfolio: {
    brand: "LINH NGUYỄN", icon: "✳", kicker: "THIẾT KẾ · NGHỆ THUẬT · KỂ CHUYỆN",
    title: "Tạo nên những điều<br>đáng để nhớ.",
    description: "Tôi là nhà thiết kế độc lập, biến những ý tưởng táo bạo thành trải nghiệm thương hiệu có ý nghĩa.",
    navCta: "Liên hệ", heroCta: "Xem dự án",
    features: ["Thiết kế nhận diện", "Trải nghiệm số", "Kể chuyện thương hiệu"],
  },
  agency: {
    brand: "NORTH DIGITAL", icon: "◈", kicker: "CHIẾN LƯỢC · SÁNG TẠO · TĂNG TRƯỞNG",
    title: "Đưa thương hiệu<br>tiến xa hơn.",
    description: "Chúng tôi đồng hành cùng doanh nghiệp tạo nên những trải nghiệm số khác biệt và bền vững.",
    navCta: "Bắt đầu", heroCta: "Khám phá dịch vụ",
    features: ["Chiến lược rõ ràng", "Thiết kế chỉn chu", "Đo lường hiệu quả"],
  },
  restaurant: {
    brand: "BẾP NHÀ", icon: "♨", kicker: "MÓN NGON · NGUYÊN LIỆU TƯƠI · VỊ NHÀ",
    title: "Hương vị thân quen,<br>cho ngày thêm vui.",
    description: "Món ăn được nấu từ nguyên liệu địa phương tươi ngon, trao gửi trọn vẹn sự ấm áp như ở nhà.",
    navCta: "Đặt bàn", heroCta: "Xem thực đơn",
    features: ["Nguyên liệu tươi", "Nấu mỗi ngày", "Hương vị quê nhà"],
  },
};

const englishPresets = {
  coffee: ["COFFEE · FROM FARM TO CUP", "A little moment of calm,<br>in every cup.", "Carefully sourced beans, freshly roasted every day. Make time for the things that matter.", "Contact", "Discover our story", ["Thoughtful sourcing", "Small-batch roasted", "Made with care"]],
  portfolio: ["DESIGN · ART · STORYTELLING", "Making things<br>worth remembering.", "I am an independent designer turning bold ideas into meaningful brand experiences.", "Contact", "View projects", ["Brand identity", "Digital experiences", "Brand storytelling"]],
  agency: ["STRATEGY · CREATIVE · GROWTH", "Move your brand<br>forward.", "We help businesses build distinctive, enduring digital experiences.", "Get started", "Explore services", ["Clear strategy", "Thoughtful design", "Measurable impact"]],
  restaurant: ["FRESH FOOD · LOCAL INGREDIENTS · HOMESTYLE", "A familiar flavor,<br>for brighter days.", "Made fresh each day with local ingredients and a little extra warmth.", "Book a table", "View the menu", ["Fresh ingredients", "Cooked daily", "A taste of home"]],
};

const palettes = {
  sage: ["#f5f1e8", "#263c33", "#65756b", "#465e4c", "#fffdf4", "#c1a584", "#889477", "#435948"],
  blue: ["#f1f4f8", "#29394f", "#67788c", "#3e5f8d", "#f8faff", "#a9bdd0", "#758ba8", "#405674"],
  rose: ["#f8f0ee", "#503b40", "#876a70", "#8e565e", "#fff9f4", "#d6aaa0", "#b27b7e", "#79535e"],
  amber: ["#f8f1e5", "#4d3827", "#88725b", "#986431", "#fffaf1", "#d9b473", "#a87949", "#68492f"],
};

function useToast() {
  const [message, setMessage] = useState("");
  useEffect(() => {
    if (!message) return undefined;
    const timer = window.setTimeout(() => setMessage(""), 3200);
    return () => window.clearTimeout(timer);
  }, [message]);
  return [message, setMessage];
}

function PromptChips({ items, value, onChange, className, chipClass = "prompt-chip" }) {
  return <div className={className}>
    {items.map(([label, addition]) => <button key={addition} type="button" className={chipClass} onClick={() => onChange(value.trim() ? `${value.trim()}, ${addition}` : addition)}>{label}</button>)}
  </div>;
}

function InspirationCards({ items, onSelect, video = false }) {
  return <div className={video ? "video-inspiration-grid" : "inspiration-grid"}>
    {items.map(([title, meta, prompt, art]) => <button key={title} className={video ? `video-inspiration-card ${art}` : `inspiration-card ${art}`} type="button" data-inspiration={prompt} onClick={() => onSelect(prompt)}>
      <span className={video ? "video-inspiration-art" : "inspiration-art"} aria-hidden="true"><i /><b /><em /></span>
      <span className={video ? "video-inspiration-meta" : "inspiration-meta"}><strong>{title}</strong><span>{meta}</span></span>
      <span className="inspiration-arrow" aria-hidden="true">↗</span>
    </button>)}
  </div>;
}

export function ImageGenerator() {
  const [prompt, setPrompt] = useState("");
  const [style, setStyle] = useState("Điện ảnh");
  const [ratio, setRatio] = useState("1:1");
  const [quantity, setQuantity] = useState("1");
  const [generatedImages, setGeneratedImages] = useState([]);
  const [generating, setGenerating] = useState(false);
  const [generationError, setGenerationError] = useState("");
  const [toast, setToast] = useToast();
  const { config, setCredits } = useAuth();
  const imageCost = (config.credit_prices?.image_per_image ?? 1) * Number(quantity);
  const styles = [["Điện ảnh", "swatch-cinema"], ["Minh họa", "swatch-illustration"], ["Tả thực", "swatch-realistic"], ["3D", "swatch-3d"]];
  const ratios = [["1:1", "ratio-square"], ["16:9", "ratio-landscape"], ["9:16", "ratio-portrait"]];

  async function submit(event) {
    event.preventDefault();
    if (!prompt.trim() || generating) return;

    setGenerating(true);
    setGenerationError("");
    setGeneratedImages([]);
    try {
      const result = await api("/api/image/generate", {
        method: "POST",
        body: JSON.stringify({
          prompt: prompt.trim(),
          style,
          aspect_ratio: ratio,
          quantity: Number(quantity),
        }),
      });
      setGeneratedImages(result.images);
      setCredits(result.credits_balance);
      setToast(result.images.length < result.requested
        ? `Đã tạo ${result.images.length}/${result.requested} ảnh. Credit cho ảnh lỗi đã được hoàn lại.`
        : `Tạo ảnh thành công (−${result.cost_credits} credit). Bạn có thể tải ảnh về thiết bị.`);
    } catch (error) {
      setGenerationError(error.message);
    } finally {
      setGenerating(false);
    }
  }

  return <section className="image-page">
    <div className="image-heading"><div><div className="image-eyebrow"><span className="eyebrow-dot" /> STUDIO SÁNG TẠO AI</div><h1>Biến ý tưởng thành <span>hình ảnh.</span></h1><p>Mô tả điều bạn tưởng tượng. Để AI giúp bạn tạo nên điều khác biệt.</p></div><a className="image-history" href="#inspiration"><span aria-hidden="true">◷</span> Ý tưởng nổi bật</a></div>
    <div className="generator-layout">
      <form className="generator-panel" id="image-generator-form" onSubmit={submit}>
        <div className="panel-title"><div className="panel-icon" aria-hidden="true">✳</div><div><h2>Mô tả hình ảnh</h2><p>Hãy viết càng cụ thể, kết quả càng đúng ý.</p></div></div>
        <label className="field-label" htmlFor="image-prompt">Ý tưởng của bạn</label>
        <div className="prompt-wrap"><textarea id="image-prompt" name="prompt" maxLength={500} placeholder="Ví dụ: Một ngôi nhà nhỏ nằm giữa cánh đồng hoa dưới bầu trời đầy sao, phong cách minh họa điện ảnh..." required value={prompt} onChange={(event) => setPrompt(event.target.value)} /><span className="prompt-count">{prompt.length} / 500</span></div>
        <PromptChips items={[["☀ Ánh hoàng hôn", "ánh sáng hoàng hôn"], ["▧ Điện ảnh", "phong cách điện ảnh"], ["✧ Tinh xảo", "chi tiết tinh xảo"]]} value={prompt} onChange={setPrompt} className="suggestion-row" />
        <div className="form-divider" />
        <div className="field-heading"><span className="field-label">Phong cách</span><span className="field-hint">Chọn một phong cách</span></div>
        <div className="style-options" role="group" aria-label="Chọn phong cách hình ảnh">{styles.map(([label, swatch]) => <button key={label} type="button" className={`style-option${style === label ? " is-selected" : ""}`} aria-pressed={style === label} onClick={() => setStyle(label)}><span className={`style-swatch ${swatch}`} aria-hidden="true" /><span>{label}</span></button>)}</div>
        <div className="form-divider" />
        <div className="settings-grid">
          <div><div className="field-heading"><span className="field-label">Tỷ lệ khung hình</span></div><div className="ratio-options" role="group" aria-label="Chọn tỷ lệ khung hình">{ratios.map(([label, icon]) => <button key={label} type="button" className={`ratio-option${ratio === label ? " is-selected" : ""}`} aria-pressed={ratio === label} onClick={() => setRatio(label)}><span className={icon} /> {label}</button>)}</div></div>
          <label className="quantity-field" htmlFor="image-quantity"><span className="field-label">Số lượng</span><select id="image-quantity" value={quantity} onChange={(event) => setQuantity(event.target.value)}>{[1, 2, 3, 4].map((number) => <option key={number} value={number}>{number} ảnh</option>)}</select></label>
        </div>
        <button type="submit" className="generate-button" disabled={generating}><span aria-hidden="true">✦</span> {generating ? "Đang tạo ảnh..." : <>Tạo hình ảnh <span className="generation-cost">· {imageCost} credit</span></>} <span className="button-arrow" aria-hidden="true">↗</span></button>
        {generationError && <p className="image-generation-error" role="alert">{generationError}</p>}
        <p className="generation-note"><span aria-hidden="true">✧</span> Tác phẩm của bạn bắt đầu từ một ý tưởng.</p>
      </form>
      <section className="preview-panel" aria-label="Xem trước hình ảnh">
        <div className="preview-topline"><span><span className="live-dot" /> KHUNG XEM TRƯỚC</span><button type="button" className="preview-menu" aria-label="Tùy chọn xem trước">•••</button></div>
        <div className={`artwork${generatedImages.length ? " has-generated-images" : ""}`} id="artwork-preview" data-ratio={ratio} aria-label="Khung xem trước ảnh">
          {generatedImages.length ? <div className="generated-image-grid" data-count={generatedImages.length}>
            {generatedImages.map((image, index) => {
              const imageUrl = image.asset_url;
              return <figure className="generated-image" key={image.asset_url}>
                <img src={imageUrl} alt={`${prompt.trim()} - ảnh ${index + 1}`} />
                <a className="image-download" href={imageUrl} download={`webai-image-${index + 1}.${image.mime_type.split("/")[1]}`}>↓ Tải ảnh</a>
              </figure>;
            })}
          </div> : generating ? <div className="image-loading" role="status"><span className="image-loading-spinner" /> Đang tạo hình ảnh...</div> : <div className="artwork-placeholder"><div className="artwork-sky" /><div className="artwork-sun" /><div className="artwork-stars" /><div className="artwork-mountain mountain-back" /><div className="artwork-mountain mountain-front" /><div className="artwork-water" /><div className="artwork-reflection" /><div className="artwork-caption"><span>GỢI Ý SÁNG TẠO</span><strong>{prompt.trim() ? prompt.slice(0, 42) : "Một chiều thật dịu dàng"}</strong></div><div className="artwork-grain" /></div>}
        </div>
        <div className="preview-caption-row"><div className="preview-caption-icon" aria-hidden="true">✦</div><div><strong>{generatedImages.length ? "Ảnh đã tạo" : "Không gian sáng tạo của bạn"}</strong><p>{generatedImages.length ? "Nhấn tải ảnh để lưu về thiết bị." : "Điều kỳ diệu sẽ xuất hiện ngay tại đây."}</p></div><span className="preview-ratio">{ratio}</span></div>
      </section>
    </div>
    <section className="inspiration-section" id="inspiration"><div className="inspiration-heading"><div><span className="inspiration-kicker">MỞ LỐI SÁNG TẠO</span><h2>Bắt đầu từ một cảm hứng</h2></div><span className="inspiration-subtitle">Chạm vào một ý tưởng để khám phá</span></div><InspirationCards items={imageIdeas} onSelect={setPrompt} /></section>
    <div className={`image-toast${toast ? " is-visible" : ""}`} role="status" aria-live="polite">{toast}</div>
  </section>;
}

export function VideoGenerator() {
  const [prompt, setPrompt] = useState("");
  const [style, setStyle] = useState("Điện ảnh");
  const [ratio, setRatio] = useState("16:9");
  const [duration, setDuration] = useState(5);
  const [elapsed, setElapsed] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [videoUrl, setVideoUrl] = useState("");
  const [generating, setGenerating] = useState(false);
  const [generationError, setGenerationError] = useState("");
  const [toast, setToast] = useToast();
  const { config, setCredits } = useAuth();
  const videoCost = (config.credit_prices?.video_per_second ?? 2) * duration;
  async function submit(event) {
    event.preventDefault();
    if (!prompt.trim() || generating) return;

    setGenerating(true);
    setGenerationError("");
    setVideoUrl("");
    setPlaying(false);
    setElapsed(0);
    try {
      const result = await api("/api/video/generate", {
        method: "POST",
        body: JSON.stringify({
          prompt: prompt.trim(),
          style,
          aspect_ratio: ratio,
          duration,
        }),
      });
      setVideoUrl(result.asset_url);
      setCredits(result.credits_balance);
      setPlaying(false);
      setElapsed(0);
      setToast(`Tạo video thành công (−${result.cost_credits} credit). Bạn có thể phát hoặc tải video về.`);
    } catch (error) {
      setGenerationError(error.message);
    } finally {
      setGenerating(false);
    }
  }
  useEffect(() => {
    if (!playing || videoUrl) return undefined;
    const timer = window.setInterval(() => setElapsed((time) => {
      if (time + 0.1 >= duration) {
        setPlaying(false);
        return 0;
      }
      return Math.round((time + 0.1) * 10) / 10;
    }), 100);
    return () => window.clearInterval(timer);
  }, [playing, duration, videoUrl]);
  const togglePlay = () => {
    if (elapsed >= duration) setElapsed(0);
    setPlaying((current) => !current);
  };
  const formatTime = (time) => `0:${String(Math.floor(time)).padStart(2, "0")}`;

  return <section className="video-page">
    <div className="video-heading"><div><div className="video-eyebrow"><span className="eyebrow-dot" /> AI VIDEO STUDIO</div><h1>Kể câu chuyện của bạn <span>bằng chuyển động.</span></h1><p>Mô tả khung cảnh bạn hình dung. AI sẽ giúp ý tưởng chuyển mình thành video.</p></div><a className="image-history" href="#video-inspiration"><span aria-hidden="true">✧</span> Khám phá ý tưởng</a></div>
    <div className="video-workspace">
      <form className="video-generator-panel" id="video-generator-form" onSubmit={submit}>
        <div className="panel-title"><div className="panel-icon video-panel-icon" aria-hidden="true">▶</div><div><h2>Tạo video mới</h2><p>Mô tả cảnh quay, chuyển động và cảm xúc bạn muốn.</p></div></div>
        <label className="field-label" htmlFor="video-prompt">Ý tưởng video</label>
        <div className="prompt-wrap video-prompt-wrap"><textarea id="video-prompt" name="prompt" maxLength={500} placeholder="Ví dụ: Máy quay lướt chậm qua con phố cổ sau cơn mưa, đèn lồng phản chiếu trên mặt đường, không khí yên bình..." required value={prompt} onChange={(event) => setPrompt(event.target.value)} /><span className="prompt-count">{prompt.length} / 500</span></div>
        <PromptChips items={[["↗ Máy quay chậm", "chuyển động máy quay chậm"], ["✦ Ánh sáng điện ảnh", "ánh sáng điện ảnh"], ["〰 Chuyển động mượt", "chuyển động mượt mà"]]} value={prompt} onChange={setPrompt} className="suggestion-row" chipClass="video-prompt-chip" />
        <div className="form-divider" /><div className="field-heading"><span className="field-label">Phong cách video</span><span className="field-hint">Chọn phong cách hình ảnh</span></div>
        <div className="video-style-options" role="group" aria-label="Chọn phong cách video">{[["Điện ảnh", "◒", "video-swatch-cinema"], ["Tả thực", "◉", "video-swatch-real"], ["Hoạt hình", "✿", "video-swatch-animation"], ["3D", "◇", "video-swatch-3d"]].map(([label, icon, swatch]) => <button key={label} type="button" className={`video-style-option${style === label ? " is-selected" : ""}`} aria-pressed={style === label} onClick={() => setStyle(label)}><span className={`video-style-swatch ${swatch}`} aria-hidden="true">{icon}</span><span>{label}</span></button>)}</div>
        <div className="form-divider" /><div className="video-settings-grid">
          <div><span className="field-label">Tỷ lệ khung hình</span><div className="ratio-options video-ratio-options" role="group" aria-label="Chọn tỷ lệ khung hình video">{[["16:9", "ratio-landscape"], ["9:16", "ratio-portrait"], ["1:1", "ratio-square"]].map(([label, icon]) => <button key={label} type="button" className={`video-ratio-option${ratio === label ? " is-selected" : ""}`} aria-pressed={ratio === label} onClick={() => setRatio(label)}><span className={icon} /> {label}</button>)}</div></div>
          <label className="quantity-field" htmlFor="video-duration"><span className="field-label">Thời lượng</span><select id="video-duration" value={duration} onChange={(event) => { setDuration(Number(event.target.value)); setElapsed(0); setPlaying(false); }}><option value={5}>5 giây</option><option value={10}>10 giây</option></select></label>
        </div>
        <button type="submit" className="generate-button video-generate-button" disabled={generating}><span aria-hidden="true">✦</span> {generating ? "Đang tạo video..." : <>Tạo video <span className="generation-cost">· {videoCost} credit</span></>} <span className="button-arrow" aria-hidden="true">↗</span></button>
        {generationError && <p className="video-generation-error" role="alert">{generationError}</p>}
        <p className="generation-note"><span aria-hidden="true">✧</span> Một câu chuyện mới sắp bắt đầu.</p>
      </form>
      <section className="video-preview-panel" aria-label="Xem trước video">
        <div className="video-preview-topline"><span><span className="live-dot" /> BẢN XEM TRƯỚC</span><span className="preview-quality">PREVIEW · {ratio}</span></div>
        <div className={`video-stage${playing ? " is-playing" : ""}`} id="video-stage" data-ratio={ratio} aria-label="Khung cảnh bờ biển lúc hoàng hôn">
          {videoUrl ? <><video className="generated-video" src={videoUrl} controls playsInline aria-label="Video do Pollinations tạo" /><a className="video-download" href={videoUrl} download="webai-video.mp4">↓ Tải video</a></> : generating ? <div className="video-generation-loading" role="status"><span className="video-generation-spinner" /> Đang tạo video, vui lòng đợi...</div> : <>
          <div className="video-scene-sky" /><div className="video-scene-sun" /><div className="video-scene-cloud cloud-one" /><div className="video-scene-cloud cloud-two" /><div className="video-scene-cliff" /><div className="video-scene-sea" /><div className="video-scene-wave wave-one" /><div className="video-scene-wave wave-two" /><div className="video-scene-light" /><div className="video-scene-grain" />
          <div className="video-scene-copy"><span>KHUNG CẢNH GỢI Ý</span><strong>{prompt.trim() ? prompt.slice(0, 42) : "Nơi ngày khép lại thật êm"}</strong></div>
          <div className="video-play-overlay"><button className="video-play-button" type="button" aria-label={playing ? "Tạm dừng xem trước" : "Phát xem trước"} aria-pressed={playing} onClick={togglePlay}>{playing ? "Ⅱ" : "▶"}</button></div>
          <div className="video-controls"><button className="video-control-play" type="button" aria-label={playing ? "Tạm dừng xem trước" : "Phát xem trước"} onClick={togglePlay}>{playing ? "Ⅱ" : "▶"}</button><span className="video-time">{formatTime(elapsed)} / {formatTime(duration)}</span><input className="video-timeline" type="range" min="0" max={duration} step="0.1" value={elapsed} aria-label="Tiến trình xem trước" onChange={(event) => setElapsed(Number(event.target.value))} /><span className="video-control-mark" aria-hidden="true">⌗</span><button className="video-control-fullscreen" type="button" aria-label="Phóng to xem trước" onClick={(event) => event.currentTarget.closest(".video-stage")?.requestFullscreen?.()}>⛶</button></div>
          </>}
        </div>
        <div className="video-preview-caption"><div className="preview-caption-icon video-caption-icon" aria-hidden="true">▶</div><div><strong>{videoUrl ? "Video đã tạo" : "Khung hình xem trước"}</strong><p>{videoUrl ? "Video đã sẵn sàng để phát và tải xuống." : "Nhấn phát để xem chuyển động minh họa."}</p></div><span className="preview-ratio">{ratio}</span></div>
      </section>
    </div>
    <section className="video-inspiration-section" id="video-inspiration"><div className="inspiration-heading"><div><span className="inspiration-kicker">MỖI CÂU CHUYỆN BẮT ĐẦU TỪ ĐÂY</span><h2>Gợi ý cho thước phim tiếp theo</h2></div><span className="inspiration-subtitle">Chọn một ý tưởng để đưa vào khung mô tả</span></div><InspirationCards items={videoIdeas} onSelect={setPrompt} video /></section>
    <div className={`image-toast${toast ? " is-visible" : ""}`} role="status" aria-live="polite">{toast}</div>
  </section>;
}

export function WebsiteBuilder() {
  const [prompt, setPrompt] = useState("");
  const [type, setType] = useState("coffee");
  const [palette, setPalette] = useState("sage");
  const [language, setLanguage] = useState("Tiếng Việt");
  const [device, setDevice] = useState("desktop");
  const [generatedContent, setGeneratedContent] = useState(null);
  const [generating, setGenerating] = useState(false);
  const [generationError, setGenerationError] = useState("");
  const [toast, setToast] = useToast();
  const { config, setCredits } = useAuth();
  const websiteCost = config.credit_prices?.website ?? 2;
  const preset = websitePresets[type];
  const english = language === "English";
  const content = english ? englishPresets[type] : null;
  const paletteVariables = ["bg", "text", "muted", "accent", "accent-text", "art-base", "art-back", "art-front"];
  const mockupStyle = Object.fromEntries(palettes[palette].map((color, index) => [`--mockup-${paletteVariables[index]}`, color]));
  const title = generatedContent?.title || (english ? content[1] : preset.title);
  const titleParts = generatedContent ? title.split(/\r?\n/) : title.split("<br>");
  const featureTitles = generatedContent?.features || (english ? content[5] : preset.features);
  const featureDescriptions = generatedContent?.feature_descriptions || (english
    ? ["Thoughtfully selected", "Made with care", "Every day"]
    : ["Tuyển chọn từ nông trại bền vững", "Giữ trọn hương vị tự nhiên", "Từng chi tiết đều được chăm chút"]);

  async function submit(event) {
    event.preventDefault();
    if (!prompt.trim() || generating) return;

    setGenerating(true);
    setGenerationError("");
    try {
      const result = await api("/api/website/generate", {
        method: "POST",
        body: JSON.stringify({
          prompt: prompt.trim(),
          website_type: type,
          palette,
          language,
        }),
      });
      setGeneratedContent(result.website);
      setCredits(result.credits_balance);
      setToast("AI đã tạo nội dung website. Bạn có thể tiếp tục chỉnh phong cách xem trước.");
    } catch (error) {
      setGenerationError(error.message);
    } finally {
      setGenerating(false);
    }
  }

  return <section className="website-page">
    <div className="website-heading"><div><div className="website-eyebrow"><span className="eyebrow-dot" /> AI WEBSITE STUDIO</div><h1>Ý tưởng của bạn. <span>Một website hoàn chỉnh.</span></h1><p>Mô tả website bạn cần, AI sẽ tạo nội dung và cập nhật bản xem trước.</p></div><a className="image-history" href="#website-inspiration"><span aria-hidden="true">✧</span> Khám phá ý tưởng</a></div>
    <div className="website-workspace">
      <form className="website-builder-panel" id="website-builder-form" onSubmit={submit}>
        <div className="panel-title"><div className="panel-icon website-panel-icon" aria-hidden="true">⌘</div><div><h2>Mô tả website của bạn</h2><p>Chia sẻ mục tiêu, nội dung và phong cách mong muốn.</p></div></div>
        <label className="field-label" htmlFor="website-prompt">Bạn muốn tạo website như thế nào?</label>
        <div className="prompt-wrap website-prompt-wrap"><textarea id="website-prompt" name="prompt" maxLength={600} placeholder="Ví dụ: Website cho tiệm cà phê rang xay thủ công, phong cách tối giản ấm áp, có menu, câu chuyện thương hiệu và nút đặt bàn..." required value={prompt} onChange={(event) => { setPrompt(event.target.value); setGeneratedContent(null); }} /><span className="prompt-count">{prompt.length} / 600</span></div>
        <PromptChips items={[["＋ Giới thiệu thương hiệu", "có trang giới thiệu thương hiệu"], ["＋ Nút hành động", "có nút kêu gọi hành động nổi bật"], ["＋ Tối ưu mobile", "tối ưu cho điện thoại"]]} value={prompt} onChange={(value) => { setPrompt(value); setGeneratedContent(null); }} className="website-quick-prompts" chipClass="website-prompt-chip" />
        <div className="form-divider" /><div className="field-heading"><span className="field-label">Loại website</span><span className="field-hint">Chọn mẫu để xem trước</span></div>
        <div className="website-type-options" role="group" aria-label="Chọn loại website">{[["coffee", "☕", "Cửa hàng"], ["portfolio", "✳", "Portfolio"], ["agency", "◈", "Doanh nghiệp"], ["restaurant", "♨", "Nhà hàng"]].map(([key, icon, label]) => <button key={key} type="button" className={`website-type-option${type === key ? " is-selected" : ""}`} aria-pressed={type === key} onClick={() => { setType(key); setGeneratedContent(null); }}><span className={`website-type-icon type-${key}`} aria-hidden="true">{icon}</span><span>{label}</span></button>)}</div>
        <div className="form-divider" /><div className="website-style-row">
          <div><span className="field-label">Bảng màu</span><div className="website-palette-options" role="group" aria-label="Chọn bảng màu">{[["sage", "Bảng màu xanh lá"], ["blue", "Bảng màu xanh dương"], ["rose", "Bảng màu hồng"], ["amber", "Bảng màu vàng"]].map(([key, label]) => <button key={key} type="button" className={`palette-option${palette === key ? " is-selected" : ""}`} aria-label={label} aria-pressed={palette === key} onClick={() => setPalette(key)}><span className={`palette-swatch palette-${key}`} /></button>)}</div></div>
          <label className="website-language" htmlFor="website-language"><span className="field-label">Ngôn ngữ</span><select id="website-language" value={language} onChange={(event) => { setLanguage(event.target.value); setGeneratedContent(null); }}><option>Tiếng Việt</option><option>English</option></select></label>
        </div>
        <button type="submit" className="generate-button website-generate-button" disabled={generating}><span aria-hidden="true">✦</span> {generating ? "Đang tạo website..." : <>Tạo website <span className="generation-cost">· {websiteCost} credit</span></>} <span className="button-arrow" aria-hidden="true">↗</span></button>
        {generationError && <p className="website-generation-error" role="alert">{generationError}</p>}
        <p className="generation-note"><span aria-hidden="true">✧</span> Một không gian mới đang chờ bạn tạo nên.</p>
      </form>
      <section className="website-preview-panel" aria-label="Xem trước website">
        <div className="website-preview-toolbar"><div className="website-browser-dots" aria-hidden="true"><i /><i /><i /></div><div className="website-address"><span aria-hidden="true">⌑</span> ban-website-moi.vn</div><div className="website-device-options" role="group" aria-label="Chọn thiết bị xem trước">{[["desktop", "▰", "Xem trên máy tính"], ["mobile", "▯", "Xem trên điện thoại"]].map(([key, icon, label]) => <button key={key} type="button" className={`device-option${device === key ? " is-selected" : ""}`} aria-label={label} aria-pressed={device === key} onClick={() => setDevice(key)}>{icon}</button>)}</div></div>
        <div className="website-preview-wrap"><div className="website-mockup" id="website-mockup" data-type={type} data-palette={palette} data-device={device} style={mockupStyle}>
          <div className="mockup-nav"><span className="mockup-brand"><i>{generatedContent?.icon || preset.icon}</i><strong>{generatedContent?.brand || preset.brand}</strong></span><div className="mockup-links">{(generatedContent?.nav_links || (english ? ["Home", "About", "Services"] : ["Trang chủ", "Về chúng tôi", "Dịch vụ"])).map((link) => <span key={link}>{link}</span>)}</div><button type="button" className="mockup-nav-cta">{generatedContent?.nav_cta || (content ? content[3] : preset.navCta)}</button></div>
          <div className="mockup-hero"><div className="mockup-hero-copy"><span className="mockup-kicker">{generatedContent?.kicker || (content ? content[0] : preset.kicker)}</span><h2>{titleParts.map((part, index) => <span key={`${index}-${part}`}>{index > 0 && <br />}{part}</span>)}</h2><p>{generatedContent?.description || (content ? content[2] : preset.description)}</p><button type="button" className="mockup-hero-cta">{generatedContent?.hero_cta || (content ? content[4] : preset.heroCta)} <span aria-hidden="true">↗</span></button></div><div className="mockup-hero-art" aria-hidden="true"><div className="mockup-art-sun" /><div className="mockup-art-shape shape-back" /><div className="mockup-art-shape shape-front" /><div className="mockup-art-object"><i /><b /></div><span className="mockup-art-stamp">MADE<br />WITH<br />CARE</span></div></div>
          <div className="mockup-bottom">{featureTitles.map((feature, index) => <div key={`${index}-${feature}`}><span className="mockup-bottom-icon">{["✳", "⌁", "♡"][index]}</span><span><strong>{feature}</strong><small>{featureDescriptions[index]}</small></span></div>)}</div>
        </div></div>
        <div className="website-preview-footer"><div className="website-preview-status"><span className="website-status-dot" /><span>{generating ? "AI đang tạo nội dung website" : generatedContent ? "Nội dung được tạo bởi Pollinations AI" : prompt ? "Bản xem trước mẫu" : "Bản xem trước trực tiếp"}</span></div><span className="website-preview-device-label">{device === "desktop" ? "Desktop · 1440 px" : "Mobile · 390 px"}</span></div>
      </section>
    </div>
    <section className="website-inspiration-section" id="website-inspiration"><div className="inspiration-heading"><div><span className="inspiration-kicker">BẮT ĐẦU NHANH HƠN</span><h2>Ý tưởng cho website tiếp theo</h2></div><span className="inspiration-subtitle">Chọn một mẫu để cập nhật bản xem trước</span></div>
      <div className="website-inspiration-grid">{[["coffee", "sage", "Thương hiệu thủ công", "Cửa hàng · Ấm áp, tự nhiên"], ["portfolio", "blue", "Portfolio sáng tạo", "Cá nhân · Tối giản, hiện đại"], ["agency", "rose", "Studio kỹ thuật số", "Doanh nghiệp · Tinh tế"], ["restaurant", "amber", "Nhà hàng địa phương", "Ẩm thực · Gần gũi"]].map(([key, color, label, detail]) => <button key={key} type="button" className="website-inspiration-card" data-type={key} data-palette={color} onClick={() => { setType(key); setPalette(color); setGeneratedContent(null); }}><span className={`website-template-art template-${key}`}><i /><b /><em /></span><span className="website-template-meta"><strong>{label}</strong><span>{detail}</span></span><span className="inspiration-arrow" aria-hidden="true">↗</span></button>)}</div>
    </section>
    <div className={`image-toast${toast ? " is-visible" : ""}`} role="status" aria-live="polite">{toast}</div>
  </section>;
}
