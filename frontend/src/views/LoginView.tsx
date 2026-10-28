import { useState } from 'react';
export function LoginView({busy, error, login}: {busy: boolean; error: string; login: (username: string, password: string) => Promise<void>}) {
  const [username, setUsername] = useState(''), [password, setPassword] = useState('');
  return <main className="login"><form onSubmit={e => {e.preventDefault(); void login(username, password).finally(() => setPassword(''));}}>
    <p className="eyebrow">COMPANY KNOWLEDGE</p><h1>사내 지식 어시스턴트</h1><p>함께 쓰는 문헌, 나만의 대화.</p>
    <label>아이디<input autoComplete="username" required value={username} onChange={e => setUsername(e.target.value)} /></label>
    <label>비밀번호<input type="password" autoComplete="current-password" required value={password} onChange={e => setPassword(e.target.value)} /></label>
    {error && <p role="alert" className="error">{error}</p>}<button className="primary" disabled={busy}>{busy ? '로그인 확인 중' : '로그인'}</button>
    <p className="muted">계정은 운영자가 발급합니다. 대화와 질문 이력은 다른 직원에게 공개되지 않습니다.</p>
  </form></main>;
}
