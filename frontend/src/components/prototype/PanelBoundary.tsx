import { Component, type ReactNode } from "react";

/** A visualization failure must not erase the workbench or its event record. */
export class PanelBoundary extends Component<{ children: ReactNode; name: string }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  render() {
    return this.state.failed ? <section role="alert" className="flex min-h-0 items-center justify-center border border-amber-200 bg-white p-5 text-xs leading-6 text-amber-800"><div><p>{this.props.name}暂不可用。事件记录未删除，不会伪造后续执行。</p><button className="mt-2 border border-amber-300 px-3 py-1" onClick={() => this.setState({ failed: false })}>重试显示</button></div></section> : this.props.children;
  }
}
