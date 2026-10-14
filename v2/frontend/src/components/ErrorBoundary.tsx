import { Component, type ReactNode } from "react";

export class ErrorBoundary extends Component<
  { children: ReactNode },
  { failed: boolean }
> {
  state = { failed: false };
  static getDerivedStateFromError() {
    return { failed: true };
  }
  render() {
    return this.state.failed ? (
      <main className="container app-page">
        <h1>This screen couldn’t be opened</h1>
        <p>Your saved activity is safe. Reload SkillSwap to try again.</p>
        <button className="button" onClick={() => window.location.reload()}>
          Reload SkillSwap
        </button>
      </main>
    ) : (
      this.props.children
    );
  }
}
