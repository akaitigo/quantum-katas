import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Link, Route, Routes } from "react-router-dom";
import { KataDetail } from "@/components/KataDetail";
import { KataList } from "@/components/KataList";
import { ProgressBar } from "@/components/ProgressBar";
import { useProgress } from "@/hooks/useProgress";
import "./index.css";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function AppLayout(): React.JSX.Element {
  const { completedCount } = useProgress();

  return (
    <div className="app-container">
      <header className="app-header">
        <Link to="/" style={{ textDecoration: "none" }}>
          <h1>
            <span>Q</span>uantum Katas
          </h1>
        </Link>
        <ProgressBar completedCount={completedCount} />
      </header>
      <main>
        <Routes>
          <Route path="/" element={<KataList />} />
          <Route path="/kata/:kataId" element={<KataDetail />} />
        </Routes>
      </main>
    </div>
  );
}

export function App(): React.JSX.Element {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AppLayout />
      </BrowserRouter>
    </QueryClientProvider>
  );
}
