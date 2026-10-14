import React from "react";
import ReactDOM from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Link, Route, Routes } from "react-router-dom";
import "@fontsource/nunito-sans/latin-400.css";
import "@fontsource/nunito-sans/latin-600.css";
import "@fontsource/nunito-sans/latin-700.css";
import "@fontsource/nunito-sans/latin-800.css";
import "@fontsource/nunito-sans/latin-900.css";
import { AuthProvider } from "./auth";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { Layout, Protected } from "./components/Layout";
import { Explore, Home, MemberProfile } from "./pages/discovery";
import { AuthPage, ProfileEditor } from "./pages/account";
import { Dashboard } from "./pages/dashboard";
import { Credits } from "./pages/credits";
import { Notifications } from "./pages/notifications";
import { RequestDetails, RequestList } from "./pages/requests";
import { SessionDetails, SessionList } from "./pages/sessions";
import { Admin } from "./pages/admin";
import "./styles.css";

const client = new QueryClient({
  defaultOptions: { queries: { staleTime: 15000, refetchOnWindowFocus: true } },
});
ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <BrowserRouter>
        <QueryClientProvider client={client}>
          <AuthProvider>
            <Routes>
              <Route element={<Layout />}>
                <Route index element={<Home />} />
                <Route path="explore" element={<Explore />} />
                <Route path="members/:id" element={<MemberProfile />} />
                <Route path="login" element={<AuthPage />} />
                <Route path="register" element={<AuthPage register />} />
                <Route element={<Protected />}>
                  <Route path="profile" element={<ProfileEditor />} />
                  <Route path="dashboard" element={<Dashboard />} />
                  <Route path="requests" element={<RequestList />} />
                  <Route path="requests/:id" element={<RequestDetails />} />
                  <Route path="sessions" element={<SessionList />} />
                  <Route path="sessions/:id" element={<SessionDetails />} />
                  <Route path="credits" element={<Credits />} />
                  <Route path="notifications" element={<Notifications />} />
                </Route>
                <Route element={<Protected admin />}>
                  <Route path="admin" element={<Admin />} />
                </Route>
                <Route
                  path="*"
                  element={
                    <div className="container">
                      <h1>Page not found</h1>
                      <Link to="/">Return to SkillSwap</Link>
                    </div>
                  }
                />
              </Route>
            </Routes>
          </AuthProvider>
        </QueryClientProvider>
      </BrowserRouter>
    </ErrorBoundary>
  </React.StrictMode>,
);
