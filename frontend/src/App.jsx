import { Routes, Route, Navigate } from "react-router-dom";
import Login from "./components/Login";
import Signup from "./components/Signup";

function Home() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-white dark:bg-[#16171d]">
      <div className="text-center">
        <h1 className="text-4xl font-semibold text-[#08060d] dark:text-[#f3f4f6] tracking-tight mb-3">
          Welcome
        </h1>
        <p className="text-[#6b6375] dark:text-[#9ca3af] text-sm">
          You are signed in.
        </p>
      </div>
    </div>
  );
}

function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;
