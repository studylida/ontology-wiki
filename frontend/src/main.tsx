import React, { Component, type ReactNode } from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./styles/app.css";
import "./styles/transitions.css";

class ErrorBoundary extends Component<
  { children: ReactNode },
  { failed: boolean }
> {
  state = { failed: false };
  static getDerivedStateFromError() {
    return { failed: true };
  }
  render() {
    if (this.state.failed)
      return (
        <main className="fatal-error">
          <h1>화면을 불러오는 중 문제가 생겼습니다</h1>
          <p>저장된 대화는 유지됩니다. 새로고침해 다시 연결해 주세요.</p>
          <button
            className="primary-button"
            onClick={() => window.location.reload()}
          >
            다시 열기
          </button>
        </main>
      );
    return this.props.children;
  }
}
ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </React.StrictMode>,
);
