import { useState, type FormEvent } from "react";
import {
  ArrowRight,
  BookOpen,
  Cpu,
  FileCheck2,
  Network,
  ShieldCheck,
} from "lucide-react";
import { ErrorNotice } from "./components/Primitives";

export function LoginView({
  busy,
  error,
  onLogin,
}: {
  busy: boolean;
  error: string | null;
  onLogin: (username: string, password: string) => Promise<void>;
}) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const submit = (event: FormEvent) => {
    event.preventDefault();
    void onLogin(username, password);
  };
  return (
    <main className="login-shell">
      <section className="login-story">
        <div className="brand">
          <span className="brand-mark">
            <Cpu size={23} />
          </span>
          <div>
            <strong>반도체 지식 허브</strong>
            <span>SEMICONDUCTOR KNOWLEDGE</span>
          </div>
        </div>
        <div className="login-story-content">
          <span className="eyebrow">FROM SOURCES TO UNDERSTANDING</span>
          <h1>
            흩어진 자료를
            <br />
            <em>연결된 이해로.</em>
          </h1>
          <p>
            원문을 찾고, 관점을 비교하고,
            <br />
            필요한 지식을 하나의 대화에서 이어가세요.
          </p>
          <div className="login-feature">
            <BookOpen size={19} />
            <div>
              <strong>질문에 맞는 두 가지 답변</strong>
              <span>개념을 정리하는 위키 · 조건을 살피는 분석</span>
            </div>
          </div>
          <div className="login-feature">
            <Network size={19} />
            <div>
              <strong>맥락이 이어지는 근거 탐색</strong>
              <span>관계와 원문을 답변 옆에서 확인</span>
            </div>
          </div>
          <div className="login-feature">
            <FileCheck2 size={19} />
            <div>
              <strong>개인의 기록, 공용의 문헌</strong>
              <span>개인 위키와 문헌 검토를 나눈 지식 관리</span>
            </div>
          </div>
        </div>
        <p className="login-footnote">
          자료의 근거와 적용 조건을 함께 살펴보는 작업 공간
        </p>
      </section>
      <section className="login-form-wrap">
        <form className="login-form" onSubmit={submit}>
          <div className="login-icon">
            <ShieldCheck size={25} />
          </div>
          <p className="eyebrow">YOUR KNOWLEDGE WORKSPACE</p>
          <h2>다시 만나 반갑습니다</h2>
          <p className="muted">계정으로 로그인해 지식 탐색을 이어가세요.</p>
          <label className="field">
            사용자 이름
            <input
              autoComplete="username"
              autoFocus
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              placeholder="사용자 이름"
              required
            />
          </label>
          <label className="field">
            비밀번호
            <input
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="비밀번호"
              required
            />
          </label>
          <ErrorNotice>{error}</ErrorNotice>
          <button
            className="primary-button login-submit"
            type="submit"
            disabled={busy}
          >
            {busy ? "로그인하는 중" : "로그인"}
            <ArrowRight size={18} />
          </button>
          <p className="fine-print">
            등록된 계정이 없다면 서비스 관리자에게 문의해 주세요.
          </p>
        </form>
      </section>
    </main>
  );
}
