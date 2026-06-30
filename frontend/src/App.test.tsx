import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import App from "./App";

vi.stubGlobal("fetch", vi.fn((url: string) => {
  if (url.startsWith("/api/config/sectors")) {
    return Promise.resolve({ ok: true, json: () => Promise.resolve({ sectors: [{ id: "ai-agents", name: "AI agents" }] }) });
  }
  if (url.startsWith("/api/topics")) {
    return Promise.resolve({ ok: true, json: () => Promise.resolve({ snapshot_at: null, topics: [], sectors: [] }) });
  }
  return Promise.resolve({
    ok: true,
    json: () => Promise.resolve({ snapshot_at: null, repos: [], sectors: [], totals: { repositories: 0, stars_delta: 0, forks_delta: 0 } })
  });
}));

describe("App", () => {
  it("renders empty dashboard state", async () => {
    render(<App />);
    expect(await screen.findByText("No trend snapshot yet")).toBeInTheDocument();
  });
});
